import os
import re
import argparse

from datetime import datetime

from typing import Callable, Iterable


#! DEPRECATED, maybe useful... for future functionality
def get_tags_from_name(path: str) -> set[str]:
    """
    Reads all Markdown files (.md) in a directory
    and extracts tags from the filenames.
    Filenames are split by '_' and returned as lowercase tags.
    """
    tags = set()
    for name in os.listdir(path):
        item_path = os.path.join(path, name)
        if (
            os.path.isfile(item_path)
            and os.path.splitext(item_path)[1].lower() == ".md"
            and not item_path.endswith("linklist.md")
        ):
            text = os.path.splitext(name)[0].lower()
            words = text.split("_")
            for word in words:
                tags.add(word)
    return tags


def get_tags_from_headers(text: str) -> set[str]:
    """
    reads markdown formatted string and extracts tags from headers (#, ##, ###, …).
    The header text is converted to lowercase and returned as a set.
    """
    return {
        "".join(tag.split("# ")[1:]) for tag in re.findall(r"(?<!\S| )#{1,6} .+", text)
    }


# ! not quite the intended Behavior, unused for now
def get_tags_from_bold(text: str) -> set[str]:
    """
    reads markdown formatted string and extracts tags from bold expressions (**expression**).
    The text is converted to lowercase and returned as a set.
    """
    return {tag for tag in re.findall(r"(?<=\*\*)[^\*\[\]]*(?=\*\*)", text)}


def get_tags_from_wikiquote(text: str) -> set[str]:
    """
    reads markdown formatted string and extracts tags from headers (#, ##, ###, …).
    The header text is converted to lowercase and returned as a set.
    """
    return {tag for tag in re.findall(r"(?<=\[\[)[^\[\]]*(?=\]\])", text)}


def get_tags_from_comment(text: str) -> set[str]:
    """
    Reads a Markdown formated Text and looks for a special comment:
    [tags]:# (tag1,tag2,...)
    Extracts the tags, removes extra spaces, and returns them as a set.
    """
    tags = set()
    try:
        m = re.search(r"(?<!\S| )\[tags\]:# \((.*)\)", text)
        assert m is not None
        string = m.group(1).replace(", ", ",")
        tags = set(string.split(","))
        tags.discard("")
    finally:
        return tags


def add_tags(tags: set[str], text: str) -> str:
    """
    Adds the given tags to a Markdown formated text.
    If a [tags]:# entry already exists, it is updated.
    Otherwise, a new one is inserted at the top.
    """
    tags = tags.union(get_tags_from_comment(text))
    taglist = sorted(tags)
    tagstring = ""
    for tag in taglist:
        tagstring += f"{tag}, "
    rt = re.compile(r"(?<!\S| )\[tags\]:# \((.*)\)")  # match [tags]:# (...)
    if re.match(r"(?<!\S| )\[tags\]:# \((.*)\)\n\n", text):
        text = re.sub(rt, f"[tags]:# ({tagstring})", text)
    elif re.search(r"(?<!\S| )\[tags\]:# \((.*)\)", text):
        text = re.sub(rt, "", text)
        text = text.lstrip()
        text = f"[tags]:# ({tagstring})\n\n" + text
    else:
        text = f"[tags]:# ({tagstring})\n\n" + text
    return text


def add_links_from_list(text: str, linklist: str) -> str:
    """
    Goes through the text of a Markdown formated text and replaces occurrences of tags
    with Markdown reference links in the form [tag][tag].
    Then appends link definitions at the end of the file in this format:
    [tag]: relative/path/file.md#tag
    """
    tre = re.compile(r"\[(.*)\]\((.*)\)")
    ld = {
        re.match(tre, strg).group(1): re.match(tre, strg).group(2)
        for strg in linklist.rstrip().split("\n\n")[1:]
    }
    appendix = "\n\n"
    m = re.match(r"(?<!\S| )\[tags\]:# \((.*)\)", text)
    assert m is not None
    tagstring = m.group(0)
    text = re.sub(r"(?<!\S| )\[tags\]:# \((.*)\)", "@@-0-@@", text)
    tags = sorted(get_tags_from_comment(linklist), key=len)[::-1]
    placeholders = {}
    for i, tag in enumerate(tags):
        etag = re.escape(tag)
        placeholder = rf"@@@{i}@@@"
        placeholders[placeholder] = f"[{tag}][{tag}]"
        text = re.sub(re.escape(placeholders[placeholder]), placeholder, text)
        text = re.sub(rf"(?i)\[{etag}\]: .*#.*\.md\n", "", text)
        text = re.sub(
            rf"(?i)(?<!#)(?<!# )(?<!\(|\[)\b{etag}(?![a-z,][ \)][\)\n]|\.md)|(?<=\[\[){etag}(?=\]\])",
            placeholder,
            text,
        )
        text.rstrip()
        text = re.sub(rf"(?i)\[{etag}\]\[{etag}\]", placeholder, text)
    for placeholder in placeholders.keys():
        text = re.sub(rf"\[\[{placeholder}\]\]", placeholder, text)
        text = re.sub(placeholder, placeholders[placeholder], text)

    for tag in tags:
        etag = re.escape(tag)
        if re.search(rf"(?i)\[{etag}\]\[{etag}\]", text):
            if (
                re.search(
                    rf"(?i)(?<!\S| )\[{etag}\]: {re.escape(ld[tag])}",
                    text,
                )
                is None
            ):
                appendix += f"[{tag}]: {ld[tag]}\n"
    text = re.sub(r"@@-0-@@", tagstring, text)
    if appendix == "\n\n":
        return text
    else:
        return text + appendix


# TODO reduce use of expensive operation
def get_origin(tag: str, path: str) -> str:
    """
    Searches for a Markdown file in the directory that contains the tag
    inside its [tags]:# entry.
    Returns the path to the file where the tag is defined.
    """
    rt = re.compile(r"(?i)(?<!\S| )\[tags\]:# \((.*)\)")
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not file_path.endswith("linklist.md")
        ):
            with open(os.path.realpath(file_path), encoding="utf-8") as f:
                m = re.search(rt, f.read())
                assert m is not None
                tagstring = m.group(1)
                if tag in tagstring.lower().split(", "):
                    return file_path
    else:
        raise ValueError(f"no tag: {tag} was found in {path}")


def initialize_tagging(path: str) -> None:
    """
    Initializes tagging:
    - goes through all Markdown files in the directory
    - extracts tags from headers
    - inserts them into [tags]:# comments
    - then creates cross-links between all files based on tags
    """
    drc = os.listdir(path)
    if len(drc) == 0:
        return
    atags = set()
    atag_paths: dict = {}
    linklist = ""
    for name in drc:
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not file_path.endswith("linklist.md")
        ):
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
            tags = get_tags_from_headers(text)
            tags.update(get_tags_from_comment(text))
            tags.update(get_tags_from_wikiquote(text))
            text = add_tags(tags, text)
            tag_paths = get_tag_headers(tags, text, os.path.relpath(file_path, path))
            atags.update(tags)
            atag_paths |= tag_paths
            with open(file_path, mode="w", encoding="utf-8") as f:
                f.write(text)
    linklist = add_tags(atags, linklist)
    linklist = add_taglinks_to_linklist(atags, atag_paths, linklist)
    for name in drc:
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not file_path.endswith("linklist.md")
        ):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            out = add_links_from_list(text, linklist)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(out)
    with open(os.path.join(path, "linklist.md"), "w", encoding="utf-8") as fl:
        fl.write(linklist)


def add_taglinks_to_linklist(tags: set[str], tag_paths: dict, text: str) -> str:
    for tag in sorted(tags):
        if not re.search(rf"\[{tag}\]", text):
            text += f"[{tag}]({tag_paths[tag]}); \n\n"
    return text


def get_tag_headers(tags: set, text, rel_path):
    tags = tags.copy()
    hre = re.compile(r"^#{1,6} .*(?=\n)|(?<=\n)#{1,6} .*(?=\n|$)")
    headers = re.findall(hre, text)
    if (m := re.match(r"^\[tags\]:# .*\n\n", text)) is not None:
        assert m is not None
        text = text[len(m.group(0)) :]
    tag_paths = {
        header.split("# ")[1]: rel_path + "#" + header.split("# ")[1].replace(" ", "-")
        for header in headers
    }
    headers = [""] + headers
    splt = re.split(hre, text)
    tags.difference_update(tag_paths.keys())
    for tag in tags:
        for i, strng in enumerate(splt):
            if tag in tag_paths.keys():
                continue
            if tag in strng:
                if headers[i] == "":
                    tag_paths[tag] = rel_path
                else:
                    tag_paths[tag] = (
                        rel_path + "#" + headers[i].split("# ")[1].replace(" ", "-")
                    )
    for tag in tags:
        if tag not in tag_paths.keys():
            tag_paths[tag] = rel_path
    return tag_paths


def check_list_for_tags(tags: Iterable, path: str) -> set:
    """
    Checks if the linklist of a directory has the provided tags,
    if no list exists it returns an empty set.
    """
    found_tags: set = set()
    try:
        with open(os.path.join(path, "linklist.md"), "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError as e:
        return found_tags
    for tag in tags:
        if f"[{tag.lower()}]" in text:
            found_tags.add(tag)
    return found_tags


def find_links_to_tag(tag: str, path: str) -> list[str | None]:
    links: list[str | None] = []
    hre = re.compile(r"^#{1,6} .*(?=\n)|(?<=\n)#{1,6} .*(?=\n)")
    tre = re.compile(rf"(?i)\[{tag}\]\[{tag}\]")
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not os.path.splitext(file_path)[0].endswith("linklist")
        ):
            with open(file_path, encoding="utf-8") as f:
                text = f.read()

            headers = [""] + re.findall(hre, text)
            split = re.split(hre, text)
            for i, strng in enumerate(split):
                for m in re.findall(tre, strng):
                    if m == "":
                        continue
                    if headers[i] == "":
                        links.append(os.path.relpath(file_path, path))
                    else:
                        links.append(
                            os.path.relpath(file_path, path)
                            + "#"
                            + headers[i].split("# ")[1].replace(" ", "-")
                        )

        links.sort()
    return links


# TODO
def update_tags_on_file(file_path: str) -> None:
    pass


def terminal_operation() -> None:
    parser = argparse.ArgumentParser(
        description="link markdown documents through headers automaticly",
        add_help=False,
    )
    parser.add_argument(
        "-n",
        action="store_true",
        dest="new",
        help="set if you want to generate links from the ground up over all documents",
    )
    parser.add_argument(
        "-p",
        type=str,
        dest="path",
        default=os.path.realpath("./"),
        help="provide the directory path",
    )

    args = parser.parse_args()
    if args.new:
        initialize_tagging(os.path.realpath(args.path))


if __name__ == "__main__":
    terminal_operation()

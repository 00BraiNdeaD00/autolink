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
        ):
            text = os.path.splitext(name)[0].lower()
            words = text.split("_")
            for word in words:
                tags.add(word)
    return tags


def get_tags_from_headers(file_path: str) -> set[str]:
    """
    Reads a Markdown file and extracts tags from headers (#, ##, ###, …).
    The header text is converted to lowercase and returned as a set.
    """
    with open(file_path, encoding="utf-8") as file:
        tags = {
            "".join(tag.split("# ")[1:]).lower()
            for tag in re.findall(r"(?<!\S| )#{1,6} .+", file.read())
        }
    return tags


# ! not quite the intended Behavior, unused for now
def get_tags_from_bold(file_path: str) -> set[str]:
    """
    Reads a Markdown file and extracts tags from headers (#, ##, ###, …).
    The header text is converted to lowercase and returned as a set.
    """
    with open(file_path, encoding="utf-8") as file:
        tags = {
            tag.lower()
            for tag in re.findall(r"(?<=\*\*)[^\*\[\]]*(?=\*\*)", file.read())
        }
    return tags


def get_tags_from_wikiquote(file_path: str) -> set[str]:
    """
    Reads a Markdown file and extracts tags from headers (#, ##, ###, …).
    The header text is converted to lowercase and returned as a set.
    """
    with open(file_path, encoding="utf-8") as file:
        tags = {
            tag.lower() for tag in re.findall(r"(?<=\[\[)[^\[\]]*(?=\]\])", file.read())
        }
    return tags


def get_tags_from_comment(file_path: str) -> set[str]:
    """
    Reads a Markdown file and looks for a special comment:
    [tags]:# (tag1,tag2,...)
    Extracts the tags, removes extra spaces, and returns them as a set.
    """
    with open(file_path, encoding="utf-8") as file:
        tags = set()
        try:
            m = re.search(r"(?<!\S| )\[tags\]:# \((.*)\)", file.read())
            assert m is not None
            string = m.group(1).replace(", ", ",")
            tags = set(string.split(","))
            tags.discard("")
        finally:
            return tags


#! DEPRECATED or maybe later feature...
def check_direct_links(tags: set[str], file_path: str) -> bool:
    """
    Checks if all tags either appear in the filename or in the file content,
    and whether they already exist as Markdown links to other files.
    Returns True if links already exist, otherwise False.
    """
    with open(file_path, encoding="utf-8") as file:
        text = file.read()
        for tag in tags:
            if a := re.search(rf"(?i){tag}", os.path.basename(file_path)):
                continue
            if ist := re.search(rf"(?i){tag}", text):
                if b := re.search(rf"(?i)\[{tag}\]\(.*\.md\)", text):
                    continue
                else:
                    return False
        return True


def check_tags(tags: set[str], file_path) -> bool:
    otags = get_tags_from_comment(file_path)
    return otags == tags


def combine_tags(tags: set[str], file_path) -> set[str]:
    """
    Compares the tags stored in the [tags]:# comment
    with the provided tags, then combine them.
    """
    otags = set()
    with open(file_path, encoding="utf-8") as file:
        if m := re.search(r"(?<!\S| )\[tags\]:# \((.*)\)", file.read()):
            string = m.group(1).replace(", ", ",")
            otags = set(string.split(","))
            otags.discard("")

    return tags.union(otags)


def add_tags(tags: set[str], file_path: str) -> None:
    """
    Adds the given tags to a Markdown file.
    If a [tags]:# entry already exists, it is updated.
    Otherwise, a new one is inserted at the top.
    """
    tags = combine_tags(tags, file_path)
    taglist = list(tags)
    tagstring = ""
    for tag in taglist:
        tagstring += f"{tag}, "
    rt = re.compile(r"(?<!\S| )\[tags\]:# \((.*)\)")
    with open(file_path, encoding="utf-8") as file:
        text = file.read()
        if m := re.match(rt, text):
            text = re.sub(rt, f"[tags]:# ({tagstring})", text)
        elif m := re.search(rt, text):
            text = re.sub(rt, "", text)
            text = f"[tags]:# ({tagstring})\n" + text
        else:
            text = f"[tags]:# ({tagstring})\n" + text
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)


def add_links(tags: set[str] | list[str], file_path: str, path: str) -> None:
    """
    Goes through the text of a Markdown file and replaces occurrences of tags
    with Markdown reference links in the form [tag][tag].
    Then appends link definitions at the end of the file in this format:
    [tag]: relative/path/file.md#tag
    """
    appendix = "\n\n"
    with open(file_path, encoding="utf-8") as file:
        text = file.read()
    m = re.match(r"(?<!\S| )\[tags\]:# \((.*)\)", text)
    assert m is not None
    tagstring = m.group(0)
    text = re.sub(r"(?<!\S| )\[tags\]:# \((.*)\)", "@@-0-@@", text)
    tags = sorted(tags, key=len)[::-1]
    placeholders = {}
    for i, tag in enumerate(tags):
        etag = re.escape(tag)
        placeholder = rf"@@@{i}@@@"
        placeholders[placeholder] = f"[{tag}][{tag}]"
        text = re.sub(re.escape(placeholders[placeholder]), placeholder, text)
        text = re.sub(rf"(?i)\[{etag}\]: .*#.*\.md\n", "", text)
        text = re.sub(
            rf"(?i)(?<!#)(?<!# )(?<!\(|\[)\b{etag}(?![a-z,][ \)][\)\n]|\.md)",
            placeholder,
            text,
        )
        text.rstrip()
        text = re.sub(rf"(?i)\[{etag}\]\[{etag}\]", placeholder, text)
    for placeholder in placeholders.keys():
        text = re.sub(placeholder, placeholders[placeholder], text)

    for tag in tags:
        tag_origin = get_origin(tag, path)
        etag = re.escape(tag)
        if re.search(rf"(?i)\[{etag}\]\[{etag}\]", text):
            if (
                re.search(
                    rf"(?i)(?<!\S| )\[{etag}\]: {re.escape(os.path.relpath(str(tag_origin), path))}#{re.escape(tag.replace(" ","-"))}",
                    text,
                )
                is None
            ):
                appendix += f"[{tag}]: {os.path.relpath(str(tag_origin), path)}#{tag.replace(" ","-")}\n"
    text = re.sub(r"@@-0-@@", tagstring, text)
    with open(file_path, "w", encoding="utf-8") as file:
        if appendix == "\n\n":
            file.write(text)
        else:
            file.write(text + appendix)


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
    atags = set()
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not file_path.endswith("linklist.md")
        ):
            tags = get_tags_from_headers(file_path)
            tags.update(get_tags_from_bold(file_path))
            tags.update(get_tags_from_comment(file_path))
            # td = {tag: file_path for tag in tags}
            # tag_dict += td
            add_tags(tags, file_path)
            atags.update(tags)
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not file_path.endswith("linklist.md")
        ):
            add_links(atags, file_path, path)


def create_linklist(path: str) -> str:
    """
    Creates a list of generated tags, and their links.
    Returns the path to the list.
    """
    tags: set = set()
    list_path = os.path.join(path, "linklist.md")
    try:
        with open(list_path, "x", encoding="utf-8") as f:
            pass
        text = ""
    except FileExistsError as e:
        with open(list_path) as f:
            text = ""
        # TODO tags.update(get_tags_from_list(list_path))
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
            and not file_path.endswith("linklist.md")
        ):
            tags.update(get_tags_from_comment(file_path))
            tags.update(get_tags_from_bold(file_path))
            tags.update(get_tags_from_headers(file_path))
    for tag in sorted(tags):
        tag_path = get_origin(tag, path)
        text += f"[{tag}]({os.path.relpath(tag_path, path)}#{tag.replace(" ", "-")}); "
        now = datetime.now()
        for link in find_links_to_tag(tag, path):
            text += f"[{link}: {now.strftime('%d/%m/%Y, %H:%M:%S')}]({link}); "
        text += "\n\n"

    with open(list_path, "w", encoding="utf-8") as f:
        f.write(text)
    add_tags(tags, list_path)

    return list_path


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


def update_tags_on_file(file_path: str) -> None:
    pass


def clean_wikilinks(file_path):
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
        create_linklist(os.path.realpath(args.path))


if __name__ == "__main__":
    terminal_operation()
    # print(get_tags_from_bold(os.path.realpath("./README.md")))

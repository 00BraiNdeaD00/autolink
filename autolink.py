import os
import re

from typing import Callable


#! DEPRECATED, maybe useful... for future functionality
def get_tags_from_name(path) -> set[str]:
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


def get_tags_from_headers(file_path) -> set[str]:
    """
    Reads a Markdown file and extracts tags from headers (#, ##, ###, …).
    The header text is converted to lowercase and returned as a set.
    """
    with open(file_path) as file:
        tags = {
            "".join(tag.split("# ")[1:]).lower()
            for tag in re.findall(r"(?<!\S| )#{1,6} .+", file.read())
        }
    return tags


def get_tags_from_comment(file_path):
    """
    Reads a Markdown file and looks for a special comment:
    [tags]:# (tag1,tag2,...)
    Extracts the tags, removes extra spaces, and returns them as a set.
    """
    with open(file_path) as file:
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
def check_direct_links(tags, file_path):
    """
    Checks if all tags either appear in the filename or in the file content,
    and whether they already exist as Markdown links to other files.
    Returns True if links already exist, otherwise False.
    """
    with open(file_path) as file:
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
    with open(file_path) as file:
        if m := re.search(r"(?<!\S| )\[tags\]:# \((.*)\)", file.read()):
            string = m.group(1).replace(", ", ",")
            otags = set(string.split(","))
            otags.discard("")

    return tags.union(otags)


def add_tags(tags, file_path) -> None:
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
    with open(file_path) as file:
        text = file.read()
        if m := re.match(rt, text):
            text = re.sub(rt, f"[tags]:# ({tagstring})", text)
        elif m := re.search(rt, text):
            text = re.sub(rt, "", text)
            text = f"[tags]:# ({tagstring})\n" + text
        else:
            text = f"[tags]:# ({tagstring})\n" + text
    with open(file_path, "w") as file:
        file.write(text)


def add_links(tags: set[str] | list[str], file_path):
    """
    Goes through the text of a Markdown file and replaces occurrences of tags
    with Markdown reference links in the form [tag][tag].
    Then appends link definitions at the end of the file in this format:
    [tag]: relative/path/file.md#tag
    """
    appendix = "\n\n"
    with open(file_path) as file:
        text = file.read()
    m = re.match(r"(?<!\S| )\[tags\]:# \((.*)\)", text)
    assert m is not None
    tagstring = m.group(0)
    print(tagstring)
    text = re.sub(r"(?<!\S| )\[tags\]:# \((.*)\)", "@@-0-@@", text)
    tags = sorted(tags, key=len)[::-1]
    placeholders = {}
    for i, tag in enumerate(tags):
        etag = re.escape(tag)
        placeholder = rf"@@@{i}@@@"
        placeholders[placeholder] = f"[{tag}][{tag}]"
        tag_origin = get_origin(tag, os.path.dirname(os.path.realpath(file_path)))
        text = re.sub(
            # rf"(?i)(?<!#)(?<!# )(?<!\(|\[)\b{tag[:-1]}\B{tag[-1]}(?![a-z,][ \)][\)\n]|\.md)",
            rf"(?i)(?<!#)(?<!# )(?<!\(|\[)\b{etag}(?![a-z,][ \)][\)\n]|\.md)",
            placeholder,
            text,
        )
        text = re.sub(rf"(?i)\[{etag}\]\[{etag}\]", placeholder, text)
    for placeholder in placeholders.keys():
        text = re.sub(placeholder, placeholders[placeholder], text)

    for tag in tags:
        etag = re.escape(tag)
        if re.search(rf"(?i)\[{etag}\]\[{etag}\]", text):
            if (
                re.search(
                    rf"(?i)(?<!\S| )\[{etag}\]: {re.escape(os.path.relpath(str(tag_origin)))}#{re.escape(tag.replace(" ","-"))}",
                    # rf"(?i)(?<!#)(?<!# )(?<!\(|\[)\b{re.escape(tag)}\b(?!\.md)",
                    text,
                )
                is None
            ):
                appendix += f"[{tag}]: {os.path.relpath(str(tag_origin))}#{tag.replace(" ","-")}\n"
    text = re.sub(r"@@-0-@@", tagstring, text)
    with open(file_path, "w") as file:
        if appendix == "\n\n":
            file.write(text)
        else:
            file.write(text + appendix)


def get_origin(tag, path):
    """
    Searches for a Markdown file in the directory that contains the tag
    inside its [tags]:# entry.
    Returns the path to the file where the tag is defined.
    """
    rt = re.compile(r"(?<!\S| )\[tags\]:# \((.*)\)")
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
        ):
            with open(file_path) as file:
                tagstring = re.search(rt, file.read()).group(1)
                if tag in tagstring.lower().split(", "):
                    return file_path
    else:
        raise ValueError(f"no tag: {tag} was found in {path}")


def initialize_tagging(path):
    """
    Initializes tagging:
    - goes through all Markdown files in the directory
    - extracts tags from headers
    - inserts them into [tags]:# comments
    - then creates cross-links between all files based on tags
    """
    atags = set()
    tag_dict = {}
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(file_path)[1].lower() == ".md"
        ):
            tags = get_tags_from_headers(file_path)
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
        ):
            add_links(atags, file_path)


if __name__ == "__main__":
    tags = initialize_tagging(os.path.realpath("./"))

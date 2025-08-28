import os
import sys
import re
import argparse
from autolink.tag_index import TagIndex  # Import the new TagIndex class

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


def get_tags_from_wikilinks(text: str) -> set[str]:
    """
    reads markdown formatted string and extracts tags text formatted like wikilinks: [[tag]].
    The text returned as a set.
    """
    return {tag for tag in re.findall(r"(?<=\[\[)[^\[\]]*(?=\]\])", text)}


def get_tags_from_comment(text: str) -> set[str]:
    """
    Reads a Markdown formated Text and looks for a special comment:
    [tags]:# (tag1,tag2,...)
    Extracts the tags, removes extra spaces, and returns them as a set.
    """
    tags = set()
    m = re.search(r"(?<!\S| )\[tags\]:# \((.*)\)", text)
    if m:
        string = m.group(1).replace(", ", ",")
        tags = set(string.split(","))
        tags.discard("")
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
    tre = re.compile(r"\[(.*?)\]\((.*?)\);")
    ld = {
        m.group(1): m.group(2)
        for strg in linklist.rstrip().split("\n\n")[1:]
        if (m := re.match(tre, strg))
    }
    appendix = "\n\n"
    m = re.match(r"(?<!\S| )\[tags\]:# \((.*)\)", text)
    if not m:
        return text  # Cannot proceed without a tags comment
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
                if m:
                    tagstring = m.group(1)
                    if tag in tagstring.split(", "):
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
    - builds and saves a tag index for faster lookups
    """
    drc = os.listdir(path)
    if len(drc) == 0:
        return
    atags = set()
    atag_paths: dict = {}
    linklist = ""
    tag_index = TagIndex(path)
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
            tags.update(get_tags_from_wikilinks(text))
            text = add_tags(tags, text)
            tag_paths = get_tag_headers(tags, text, os.path.relpath(file_path, path))
            atags.update(tags)
            atag_paths |= tag_paths
            with open(file_path, mode="w", encoding="utf-8") as f:
                f.write(text)
    linklist = add_tags(atags, linklist)
    linklist = add_taglinks_to_linklist(atag_paths, linklist)
    # Populate tag index with definitions
    for tag, path_info in atag_paths.items():
        # The file_path for definition is just the file, not with #header
        tag_index.add_definition(tag, path_info.split("#")[0], path_info)
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
            tag_index.update_file_references(
                os.path.relpath(file_path, path), tag_index.get_all_tags(), out
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(out)
    tag_index.save()
    with open(os.path.join(path, "linklist.md"), "w", encoding="utf-8") as fl:
        fl.write(linklist)
    tag_index.save()


def add_taglinks_to_linklist(tags_with_paths: dict[str, str], text: str) -> str:
    """
    Adds or updates tag definitions in the linklist content.
    `tags_with_paths` is a dictionary where keys are tags and values are their paths.
    """
    for tag, path in tags_with_paths.items():
        # Remove existing definition for this tag
        text = re.sub(
            rf"\[{re.escape(tag)}\]\(.*\); \n\n", "", text, flags=re.IGNORECASE
        )
        # Add new definition in the correct format
        text += f"[{tag}]({path}); \n\n"
    return text


def _remove_tag_references_from_file(tag: str, file_path: str) -> None:
    """
    Removes all references and definitions for a given tag from a file.
    - Replaces `[tag][tag]` with `tag`.
    - Removes `[tag]: path/to/file.md#header` definition.
    """
    with open(file_path, "r+", encoding="utf-8") as f:
        content = f.read()
        modified_content = content

        # Replace the reference-style link `[tag][tag]` with the plain tag text.
        modified_content = re.sub(
            rf"\[{re.escape(tag)}\]\[{re.escape(tag)}\]",
            tag,
            modified_content,
            flags=re.IGNORECASE,
        )
        # Remove the link definition from the appendix of the file.
        modified_content = re.sub(
            rf"^\s*\[{re.escape(tag)}\]: .*\n?",  # Match [tag]: ...\n
            "",
            modified_content,
            flags=re.MULTILINE | re.IGNORECASE,
        )

        if modified_content != content:
            f.seek(0)
            f.write(modified_content.rstrip() + "\n")
            f.truncate()


def get_tag_headers(tags: set, text, rel_path):
    tags = tags.copy()
    hre = re.compile(r"^#{1,6} .*(?=\n)|(?<=\n)#{1,6} .*(?=\n|$)")
    headers = re.findall(hre, text)
    if (m := re.match(r"^\[tags\]:# .*\n\n", text)) is not None:
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
        if f"[{tag}]" in text:
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


def _cleanup_dead_tag_in_project(
    tag: str, directory_path: str, tag_index: TagIndex
) -> None:
    """
    When a tag is completely removed from the project, this function cleans up
    any lingering references to it in all project files.
    """
    # Only clean up files that are known to reference this tag from the index
    for name in tag_index.get_referenced_files(tag):
        other_file_path = os.path.join(directory_path, name)
        if (
            os.path.isfile(other_file_path)
            and os.path.splitext(other_file_path)[1].lower() == ".md"
            and not other_file_path.endswith("linklist.md")
        ):
            _remove_tag_references_from_file(tag, other_file_path)


def update_tags_on_file(file_path: str) -> None:
    """
    Updates a single file and the central linklist.
    - Adds links to the file for any new tags found in the linklist.
    - Scans the file for new or removed tags.
    - Updates the linklist with these changes.
    """
    # Initialize TagIndex for the current directory
    dir_path = os.path.dirname(file_path)
    if not dir_path:
        dir_path = "."
    linklist_path = os.path.join(dir_path, "linklist.md")
    rel_path = os.path.relpath(file_path, dir_path)

    # Read original state of file and linklist
    tag_index = TagIndex(dir_path)
    old_tags = {
        tag
        for tag in tag_index.get_all_tags()
        if os.path.relpath(file_path, dir_path)
        in tag_index.get_defining_files(tag).keys()
    }
    with open(file_path, "r", encoding="utf-8") as f:
        original_file_content = f.read()

    try:
        with open(linklist_path, "r", encoding="utf-8") as f:
            linklist_content = f.read()
    except FileNotFoundError:
        # If no linklist, start with empty.
        linklist_content = ""

    # Update the file's tags
    current_tags = get_tags_from_headers(original_file_content)
    current_tags.update(get_tags_from_wikilinks(original_file_content))
    current_tags.update(get_tags_from_comment(original_file_content))
    file_content_with_updated_tags = add_tags(current_tags, original_file_content)
    # Add links from the master linklist to the file.
    final_file_content = add_links_from_list(
        file_content_with_updated_tags, linklist_content
    )
    # Save updated file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_file_content)

    tag_index.update_file_references(
        rel_path, tag_index.get_all_tags(), final_file_content
    )

    # Update the linklist based on changes in the file
    linklist_tags = get_tags_from_comment(linklist_content)

    # Determine what was added to or removed from this file.
    tags_added_to_file = current_tags - old_tags
    tags_removed_from_file = old_tags - current_tags
    if not tags_added_to_file and not tags_removed_from_file:
        return

    # Update tag index with definitions from this file for newly added tags
    all_current_file_tag_paths = get_tag_headers(
        current_tags, final_file_content, rel_path
    )
    for tag in tags_added_to_file:
        tag_index.add_definition(tag, rel_path, all_current_file_tag_paths[tag])

    # Prepare tags for update/removal in the linklist's definitions section
    tags_to_update_in_linklist: dict[str, str] = {}

    for tag in tags_removed_from_file:
        tag_index.remove_definition(tag, rel_path)
        remaining_defining_files = tag_index.get_defining_files(tag)
        if not remaining_defining_files:
            _cleanup_dead_tag_in_project(tag, dir_path, tag_index)
            tag_index.remove_tag_from_index(tag)
            # Also remove its definition from new_linklist_content
            # TODO should this be its own function?
            linklist_content = re.sub(
                rf"\[{re.escape(tag)}\]\(.*\); \n\n",
                "",
                linklist_content,
                flags=re.IGNORECASE,
            )
            linklist_content = re.sub(
                rf"{re.escape(tag)}, ", "", linklist_content, flags=re.IGNORECASE
            )
        else:
            # Tag still defined elsewhere, update its path in linklist_content
            # Pick the first remaining defining file as the new canonical source for linklist.md
            first_defining_file_path = next(iter(remaining_defining_files.keys()))
            first_defining_file_tag_path = remaining_defining_files[
                first_defining_file_path
            ]
            tags_to_update_in_linklist[tag] = first_defining_file_tag_path

    # Update the set of all tags for the linklist.
    final_linklist_tags = (linklist_tags | tags_added_to_file) - tags_removed_from_file

    # Start building the new linklist content by updating its [tags] comment.
    linklist_content = add_tags(final_linklist_tags, linklist_content)
    tags_to_update_in_linklist.update(all_current_file_tag_paths)
    linklist_content = add_taglinks_to_linklist(
        tags_to_update_in_linklist, linklist_content
    )

    # Final Saves
    tag_index.save()
    with open(linklist_path, "w", encoding="utf-8") as f:
        f.write(linklist_content)


def terminal_operation(argv=None) -> None:
    """
    Parses command-line arguments and executes the corresponding autolink operation.
    """
    parser = argparse.ArgumentParser(
        description="Automatically manage tags and links in a directory of Markdown files."
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # 'init' command
    init_parser = subparsers.add_parser(
        "init", help="Initialize a directory from scratch."
    )
    init_parser.add_argument(
        "path",
        type=str,
        default=".",
        nargs="?",
        help="Directory path to initialize.",
    )

    # 'update' command
    update_parser = subparsers.add_parser(
        "update", help="Update tags and links for a file or directory."
    )
    update_parser.add_argument(
        "path",
        type=str,
        default=".",
        nargs="?",
        help="File or directory path to update.",
    )

    args = parser.parse_args(argv)
    path = os.path.realpath(args.path)

    if args.command == "init":
        if os.path.isdir(path):
            print(f"Initializing directory: {path}")
            initialize_tagging(path)
        else:
            print("Error: 'init' command requires a directory path.")
            return
    elif args.command == "update":
        if os.path.isfile(path):
            print(f"Updating file: {path}")
            update_tags_on_file(path)
        elif os.path.isdir(path):
            print(f"Updating all files in directory: {path}")
            for name in os.listdir(path):
                file_path = os.path.join(path, name)
                if (
                    os.path.isfile(file_path)
                    and os.path.splitext(file_path)[1].lower() == ".md"
                    and not file_path.endswith("linklist.md")
                ):
                    print(f"  - Updating {name}")
                    update_tags_on_file(file_path)
        else:
            print(f"Error: Path not found - {path}")


if __name__ == "__main__":
    terminal_operation()

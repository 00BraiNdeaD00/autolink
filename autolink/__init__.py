from .tag_index import TagIndex

from .autolink import (
    get_tags_from_headers,
    get_tags_from_comment,
    add_tags,
    add_links_from_list,
    get_origin,
    initialize_tagging,
    add_taglinks_to_linklist,
    _remove_tag_references_from_file,
    get_tag_headers,
    check_list_for_tags,
    find_links_to_tag,
    _cleanup_dead_tag_in_project,
    update_tags_on_file,
    terminal_operation,
    rename_tag,
)

__all__ = [
    "TagIndex",
    "get_tags_from_headers",
    "get_tags_from_comment",
    "add_tags",
    "add_links_from_list",
    "get_origin",
    "initialize_tagging",
    "add_taglinks_to_linklist",
    "_remove_tag_references_from_file",
    "get_tag_headers",
    "check_list_for_tags",
    "find_links_to_tag",
    "_cleanup_dead_tag_in_project",
    "update_tags_on_file",
    "terminal_operation",
    "rename_tag",
]

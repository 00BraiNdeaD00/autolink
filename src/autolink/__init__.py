from .tag_index import TagIndex

from .autolink import (
    get_tags_from_headers,
    get_tags_from_comment,
    get_origin,
    initialize_tagging,
    update_tags_on_file,
    rename_tag,
    terminal_operation,
)

__all__ = [
    "TagIndex",
    "get_tags_from_headers",
    "get_tags_from_comment",
    "get_origin",
    "initialize_tagging",
    "update_tags_on_file",
    "rename_tag",
    "terminal_operation",
]

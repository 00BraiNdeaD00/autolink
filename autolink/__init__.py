"""
Autolink: A package for automatically linking related items.

This is the main entry point for the 'autolink' package, providing a
convenient public API by exposing key functions and classes from its
submodules.
"""

__version__ = "0.1.0"

# --- Public API ---
# To make your package easy to use, you can import the most important
# functions and classes from your submodules here. This allows users to
# import them directly from the top-level package, like so:
#
#   from autolink import TagIndex
#
# instead of the more verbose:
#
#   from autolink.tag_index import TagIndex

# Replace these placeholders with the actual functions and classes from your files.

# Imports from your 'tag_index.py' submodule
from .tag_index import TagIndex

# Imports from your 'autolink.py' submodule
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
)


# The __all__ variable defines what `from autolink import *` will import.
# It's best practice to list all the public names you've exposed above.
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
]

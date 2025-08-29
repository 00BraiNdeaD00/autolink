"""
Tests for the autolink functionality, specifically for renaming tags.
"""

import os
import json
from autolink import initialize_tagging, rename_tag


def test_rename_tag_successfully(tmp_path):
    """
    Tests the rename_tag function to ensure it correctly renames a tag
    across all files, including headers, comments, links, and the tag index.
    """
    # 1. Setup: create markdown files in a temporary directory
    f1 = tmp_path / "file1.md"
    f2 = tmp_path / "file2.md"
    f1.write_text(
        """
# old tag

Some content about the old tag.

This file also references another tag.
"""
    )
    f2.write_text(
        """
# another tag

This file references old tag.
"""
    )

    # 2. Initialize tagging to create the initial project state
    initialize_tagging(tmp_path)

    # 3. Call the function to be tested
    rename_tag(tmp_path, "old tag", "new tag")

    # 4. Assertions
    # Check file1.md content
    t1 = f1.read_text()
    print(t1)
    # Header should be renamed
    assert "# new tag" in t1
    assert "# old tag" not in t1
    # [tags] comment should be updated and sorted
    assert "[tags]:# (new tag, )" in t1
    # Link definition for the new tag should be present
    assert "[new tag]: file1.md#new-tag" in t1
    assert "[old tag]:" not in t1

    # Check file2.md content
    t2 = f2.read_text()
    # Reference link should be updated
    assert "[new tag][new tag]" in t2
    assert "[old tag][old tag]" not in t2
    # Link definition should be present
    assert "[new tag]: file1.md#new-tag" in t2
    assert "[old tag]:" not in t2

    # Check linklist.md content
    linklist_path = tmp_path / "linklist.md"
    with open(linklist_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "[tags]:# (another tag, new tag, )" in content
        assert "[new tag](file1.md#new-tag);" in content
        assert "[old tag]" not in content

    # Check .tag_index.json content
    tag_index_path = tmp_path / ".tag_index.json"
    with open(tag_index_path, "r", encoding="utf-8") as f:
        index_data = json.load(f)
        assert "new tag" in index_data["tags"]
        assert "old tag" not in index_data["tags"]
        # Check definitions for the new tag
        assert index_data["tags"]["new tag"]["defines"] == {
            "file1.md": "file1.md#new-tag"
        }
        # Check references for the new tag
        assert "file2.md" in index_data["tags"]["new tag"]["references"]


def test_rename_tag_non_existent(pytester, capsys):
    """
    Tests that rename_tag handles the case where the old tag does not exist
    and prints an appropriate error message.
    """
    pytester.makefile(".md", file1="# some tag")
    initialize_tagging(str(pytester.path))

    rename_tag(str(pytester.path), "non_existent_tag", "new_tag")

    captured = capsys.readouterr()
    assert "Error: Tag 'non_existent_tag' not found in the index." in captured.out


def test_rename_tag_already_exists(pytester, capsys):
    """
    Tests that rename_tag handles the case where the new tag name
    already exists and prints an appropriate error message.
    """
    pytester.makefile(
        ".md",
        file1="""
# old_tag
# new_tag
    """,
    )
    initialize_tagging(str(pytester.path))

    rename_tag(str(pytester.path), "old_tag", "new_tag")

    captured = capsys.readouterr()
    assert "Error: Tag 'new_tag' already exists. Cannot rename." in captured.out

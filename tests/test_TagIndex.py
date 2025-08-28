import pytest
import json
import os
from datetime import datetime
from autolink.tag_index import TagIndex


def create_dummy_index(path, data):
    """
    Helper function to create a dummy JSON index file for testing purposes.

    Args:
        path (Path): The file path where the dummy index should be created.
        data (dict): The dictionary data to be written as JSON to the file.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@pytest.fixture
def temp_dir(tmp_path):
    """
    Pytest fixture that provides a temporary directory for tests.
    `tmp_path` is a built-in pytest fixture.
    """
    return tmp_path


@pytest.fixture
def tag_index_path(temp_dir):
    """
    Pytest fixture that provides the expected path for the TagIndex JSON file
    within the temporary directory.
    """
    return temp_dir / TagIndex.INDEX_FILENAME


def test_tag_index_init_no_file(temp_dir):
    """
    Tests the initialization of TagIndex when no index file exists.
    It should start with an empty internal data structure.
    """
    index = TagIndex(str(temp_dir))
    assert index._data == {"tags": {}, "last_updated": None}
    assert not os.path.exists(index.index_file_path)


def test_tag_index_init_existing_file(temp_dir, tag_index_path):
    """
    Tests the initialization of TagIndex when an existing, valid index file is present.
    It should correctly load the data, converting lists to sets where appropriate.
    """
    initial_data = {
        "tags": {
            "tag1": {
                "defining_files": {"file1.md": "file1.md#tag1"},
                "referenced_by_files": ["file2.md", "file3.md"],
            }
        },
        "last_updated": "2023-01-01T12:00:00",
    }
    create_dummy_index(tag_index_path, initial_data)

    index = TagIndex(str(temp_dir))
    assert "tag1" in index._data["tags"]
    assert index._data["tags"]["tag1"]["defining_files"] == {
        "file1.md": "file1.md#tag1"
    }
    assert index._data["tags"]["tag1"]["referenced_by_files"] == {
        "file2.md",
        "file3.md",
    }  # Should be converted to set
    assert index._data["last_updated"] == "2023-01-01T12:00:00"


def test_tag_index_init_invalid_json(temp_dir, tag_index_path, capsys):
    """
    Tests the initialization of TagIndex when the existing index file contains invalid JSON.
    It should log a warning and initialize an empty index.
    """
    tag_index_path.write_text("invalid json {")
    index = TagIndex(str(temp_dir))
    assert index._data == {"tags": {}, "last_updated": None}
    captured = capsys.readouterr()
    assert "Warning: Could not decode JSON" in captured.out


def test_tag_index_save(temp_dir, tag_index_path):
    """
    Tests the `save` method of TagIndex.
    It should correctly write the index data to a JSON file, converting sets back to lists.
    """
    index = TagIndex(str(temp_dir))
    index.add_definition("tagA", "fileX.md", "fileX.md#tagA")
    index.update_file_references("fileY.md", {"tagA"}, "content with [tagA][tagA]")
    index.save()

    assert os.path.exists(tag_index_path)
    with open(tag_index_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert "tagA" in saved_data["tags"]
    assert saved_data["tags"]["tagA"]["defining_files"] == {"fileX.md": "fileX.md#tagA"}
    assert saved_data["tags"]["tagA"]["referenced_by_files"] == [
        "fileY.md"
    ]  # Should be list in saved JSON
    assert saved_data["last_updated"] is not None
    assert isinstance(datetime.fromisoformat(saved_data["last_updated"]), datetime)


def test_tag_index_add_definition(temp_dir):
    """
    Tests the `add_definition` method.
    It should correctly add new tag definitions and update existing ones.
    """
    index = TagIndex(str(temp_dir))
    index.add_definition("tag1", "fileA.md", "fileA.md#header1")
    index.add_definition("tag2", "fileB.md", "fileB.md#header2")
    index.add_definition(
        "tag1", "fileC.md", "fileC.md#header3"
    )  # Add another definition for tag1

    assert index.get_defining_files("tag1") == {
        "fileA.md": "fileA.md#header1",
        "fileC.md": "fileC.md#header3",
    }
    assert index.get_defining_files("tag2") == {"fileB.md": "fileB.md#header2"}
    assert index.get_all_tags() == {"tag1", "tag2"}


def test_tag_index_remove_definition(temp_dir):
    """
    Tests the `remove_definition` method.
    It should remove a specific file's definition for a tag and handle non-existent entries gracefully.
    """
    index = TagIndex(str(temp_dir))
    index.add_definition("tag1", "fileA.md", "fileA.md#header1")
    index.add_definition("tag1", "fileB.md", "fileB.md#header2")
    index.add_definition("tag2", "fileC.md", "fileC.md#header3")

    index.remove_definition("tag1", "fileA.md")
    assert index.get_defining_files("tag1") == {"fileB.md": "fileB.md#header2"}
    assert index.get_defining_files("tag2") == {"fileC.md": "fileC.md#header3"}

    index.remove_definition("tag1", "non_existent_file.md")  # Should not raise error
    assert index.get_defining_files("tag1") == {"fileB.md": "fileB.md#header2"}

    index.remove_definition("non_existent_tag", "fileA.md")  # Should not raise error
    assert index.get_all_tags() == {"tag1", "tag2"}


def test_tag_index_update_file_references(temp_dir):
    """
    Tests the `update_file_references` method.
    It should correctly identify and update which files reference which tags based on content.
    """
    index = TagIndex(str(temp_dir))
    index.add_definition("tag1", "fileA.md", "fileA.md#header1")
    index.add_definition("tag2", "fileB.md", "fileB.md#header2")
    index.add_definition("tag3", "fileC.md", "fileC.md#header3")

    # Initial update for fileX.md
    index.update_file_references(
        "fileX.md", {"tag1", "tag2", "tag3"}, "Content with [tag1][tag1] and [[tag2]]"
    )
    assert index.get_referenced_files("tag1") == {"fileX.md"}
    assert index.get_referenced_files("tag2") == {"fileX.md"}
    assert (
        index.get_referenced_files("tag3") == set()
    )  # tag3 not referenced in fileX.md

    # Update fileX.md again, changing references
    index.update_file_references(
        "fileX.md", {"tag1", "tag2", "tag3"}, "New content with only [[tag3]]"
    )
    assert index.get_referenced_files("tag1") == set()  # tag1 removed from fileX.md
    assert index.get_referenced_files("tag2") == set()  # tag2 removed from fileX.md
    assert index.get_referenced_files("tag3") == {"fileX.md"}  # tag3 added to fileX.md

    # Update another file, fileY.md
    index.update_file_references(
        "fileY.md", {"tag1", "tag2", "tag3"}, "Another file referencing [tag1][tag1]"
    )
    assert index.get_referenced_files("tag1") == {"fileY.md"}
    assert index.get_referenced_files("tag2") == set()
    assert index.get_referenced_files("tag3") == {"fileX.md"}


def test_tag_index_getters(temp_dir):
    """
    Tests various getter methods of the TagIndex class (`get_all_tags`, `get_defining_files`,
    `get_referenced_files`, `get_tag_data`).
    """
    index = TagIndex(str(temp_dir))
    index.add_definition("tag1", "fileA.md", "fileA.md#header1")
    index.add_definition("tag2", "fileB.md", "fileB.md#header2")
    index.update_file_references(
        "fileA.md", {"tag1", "tag2"}, "content with [tag1][tag1], [tag2][tag2]"
    )
    index.update_file_references("fileC.md", {"tag1", "tag2"}, "content with [[tag2]]")

    assert index.get_all_tags() == {"tag1", "tag2"}
    assert index.get_defining_files("tag1") == {"fileA.md": "fileA.md#header1"}
    assert index.get_defining_files("tag2") == {"fileB.md": "fileB.md#header2"}
    assert index.get_referenced_files("tag1") == {"fileA.md"}
    assert index.get_referenced_files("tag2") == {"fileA.md", "fileC.md"}
    assert index.get_tag_data("tag1") == {
        "defining_files": {"fileA.md": "fileA.md#header1"},
        "referenced_by_files": {"fileA.md"},
    }
    assert index.get_tag_data("non_existent_tag") is None


def test_tag_index_remove_tag_from_index(temp_dir):
    """
    Tests the `remove_tag_from_index` method.
    It should completely remove a tag and all its associated data from the index.
    """
    index = TagIndex(str(temp_dir))
    index.add_definition("tag1", "fileA.md", "fileA.md#header1")
    index.add_definition("tag2", "fileB.md", "fileB.md#header2")
    index.update_file_references(
        "fileA.md", {"tag1", "tag2"}, "content with [tag1][tag1]"
    )

    index.remove_tag_from_index("tag1")
    assert index.get_all_tags() == {"tag2"}
    assert index.get_tag_data("tag1") is None
    assert index.get_defining_files("tag1") == {}
    assert index.get_referenced_files("tag1") == set()

    index.remove_tag_from_index("non_existent_tag")  # Should not raise error
    assert index.get_all_tags() == {"tag2"}

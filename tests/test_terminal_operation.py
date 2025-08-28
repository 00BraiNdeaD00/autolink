import pytest
from unittest.mock import patch

# from pathlib import Path

# Assuming autolink.py is in autolink/autolink/autolink.py
# Adjust the import path if your project structure is different
from autolink.autolink import (
    terminal_operation,
    initialize_tagging,
    update_tags_on_file,
)


# Fixture to create a temporary directory with dummy markdown files
@pytest.fixture
def temp_markdown_files(tmp_path):
    """
    Creates a temporary directory with some dummy Markdown files and a non-Markdown file.
    """
    (tmp_path / "linklist.md").write_text(
        "linklist content"
    )  # This file should be skipped by update loop
    (tmp_path / "file1.md").write_text("content of file1")
    (tmp_path / "file2.md").write_text("content of file2")
    (tmp_path / "not_a_markdown.txt").write_text("plain text content")
    return tmp_path


def test_terminal_operation_init_directory(capsys, temp_markdown_files, monkeypatch):
    """
    Tests the 'init' command with a valid directory path.
    """
    monkeypatch.chdir(temp_markdown_files)
    with patch("autolink.autolink.initialize_tagging") as mock_initialize_tagging:
        # Assumes terminal_operation is modified to accept test arguments
        terminal_operation(["init"])

        # args.path will be '.', so realpath will resolve to temp_markdown_files
        mock_initialize_tagging.assert_called_once_with(str(temp_markdown_files))
        captured = capsys.readouterr()
        assert f"Initializing directory: {temp_markdown_files}" in captured.out


def test_terminal_operation_init_file_error(capsys, temp_markdown_files):
    """
    Tests the 'init' command with a file path (should result in an error).
    """
    file_path = temp_markdown_files / "file1.md"
    assert file_path.is_file()

    with patch("autolink.autolink.initialize_tagging") as mock_initialize_tagging:
        terminal_operation(["init", str(file_path)])

        mock_initialize_tagging.assert_not_called()
        captured = capsys.readouterr()
        assert "Error: 'init' command requires a directory path." in captured.out


def test_terminal_operation_update_file(capsys, temp_markdown_files):
    """
    Tests the 'update' command with a single file path.
    """
    file_path = temp_markdown_files / "file1.md"
    assert file_path.is_file()
    resolved_path = str(file_path.resolve())

    with patch("autolink.autolink.update_tags_on_file") as mock_update_tags_on_file:
        terminal_operation(["update", str(file_path)])

        mock_update_tags_on_file.assert_called_once_with(resolved_path)
        captured = capsys.readouterr()
        assert f"Updating file: {resolved_path}" in captured.out


def test_terminal_operation_update_directory(capsys, temp_markdown_files, monkeypatch):
    """
    Tests the 'update' command with a directory path, ensuring all .md files are processed.
    """
    monkeypatch.chdir(temp_markdown_files)

    with patch("autolink.autolink.update_tags_on_file") as mock_update_tags_on_file:
        terminal_operation(["update"])  # Use default path '.'

        assert mock_update_tags_on_file.call_count == 2
        # The order of listdir is not guaranteed, so use assert_any_call
        mock_update_tags_on_file.assert_any_call(str(temp_markdown_files / "file1.md"))
        mock_update_tags_on_file.assert_any_call(str(temp_markdown_files / "file2.md"))

        captured = capsys.readouterr()
        resolved_path = str(temp_markdown_files.resolve())
        assert f"Updating all files in directory: {resolved_path}" in captured.out
        assert "  - Updating file1.md" in captured.out
        assert "  - Updating file2.md" in captured.out
        assert (
            "  - Updating linklist.md" not in captured.out
        )  # linklist should be skipped
        assert (
            "  - Updating not_a_markdown.txt" not in captured.out
        )  # non-md should be skipped


def test_terminal_operation_update_non_existent_path(capsys, temp_markdown_files):
    """
    Tests the 'update' command with a non-existent path (should result in an error).
    """
    non_existent_path = temp_markdown_files / "non_existent_dir"
    assert not non_existent_path.exists()
    resolved_path = str(non_existent_path.resolve())

    with patch("autolink.autolink.update_tags_on_file") as mock_update:
        terminal_operation(["update", str(non_existent_path)])
        mock_update.assert_not_called()

    captured = capsys.readouterr()
    assert f"Error: Path not found - {resolved_path}" in captured.out

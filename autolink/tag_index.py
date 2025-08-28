import json
import os
import re
from typing import Any, Optional
from datetime import datetime


class TagIndex:
    INDEX_FILENAME = "autolink_index.json"

    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.index_file_path = os.path.join(directory_path, self.INDEX_FILENAME)
        self._data: dict[str, Any] = {"tags": {}, "last_updated": None}
        self._load()

    def _load(self):
        if os.path.exists(self.index_file_path):
            try:
                with open(self.index_file_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # Convert referenced_by_files lists back to sets for internal use
                    for tag_name, tag_info in loaded_data.get("tags", {}).items():
                        if "referenced_by_files" in tag_info:
                            tag_info["referenced_by_files"] = set(
                                tag_info["referenced_by_files"]
                            )
                    self._data = loaded_data
            except json.JSONDecodeError:
                print(
                    f"Warning: Could not decode JSON from {self.index_file_path}. Initializing empty index."
                )
            except Exception as e:
                print(
                    f"Error loading index from {self.index_file_path}: {e}. Initializing empty index."
                )
        else:
            print(
                f"No index file found at {self.index_file_path}. Initializing empty index."
            )

    def save(self):
        self._data["last_updated"] = datetime.now().isoformat()
        # Convert referenced_by_files sets to lists for JSON serialization
        data_to_save = self._data.copy()
        data_to_save["tags"] = {
            tag_name: {
                **tag_info,
                "referenced_by_files": list(tag_info["referenced_by_files"]),
            }
            for tag_name, tag_info in self._data["tags"].items()
        }
        with open(self.index_file_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)

    def add_definition(self, tag: str, file_path: str, tag_path_within_file: str):
        """Adds or updates a tag's definition location."""
        tag_data = self._data["tags"].setdefault(
            tag, {"defining_files": {}, "referenced_by_files": set()}
        )
        tag_data["defining_files"][file_path] = tag_path_within_file

    def remove_definition(self, tag: str, file_path: str):
        """Removes a tag's definition from a specific file."""
        if (
            tag in self._data["tags"]
            and file_path in self._data["tags"][tag]["defining_files"]
        ):
            del self._data["tags"][tag]["defining_files"][file_path]

    def update_file_references(
        self, file_path: str, all_tags_in_project: set[str], file_content: str
    ):
        """
        Scans the given file content for [tag][tag] and [[tag]] references and updates the index.
        This function needs to be called after a file's content has been finalized.
        It will update the `referenced_by_files` for all tags.
        """
        # First, remove this file from all tags it might have previously referenced.
        # This is the safest way to ensure correctness before re-scanning.
        for tag_name, tag_data in self._data["tags"].items():
            if file_path in tag_data["referenced_by_files"]:
                tag_data["referenced_by_files"].remove(file_path)

        # Then, re-scan the file content for current references and add them.
        referenced_tags_in_file = set()
        for (
            tag
        ) in all_tags_in_project:  # Iterate over all known tags to check for references
            if re.search(
                rf"\[{re.escape(tag)}\]\[{re.escape(tag)}\]",
                file_content,
                re.IGNORECASE,
            ) or re.search(rf"\[\[{re.escape(tag)}\]\]", file_content, re.IGNORECASE):
                referenced_tags_in_file.add(tag)

        for tag in referenced_tags_in_file:
            tag_data = self._data["tags"].setdefault(
                tag, {"defining_files": {}, "referenced_by_files": set()}
            )
            tag_data["referenced_by_files"].add(file_path)

    def get_defining_files(self, tag: str) -> dict[str, str]:
        """Returns a dictionary of defining files for a tag."""
        return self._data["tags"].get(tag, {}).get("defining_files", {})

    def get_referenced_files(self, tag: str) -> set[str]:
        """Returns a set of files referencing a tag."""
        return self._data["tags"].get(tag, {}).get("referenced_by_files", set())

    def get_all_tags(self) -> set[str]:
        """Returns a set of all tags in the index."""
        return set(self._data["tags"].keys())

    def get_tag_data(self, tag: str) -> Optional[dict[str, Any]]:
        """Returns all data for a specific tag."""
        return self._data["tags"].get(tag)

    def remove_tag_from_index(self, tag: str):
        """Completely removes a tag from the index."""
        if tag in self._data["tags"]:
            del self._data["tags"][tag]

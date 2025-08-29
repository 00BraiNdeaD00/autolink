# Autolink

`Autolink` is a command-line utility that automatically discovers tags and creates cross-links between your Markdown files, turning your collection of notes into a navigable personal wiki.

## Description

This tool is designed for anyone who maintains a personal knowledge base, a digital garden, or a Zettelkasten-style system using Markdown files. It works by:

1.  Scanning your files to find tags from various sources (like `# Headers`, `[[wikilinks]]`, and a special `[tags]:# (...)` comment).
2.  Automatically converting occurrences of these tags into reference-style Markdown links (`[tag][tag]`).
3.  Maintaining a central `linklist.md`, and a `tag_index.json` file that contains all the link definitions, pointing each tag to its canonical source file.

This process helps you build a rich, interconnected web of knowledge without the manual effort of creating and updating links.

## Installation

You can install `Autolink` directly from the repository using pip:

```bash
pip install autolink-md
```

## Usage

Provide a simple example of how to use your library.

```python
# Example Usage of Autolink
import os
import autolink

path = os.path.realpath("my_folder")
initialize_tagging(path)
```
there are 3 commands:
1. ```console
    $autolink init path ./path/to/folder
    ```
1. ```console
    $autolink update path ./path/to/folder
    ```
3. ```console
    $autolink rename --old old_tag --new new_tag path ./path/to/folder
    ```
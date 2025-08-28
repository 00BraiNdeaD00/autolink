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
pip install Autolink
```
<!-- ^^hoffentlich bald -->

## Usage

Provide a simple example of how to use your library.

```python
# Example Usage of Autolink
import Autolink

# ... your example code here ...
```
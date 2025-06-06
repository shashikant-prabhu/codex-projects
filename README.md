# codex-projects

This repository contains a simple Python project for converting the contents of
text files to lowercase. The project includes a small submodule as an example of
structuring code in subpackages.

## Usage

The main function `convert_file_to_lowercase` reads a file and replaces its
content with a lowercase version.

```
from lowercase_converter import convert_file_to_lowercase

convert_file_to_lowercase("path/to/file.txt")
```

The subproject exposes `count_lines` which returns the number of lines in a
file.

```
from lowercase_converter.subproject import count_lines

num = count_lines("path/to/file.txt")
```

## Running Tests

Tests use `pytest`. Install the requirements and run:

```
pip install -r requirements.txt
pytest
```


## Duplicate File Cleaner

A Flask-based web utility is included for detecting and removing duplicate files.
Run the application with:

```
python -m duplicate_file_cleaner.webapp
```
Enter the directory to scan or select **Scan entire system**. You can limit the
search to specific file types such as images, videos, PDF or Word documents and
navigate the folder hierarchy using the built‑in browser. Review the duplicates
found and confirm deletion. The tool keeps the oldest copy of each duplicate set
and logs removals to `duplicate_cleaner.log` while reporting the freed disk
space.

### New Features

* Browsing directories now supports pagination to avoid overly long lists.
* You can limit the number of directories scanned per phase and estimate scan
  time before running a full search.
* Deletion history is stored in a local SQLite database located in your home
  directory and can be viewed from the application's main page.

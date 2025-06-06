"""Converter module for converting file content to lowercase."""

from pathlib import Path


def convert_file_to_lowercase(path: str) -> None:
    """Read a text file and convert all uppercase characters to lowercase.

    The conversion is done in-place, replacing the original file content.

    Parameters
    ----------
    path: str
        Path to the file to convert.
    """
    file_path = Path(path)
    text = file_path.read_text()
    lower_text = text.lower()
    file_path.write_text(lower_text)


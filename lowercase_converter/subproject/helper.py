"""Helper module inside subproject."""


def count_lines(path: str) -> int:
    """Return the number of lines in a file."""
    with open(path, 'r') as f:
        return len(f.readlines())


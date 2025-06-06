import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tempfile

from lowercase_converter import convert_file_to_lowercase
from lowercase_converter.subproject import count_lines


def test_convert_file_to_lowercase():
    content = "Hello\nWORLD"
    with tempfile.NamedTemporaryFile(delete=False, mode="w+") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        convert_file_to_lowercase(tmp_path)
        with open(tmp_path, "r") as f:
            assert f.read() == content.lower()
    finally:
        os.remove(tmp_path)


def test_count_lines():
    lines = ["a", "b", "c"]
    with tempfile.NamedTemporaryFile(delete=False, mode="w+") as tmp:
        tmp.write("\n".join(lines))
        tmp_path = tmp.name
    try:
        assert count_lines(tmp_path) == len(lines)
    finally:
        os.remove(tmp_path)


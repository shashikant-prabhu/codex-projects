import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from duplicate_file_cleaner.utils import find_duplicates, delete_files


def test_find_duplicates(tmp_path):
    file1 = tmp_path / "a.txt"
    file1.write_text("hello")
    file2 = tmp_path / "b.txt"
    file2.write_text("hello")
    file3 = tmp_path / "c.txt"
    file3.write_text("world")

    dups = find_duplicates(str(tmp_path))
    # Expect one group containing file1 and file2
    assert len(dups) == 1
    group = {p.name for p in dups[0]}
    assert group == {"a.txt", "b.txt"}


def test_delete_files(tmp_path):
    f1 = tmp_path / "a.txt"
    f1.write_text("hello")
    log = tmp_path / "log.txt"
    freed = delete_files([f1], log)
    assert freed == len("hello")
    assert not f1.exists()
    assert "Deleted" in log.read_text()

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from duplicate_file_cleaner import utils
from duplicate_file_cleaner.utils import find_duplicates, delete_files, get_history


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


def test_find_duplicates_limit(tmp_path):
    (tmp_path / "a.txt").write_text("one")
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "b.txt").write_text("one")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "c.txt").write_text("one")
    dups = find_duplicates(str(tmp_path), max_dirs=1)
    # Only root directory scanned so duplicates should be empty
    assert dups == []


def test_find_duplicates_extensions(tmp_path):
    (tmp_path / "a.jpg").write_text("img")
    (tmp_path / "b.jpg").write_text("img")
    (tmp_path / "c.txt").write_text("other")
    dups = find_duplicates(str(tmp_path), extensions=[".jpg"])
    assert len(dups) == 1
    names = {p.name for p in dups[0]}
    assert names == {"a.jpg", "b.jpg"}


def test_delete_files(tmp_path):
    f1 = tmp_path / "a.txt"
    f1.write_text("hello")
    log = tmp_path / "log.txt"
    freed = delete_files([f1], log)
    assert freed == len("hello")
    assert not f1.exists()
    assert "Deleted" in log.read_text()


def test_delete_files_history(tmp_path, monkeypatch):
    db = tmp_path / "history.db"
    monkeypatch.setattr(utils, "HISTORY_DB", db)
    f1 = tmp_path / "x.txt"
    f1.write_text("hi")
    log = tmp_path / "log.txt"
    delete_files([f1], log)
    history = get_history(db_path=db)
    assert history
    assert "x.txt" in history[-1][1]

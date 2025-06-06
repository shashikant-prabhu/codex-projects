"""Flask web application for cleaning duplicate files."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable, List

from flask import Flask, render_template_string, request, url_for

from .utils import delete_files, find_duplicates, get_history

app = Flask(__name__)
LOG_FILE = Path("duplicate_cleaner.log")

TYPE_MAP = {
    "all": None,
    "images": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
    "videos": [".mp4", ".avi", ".mov", ".mkv"],
    "pdf": [".pdf"],
    "word": [".doc", ".docx"],
}

INDEX_HTML = """
<!doctype html>
<title>Duplicate File Cleaner</title>
<h1>Select Directory</h1>
<form method="post" action="{{ url_for('scan') }}">
  <input type="text" name="directory" placeholder="Path" size="50" value="{{ path }}">
  <label><input type="checkbox" name="entire" value="1"> Scan entire system</label><br>
  <label>File types:
    <select name="type">
      <option value="all">All</option>
      <option value="images">Images</option>
      <option value="videos">Videos</option>
      <option value="pdf">PDF</option>
      <option value="word">Word</option>
    </select>
  </label><br>
  <label>Directories per phase: <input type="number" name="max_dirs" value="0"></label><br>
  <input type="submit" value="Scan">
  <input type="submit" formaction="{{ url_for('estimate') }}" value="Estimate Time">
</form>
<p><a href="{{ url_for('browse') }}">Browse directories</a></p>
<p><a href="{{ url_for('history') }}">View cleanup history</a></p>
"""

RESULT_HTML = """
<!doctype html>
<title>Duplicates Found</title>
<h1>Duplicates</h1>
<form method="post" action="{{ url_for('delete') }}">
  <input type="hidden" name="data" value='{{ data }}'>
  <table border="1" cellpadding="5">
    <tr><th>Keep</th><th>Delete</th></tr>
    {% for group in duplicates %}
      <tr>
        <td>{{ group[0] }}</td>
        <td>
          {% for file in group[1:] %}
            <label><input type="checkbox" name="delete" value="{{ file }}" checked>{{ file }}</label><br>
          {% endfor %}
        </td>
      </tr>
    {% endfor %}
  </table>
  <p>Total potential space to free: {{ space }} bytes</p>
  <input type="submit" value="Delete Selected">
</form>
"""

DELETE_HTML = """
<!doctype html>
<title>Deletion Result</title>
<h1>Deleted Files</h1>
<ul>
{% for f in deleted %}
  <li>{{ f }}</li>
{% endfor %}
</ul>
<p>Freed {{ freed }} bytes.</p>
<a href="{{ url_for('index') }}">Back</a>
"""

HISTORY_HTML = """
<!doctype html>
<title>History</title>
<h1>Cleanup History</h1>
<table border="1" cellpadding="5">
  <tr><th>Timestamp</th><th>Files</th><th>Bytes Freed</th></tr>
  {% for ts, paths, freed in rows %}
  <tr>
    <td>{{ ts }}</td>
    <td><pre>{{ paths }}</pre></td>
    <td>{{ freed }}</td>
  </tr>
  {% endfor %}
</table>
<a href="{{ url_for('index') }}">Back</a>
"""

BROWSE_HTML = """
<!doctype html>
<title>Browse</title>
<h1>Browse Directories</h1>
<ul>
  {% if parent %}
  <li><a href="{{ url_for('browse', path=parent) }}">..</a></li>
  {% endif %}
  {% for d in dirs %}
  <li><a href="{{ url_for('browse', path=d) }}">{{ d }}</a></li>
  {% endfor %}
</ul>
<p>
  {% if prev_offset is not none %}
    <a href="{{ url_for('browse', path=current, offset=prev_offset) }}">Prev</a>
  {% endif %}
  {% if next_offset is not none %}
    <a href="{{ url_for('browse', path=current, offset=next_offset) }}">Next</a>
  {% endif %}
</p>
<p><a href="{{ url_for('index', path=current) }}">Select this directory</a></p>
"""


@app.route("/")
def index():
    path = request.args.get("path", "")
    return render_template_string(INDEX_HTML, path=path)


@app.route("/browse")
def browse():
    path = request.args.get("path", Path.home())
    offset = int(request.args.get("offset", 0))
    p = Path(path)
    try:
        dirs = [str(d) for d in p.iterdir() if d.is_dir()]
    except PermissionError:
        dirs = []
    dirs.sort()
    limit = 20
    page_dirs = dirs[offset : offset + limit]
    next_offset = offset + limit if offset + limit < len(dirs) else None
    prev_offset = offset - limit if offset - limit >= 0 else None
    parent = str(p.parent) if p != p.parent else None
    return render_template_string(
        BROWSE_HTML,
        dirs=page_dirs,
        parent=parent,
        current=str(p),
        next_offset=next_offset,
        prev_offset=prev_offset,
    )


@app.route("/scan", methods=["POST"])
def scan():
    directory = request.form.get("directory", "")
    if request.form.get("entire"):
        if os.name == "nt":
            directory = os.environ.get("SystemDrive", "C:\\")
        else:
            directory = "/"
    if os.name == "nt" and len(directory) == 2 and directory[1] == ":":
        directory += "\\"
    ftype = request.form.get("type", "all")
    extensions = TYPE_MAP.get(ftype)
    max_dirs = request.form.get("max_dirs")
    try:
        limit = int(max_dirs) if max_dirs else None
    except ValueError:
        limit = None
    duplicates = find_duplicates(directory, extensions, max_dirs=limit if limit and limit > 0 else None)
    data = json.dumps([[str(p) for p in g] for g in duplicates])
    space = sum(sum(p.stat().st_size for p in g[1:]) for g in duplicates)
    return render_template_string(RESULT_HTML, duplicates=duplicates, space=space, data=data)


@app.route("/estimate", methods=["POST"])
def estimate():
    directory = request.form.get("directory", "")
    if request.form.get("entire"):
        if os.name == "nt":
            directory = os.environ.get("SystemDrive", "C:\\")
        else:
            directory = "/"
    if os.name == "nt" and len(directory) == 2 and directory[1] == ":":
        directory += "\\"
    ftype = request.form.get("type", "all")
    extensions = TYPE_MAP.get(ftype)
    start = time.time()
    count = 0
    for root, _, files in os.walk(directory):
        if time.time() - start > 180:
            break
        for name in files:
            if extensions is not None and Path(name).suffix.lower() not in extensions:
                continue
            count += 1
    seconds = int(count * 0.002)
    return f"Estimated time: {seconds}s for {count} files"


@app.route("/delete", methods=["POST"])
def delete():
    data = json.loads(request.form.get("data", "[]"))
    delete_set = set(request.form.getlist("delete"))
    deleted: List[str] = []
    freed = 0
    groups = [[Path(p) for p in g] for g in data]
    for group in groups:
        for p in group[1:]:
            if str(p) in delete_set:
                freed += delete_files([p], LOG_FILE)
                deleted.append(str(p))
    return render_template_string(DELETE_HTML, deleted=deleted, freed=freed)


@app.route("/history")
def history():
    rows = get_history()
    return render_template_string(HISTORY_HTML, rows=rows)


if __name__ == "__main__":
    app.run(debug=True)

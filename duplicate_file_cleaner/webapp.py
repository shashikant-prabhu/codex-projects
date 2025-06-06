"""Flask web application for cleaning duplicate files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List

from flask import Flask, render_template_string, request, url_for

from .utils import delete_files, find_duplicates

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
  <input type="submit" value="Scan">
</form>
<p><a href="{{ url_for('browse') }}">Browse directories</a></p>
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
<p><a href="{{ url_for('index', path=current) }}">Select this directory</a></p>
"""


@app.route("/")
def index():
    path = request.args.get("path", "")
    return render_template_string(INDEX_HTML, path=path)


@app.route("/browse")
def browse():
    path = request.args.get("path", Path.home())
    p = Path(path)
    try:
        dirs = [str(d) for d in p.iterdir() if d.is_dir()]
    except PermissionError:
        dirs = []
    parent = str(p.parent) if p != p.parent else None
    return render_template_string(BROWSE_HTML, dirs=dirs, parent=parent, current=str(p))


@app.route("/scan", methods=["POST"])
def scan():
    directory = request.form.get("directory", "")
    if request.form.get("entire"):
        if os.name == "nt":
            directory = os.environ.get("SystemDrive", "C:\\")
        else:
            directory = "/"
    ftype = request.form.get("type", "all")
    extensions = TYPE_MAP.get(ftype)
    duplicates = find_duplicates(directory, extensions)
    data = json.dumps([[str(p) for p in g] for g in duplicates])
    space = sum(sum(p.stat().st_size for p in g[1:]) for g in duplicates)
    return render_template_string(RESULT_HTML, duplicates=duplicates, space=space, data=data)


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


if __name__ == "__main__":
    app.run(debug=True)

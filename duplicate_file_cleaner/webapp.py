"""Flask web application for cleaning duplicate files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from flask import Flask, redirect, render_template_string, request, url_for

from .utils import delete_files, find_duplicates

app = Flask(__name__)
LOG_FILE = Path("duplicate_cleaner.log")

INDEX_HTML = """
<!doctype html>
<title>Duplicate File Cleaner</title>
<h1>Select Directory</h1>
<form method="post" action="{{ url_for('scan') }}">
  <input type="text" name="directory" placeholder="Path" size="50">
  <input type="submit" value="Scan">
</form>
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


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/scan", methods=["POST"])
def scan():
    directory = request.form.get("directory", "")
    duplicates = find_duplicates(directory)
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

#!/usr/bin/env python3
import re
import subprocess
import tempfile
from pathlib import Path

html_path = Path("app/src/main/assets/index.html")
html = html_path.read_text(encoding="utf-8")
if len(html) < 30000:
    raise SystemExit("Lesson UI file is unexpectedly short; payload reconstruction may be incomplete.")

scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
if len(scripts) != 1:
    raise SystemExit(f"Expected one inline script, got {len(scripts)}.")
with tempfile.NamedTemporaryFile(mode="w", suffix=".js", encoding="utf-8") as f:
    f.write(scripts[0])
    f.flush()
    subprocess.run(["node", "--check", f.name], check=True)

lesson_pattern = re.compile(r"\n\{id:'([^']+)'.*?words:\[(.*?)\]\}", re.S)
row_pattern = re.compile(r"\['((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)'\]")
lessons = lesson_pattern.findall(html)
if len(lessons) != 6:
    raise SystemExit(f"Expected 6 lessons, found {len(lessons)}.")
expected_audio = []
for lesson_id, body in lessons:
    rows = row_pattern.findall(body)
    if len(rows) != 10:
        raise SystemExit(f"{lesson_id}: expected ten words, found {len(rows)}.")
    for index, row in enumerate(rows):
        expected_audio += [
            Path("app/src/main/assets/audio") / f"{lesson_id}-{index}-word.mp3",
            Path("app/src/main/assets/audio") / f"{lesson_id}-{index}-phrase.mp3",
        ]
missing = [str(p) for p in expected_audio if not p.is_file() or p.stat().st_size < 100]
if missing:
    raise SystemExit("Missing offline audio files: " + ", ".join(missing[:6]))
manifest = Path("app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
if "android.permission.INTERNET" in manifest:
    raise SystemExit("Offline build check failed: INTERNET permission is present.")
print(f"PASS: {len(lessons)} lessons, 60 vocabulary items, valid JavaScript, {len(expected_audio)} local audio clips, no INTERNET permission.")

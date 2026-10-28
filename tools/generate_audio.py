#!/usr/bin/env python3
"""Generate small, bundled Russian speech clips from the offline lesson source."""
import re
import subprocess
import tempfile
from pathlib import Path

HTML = Path("app/src/main/assets/index.html")
AUDIO = Path("app/src/main/assets/audio")
text = HTML.read_text(encoding="utf-8")

lesson_pattern = re.compile(r"\n\{id:'([^']+)'.*?words:\[(.*?)\]\}", re.S)
row_pattern = re.compile(
    r"\['((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)','((?:\\.|[^'\\])*)'\]"
)

AUDIO.mkdir(parents=True, exist_ok=True)
generated = 0
lessons = lesson_pattern.findall(text)
if len(lessons) != 6:
    raise SystemExit(f"Expected 6 lessons; parsed {len(lessons)}")

for lesson_id, body in lessons:
    rows = row_pattern.findall(body)
    if len(rows) != 10:
        raise SystemExit(f"Lesson {lesson_id}: expected 10 entries, parsed {len(rows)}")
    for index, row in enumerate(rows):
        for kind, phrase in (("word", row[0]), ("phrase", row[3])):
            target = AUDIO / f"{lesson_id}-{index}-{kind}.mp3"
            with tempfile.TemporaryDirectory() as temp:
                wav = Path(temp) / "clip.wav"
                subprocess.run(
                    ["espeak-ng", "-v", "ru", "-s", "132", "-w", str(wav), phrase],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
                )
                subprocess.run(
                    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                     "-ar", "22050", "-ac", "1", "-b:a", "48k", str(target)],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
                )
            generated += 1

if generated != 120:
    raise SystemExit(f"Expected 120 audio clips, generated {generated}")
clips = list(AUDIO.glob("*.mp3"))
if len(clips) != 120 or any(p.stat().st_size < 100 for p in clips):
    raise SystemExit("Bundled audio inventory or size check failed")
print(f"Generated and checked {len(clips)} Russian offline audio clips.")

#!/usr/bin/env python3
"""Roll an existing course over to a new semester.

Automates the README "End-of-semester rollover" checklist:
  1. freeze the finished semester's page (skipped if already frozen)
  2. create <course>/<new-term>/ with the Jekyll stub and empty media folders
  3. reset _data/<course>/ for the new semester (course info, page metadata,
     main sections and grading are carried over with media paths rewritten;
     schedule, lectures, talks, labs, students and group projects start empty)
  4. point <course>/index.html at the new term
  5. update the Pages CMS config (.pages.yml) so uploads land in the new term folder
  6. add the semester to _data/courses.yml and mark it current

Usage: scripts/new-semester.py <course> <new-term> [--term-label "Fall 2026"] [--dry-run] [--skip-freeze]
  e.g. scripts/new-semester.py designforhri f26

Afterwards, seed the schedule from the planning sheet with
scripts/import-semester-sheet.py, then finish in Pages CMS.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit(
        "PyYAML is required. From the repo root run:\n"
        "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    )

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

TERM_LABELS = {"f": "Fall", "w": "Winter", "s": "Summer", "su": "Summer", "sp": "Spring"}
CARRY_OVER = ["course.yml", "head.yml", "main.yml", "grading.yml", "social-links.yml"]
RESET_TO_EMPTY_LIST = ["schedule.yml", "lectures.yml", "talks.yml", "labs.yml", "group_projects.yml"]
MEDIA_DIRS = ["img", "img/labs", "img/gps", "img/talk_logos", "snippets"]

DRY_RUN = False
TOUCHED: list[str] = []
NOTES: list[str] = []


# --- helpers -----------------------------------------------------------------

def fail(msg: str) -> None:
    sys.exit(f"error: {msg}")


def note(msg: str) -> None:
    NOTES.append(msg)


def write(path: str, text: str) -> None:
    TOUCHED.append(path)
    if DRY_RUN:
        print(f"  WOULD write {path}")
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")
    print(f"  wrote {path}")


def copy(src: str, dst: str) -> None:
    TOUCHED.append(dst)
    if DRY_RUN:
        print(f"  WOULD copy {src} -> {dst}")
        return
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  copied {src} -> {dst}")


def mkdir(path: str) -> None:
    if DRY_RUN:
        print(f"  WOULD mkdir {path}/")
        return
    Path(path).mkdir(parents=True, exist_ok=True)


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def capture(lines: list[str], start: int) -> tuple[int, int]:
    """[start, end) of the list item at `start` plus every deeper-indented/blank line after it."""
    base = indent(lines[start])
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and indent(line) <= base:
            break
        end += 1
    return start, end


def yaml_scalar(value: str) -> str:
    """A YAML-safe scalar: bare when plainly safe, otherwise JSON (= YAML double-quoted)."""
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 .'()/\-]*", value) and value.lower() not in {"yes", "no", "true", "false", "null"}:
        return value
    return json.dumps(value, ensure_ascii=False)


def term_label(term: str, override: str | None) -> str:
    if override:
        return override
    m = re.fullmatch(r"(f|w|s|su|sp)(\d{2})", term)
    if not m:
        fail(f"term '{term}' must look like f26 / w27 / su26 / sp26 (or pass --term-label)")
    return f"{TERM_LABELS[m.group(1)]} {2000 + int(m.group(2))}"


def drop_image_sections(main_yml: str) -> str:
    """Remove image-only sections (class photo, project collages) from main.yml.

    Those are added at the end of a semester once there is a group photo; a new
    semester starts with text sections only. Text formatting is preserved by
    cutting whole top-level list items rather than re-dumping the YAML.
    """
    lines = main_yml.split("\n")
    starts = [i for i, l in enumerate(lines) if l.startswith("- ")] + [len(lines)]
    kept = lines[: starts[0]] if starts else lines
    dropped = 0
    for a, b in zip(starts, starts[1:]):
        chunk = lines[a:b]
        try:
            item = (yaml.safe_load("\n".join(chunk)) or [{}])[0]
        except yaml.YAMLError:
            item = {}
        if item.get("image") is True and not item.get("content"):
            dropped += 1
            continue
        kept.extend(chunk)
    if dropped:
        note(f"main.yml: removed {dropped} image section(s) from last semester (class photo etc.); add this semester's at the end of term")
    return "\n".join(kept)


# --- steps -------------------------------------------------------------------

def detect_old_term(course: str) -> str:
    redirect = read(f"{course}/index.html")
    m = re.search(r"url=\./([a-z0-9]+)/", redirect)
    if not m:
        fail(f"could not find the current term in {course}/index.html (expected a meta refresh to ./<term>/)")
    return m.group(1)


def freeze_old_term(course: str, old: str, skip: bool) -> None:
    page = f"{course}/{old}/index.html"
    if not Path(page).exists():
        note(f"{page} does not exist; nothing to freeze")
        return
    first = read(page).split("\n", 1)[0].strip()
    if first != "---":
        print(f"  {page} is already frozen (static HTML), skipping freeze")
        return
    if skip:
        note(f"--skip-freeze: {page} is still a live stub and will render EMPTY once _data is reset. Run scripts/freeze-course.sh {course} {old} first.")
        return
    if DRY_RUN:
        print(f"  WOULD run scripts/freeze-course.sh {course} {old}")
        return
    print(f"  freezing {course}/{old} (bundle exec jekyll build)...")
    subprocess.run(["scripts/freeze-course.sh", course, old], check=True)
    TOUCHED.append(page)


def create_term_folder(course: str, new: str) -> None:
    for d in MEDIA_DIRS:
        mkdir(f"{course}/{new}/{d}")
    write(f"{course}/{new}/index.html", f"---\nlayout: course\ncourse: {course}\n---\n")


def carry_over_data(course: str, old: str, new: str, label: str) -> None:
    old_prefix = f"/{course}/{old}/"
    new_prefix = f"/{course}/{new}/"
    path_re = re.compile(re.escape(old_prefix) + r"[^\s\"',)]+")
    copied: set[str] = set()

    for name in CARRY_OVER:
        path = f"_data/{course}/{name}"
        if not Path(path).exists():
            note(f"{path} missing; skipped")
            continue
        text = read(path)
        if name == "main.yml":
            text = drop_image_sections(text)
        for ref in sorted(set(path_re.findall(text))):
            rel = ref[len(old_prefix):]
            src, dst = f"{course}/{old}/{rel}", f"{course}/{new}/{rel}"
            if rel in copied:
                continue
            copied.add(rel)
            if Path(src).exists():
                copy(src, dst)
            else:
                note(f"{path} references {src}, which does not exist; the new page will 404 on {dst}")
        text = text.replace(old_prefix, new_prefix)
        if name == "course.yml":
            text, n = re.subn(r"^(\s*top-text:\s*).*$", rf"\g<1>This course is running in {label}", text, flags=re.M)
            if n != 1:
                note(f"course.yml: expected one yellow_box.top-text line, found {n}; set it by hand")
        write(path, text)

    logo = f"{course}/{old}/img/class-logo.png"
    if "img/class-logo.png" not in copied:
        if Path(logo).exists():
            copy(logo, f"{course}/{new}/img/class-logo.png")
        else:
            note(f"no {logo}; add {course}/{new}/img/class-logo.png (the page loads it by relative path)")

    for name in RESET_TO_EMPTY_LIST:
        write(f"_data/{course}/{name}", "[]\n")
    write(f"_data/{course}/students.yml", "undergraduates: []\ngraduates: []\n")

    course_info = yaml.safe_load(read(f"_data/{course}/course.yml")) or {}
    yb = course_info.get("yellow_box") or {}
    for sec in yb.get("sections") or []:
        note(f"review yellow box '{sec.get('title')}': {sec.get('date')}, {sec.get('time')}, {sec.get('location')}")
    note(f"review office: {course_info.get('office')}")
    for key in ("instructors", "GSIs", "IAs"):
        names = ", ".join(p.get("name", "?") for p in (course_info.get(key) or []))
        note(f"review {key}: {names or '(none)'}")
    note("review grading.yml percentages (carried over from last semester)")


def rewrite_redirect(course: str, old: str, new: str) -> None:
    path = f"{course}/index.html"
    text = read(path)
    n = text.count(f"./{old}/")
    if n == 0:
        fail(f"{path} does not reference ./{old}/")
    write(path, text.replace(f"./{old}/", f"./{new}/"))


def rewrite_pages_cms(course: str, old: str, new: str) -> None:
    path = ".pages.yml"
    lines = read(path).split("\n")
    old_ref, new_ref = f"{course}/{old}", f"{course}/{new}"

    media_start = next((i for i, l in enumerate(lines) if l.rstrip() == f"  - name: {course}"), None)
    if media_start is None:
        fail(f".pages.yml: no media entry '  - name: {course}'")
    _, media_end = capture(lines, media_start)
    media_hits = 0
    for i in range(media_start, media_end):
        if re.match(r"^\s*(input|output):\s*/?" + re.escape(old_ref) + r"\s*$", lines[i]):
            lines[i] = lines[i].replace(old_ref, new_ref)
            media_hits += 1
    if media_hits != 2:
        note(f".pages.yml media entry '{course}': replaced {media_hits} input/output lines (expected 2)")

    group_start = next((i for i, l in enumerate(lines) if l.strip() == f"- name: {course}-current"), None)
    if group_start is None:
        fail(f".pages.yml: no content group '- name: {course}-current'")
    _, group_end = capture(lines, group_start)
    path_hits = 0
    for i in range(group_start, group_end):
        if re.match(r"^\s*path:\s*" + re.escape(old_ref) + r"(/.*)?\s*$", lines[i]):
            lines[i] = lines[i].replace(old_ref, new_ref)
            path_hits += 1
    print(f"  .pages.yml: {media_hits} media lines + {path_hits} upload paths now point at {new_ref}")

    text = "\n".join(lines)
    leftovers = [str(i + 1) for i, l in enumerate(lines) if old_ref in l]
    if leftovers:
        note(f".pages.yml still mentions {old_ref} on line(s) {', '.join(leftovers)}; check them")
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as e:
        fail(f".pages.yml would no longer parse: {e}")
    write(path, text)


def add_semester_to_directory(course: str, new: str, label: str) -> None:
    path = "_data/courses.yml"
    data = yaml.safe_load(read(path)) or {}
    target = None
    for c in data.get("courses") or []:
        for sem in c.get("semesters") or []:
            if str(sem.get("url", "")).startswith(f"/{course}/"):
                target = c
                break
        if target:
            break
    if target is None:
        note(f"{path}: no course lists a /{course}/ semester; add '{label}' under the course by hand in Pages CMS")
        return
    if any(str(s.get("url", "")).rstrip("/") == f"/{course}/{new}" for s in target["semesters"]):
        print(f"  {path} already lists /{course}/{new}/, leaving it")
        return

    lines = read(path).split("\n")
    number = str(target["number"])
    start = next((i for i, l in enumerate(lines) if re.match(r"^\s*- number:\s*['\"]?" + re.escape(number) + r"['\"]?\s*$", l)), None)
    if start is None:
        fail(f"{path}: cannot find the '- number: {number}' line")
    start, end = capture(lines, start)
    term_lines = [i for i in range(start, end) if re.match(r"^\s*- term:", lines[i])]
    sem_indent = indent(lines[term_lines[0]]) if term_lines else indent(lines[start]) + 4
    for i in range(start, end):
        lines[i] = re.sub(r"^(\s*current:\s*)true\s*$", r"\g<1>false", lines[i])

    course_info = yaml.safe_load(read(f"_data/{course}/course.yml")) or {}
    pad = " " * sem_indent
    entry = [
        f"{pad}- term: {yaml_scalar(label)}",
        f"{pad}  url: /{course}/{new}/",
        f"{pad}  current: true",
    ]
    for src_key, dst_key in (("instructors", "instructors"), ("GSIs", "gsis"), ("IAs", "ias")):
        people = [p.get("name") for p in (course_info.get(src_key) or []) if p.get("name")]
        if people:
            entry.append(f"{pad}  {dst_key}:")
            entry.extend(f"{pad}    - name: {yaml_scalar(p)}" for p in people)
    insert_at = end
    while insert_at > start and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines[insert_at:insert_at] = entry
    text = "\n".join(lines)
    yaml.safe_load(text)  # must still parse
    write(path, text)
    note(f"courses.yml: '{label}' added as current. Fill in the semester's topics/staff in Pages CMS > Courses > Course directory if they changed")


# --- main --------------------------------------------------------------------

def main() -> None:
    global DRY_RUN
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("course", help="course slug, e.g. designforhri or rob340")
    ap.add_argument("term", help="new term code, e.g. f26")
    ap.add_argument("--term-label", help='human label for the term, default derived from the code (f26 -> "Fall 2026")')
    ap.add_argument("--dry-run", action="store_true", help="print what would change without writing anything")
    ap.add_argument("--skip-freeze", action="store_true", help="do not freeze the old term (not recommended)")
    args = ap.parse_args()
    DRY_RUN = args.dry_run

    course, new = args.course, args.term.lower()
    if not Path(f"_data/{course}").is_dir() or not Path(f"{course}/index.html").exists():
        fail(f"course '{course}' not found (need _data/{course}/ and {course}/index.html). For a brand-new course use scripts/new-course.sh")
    label = term_label(new, args.term_label)
    if Path(f"{course}/{new}").exists():
        fail(f"{course}/{new}/ already exists; this course looks already rolled over to {new}")
    old = detect_old_term(course)
    if old == new:
        fail(f"{course}/index.html already points at {new}")

    print(f"Rolling {course} from {old} to {new} ({label}){' [dry run]' if DRY_RUN else ''}")
    print("1. Freeze old term");            freeze_old_term(course, old, args.skip_freeze)
    print("2. Create term folder");         create_term_folder(course, new)
    print("3. Reset _data");                carry_over_data(course, old, new, label)
    print("4. Redirect");                   rewrite_redirect(course, old, new)
    print("5. Pages CMS config");           rewrite_pages_cms(course, old, new)
    print("6. Course directory");           add_semester_to_directory(course, new, label)

    print("\nTo review:")
    for n in NOTES:
        print(f"  - {n}")
    print("\nNext steps:")
    print(f"  1. Seed the schedule from the planning sheet (download each tab as CSV):")
    print(f"       scripts/import-semester-sheet.py --course {course} --term {new} --schedule schedule.csv --timeline timeline.csv --speakers speakers.csv --check")
    print(f"  2. bundle exec jekyll serve   and open /{course}/{new}/ and /courses")
    print(f"  3. git add -A && git commit -m 'Start {label} for {course}' && git push")
    print(f"  4. Finish the content in Pages CMS > Courses")


if __name__ == "__main__":
    main()

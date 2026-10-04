#!/usr/bin/env python3
"""Seed a course semester's YAML from the staff planning sheet.

Reads the Google Sheet tabs as CSV files (File > Download > Comma-separated values,
one download per tab) and writes:

  _data/<course>/schedule.yml   sections "Lectures", "Discussions" (from the schedule tab)
                                and "Assignment deadlines" (from the timeline tab)
  _data/<course>/lectures.yml   one skeleton entry per held lecture (placeholder poster,
                                no video) so staff only add media and summaries later
  _data/<course>/talks.yml      confirmed invited speakers with a date
  _data/<course>/course.yml     yellow-box meeting days/times from the sheet's header lines

Everything skipped, cleaned or ambiguous is printed in a report; finish in Pages CMS.

Usage:
  scripts/import-semester-sheet.py --course designforhri --term f26 \
      --schedule schedule.csv --timeline timeline.csv --speakers speakers.csv --check

  --sheet-url URL      fetch the tabs directly (works only if the sheet is shared "anyone with the link")
  --year 2026          calendar year for the dates (default: from the term code)
  --keep-sheet-numbers keep the sheet's own L#/D# codes instead of renumbering held classes
  --lectures-include-discussions   also add discussion sessions to lectures.yml
  --force              overwrite files that already hold staff edits
  --dry-run            print the YAML and the report, write nothing
  --check              validate the written files

Sheet conventions the importer relies on:
  schedule tab:  optional header lines "Lectures: M/W 130-3", "Discussion: Tu 1130-1230";
                 a header row starting with "Date" whose session columns are named like
                 "Lecture - Mon", "Discuss - Tue", "Lab - Thu"; one row per week with a
                 date range ("Aug 31 - Sep 04") in the first column; cells like
                 "L4: Topic (P, LG)", "D3: Topic", "NO CLASS (LABOR DAY)", "CANCELLED",
                 "Guest lecture (2) Speaker Name"; staff-only lines such as "PATRICIA OOT"
                 and staff initials in parentheses are dropped. Footnotes like
                 "**Sep 21st: drop/add deadline" become deadlines.
  timeline tab:  a header row with "Action" and "Due" columns; actions starting with "*"
                 are internal and skipped.
  speakers tab:  a header row with "Name", "Institution", "Topic", "Format", "Date",
                 "Confirmed"; a speaker needs a Date and a Format to be imported.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import os
import re
import sys
import urllib.parse
import urllib.request
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

LECTURE_PLACEHOLDER = "/assets/course/placeholder-lecture.png"  # 16:9, matches the 320x180 video slot
TALK_PLACEHOLDER = "/assets/course/placeholder-talk.png"        # landscape logo shape
PLACEHOLDERS = (LECTURE_PLACEHOLDER, TALK_PLACEHOLDER, "/assets/course/lab.png")
DEADLINES_TITLE = "Assignment deadlines"
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
KIND_ALIASES = {"lecture": "lecture", "lec": "lecture", "discussion": "discussion", "discuss": "discussion", "disc": "discussion", "lab": "lab"}
KIND_LETTER = {"lecture": "L", "discussion": "D", "lab": "Lab"}
SECTION_TITLE = {"lecture": "Lectures", "discussion": "Discussions", "lab": "Labs"}
CLASS_LABEL = {"lecture": "Class", "discussion": "Discussion", "lab": "Lab"}
ABBREVIATIONS = [(re.compile(r"\bInd\b"), "Individual"), (re.compile(r"\bind\b"), "individual")]
DAY_NAMES = {
    "m": "Monday", "mo": "Monday", "mon": "Monday", "monday": "Monday",
    "t": "Tuesday", "tu": "Tuesday", "tue": "Tuesday", "tues": "Tuesday", "tuesday": "Tuesday",
    "w": "Wednesday", "we": "Wednesday", "wed": "Wednesday", "wednesday": "Wednesday",
    "th": "Thursday", "r": "Thursday", "thu": "Thursday", "thur": "Thursday", "thurs": "Thursday", "thursday": "Thursday",
    "f": "Friday", "fr": "Friday", "fri": "Friday", "friday": "Friday",
}
DEFAULT_TABS = {"schedule": "schedule", "timeline": "timeline & assignments", "speakers": "invited speakers"}

RE_WEEK = re.compile(r"^([A-Za-z]{3})[a-z]*\.?\s*(\d{1,2})\**\s*[-–]\s*(?:([A-Za-z]{3})[a-z]*\.?\s*)?(\d{1,2})")
RE_COLUMN = re.compile(r"^(lecture|lec|discussion|discuss|disc|lab)\w*\s*[-–:]\s*(mon|tue|wed|thu|fri|sat|sun)", re.I)
RE_OOT = re.compile(r"^[A-Z][A-Z' \-]*\bOO[TO]\b")
RE_INITIALS = re.compile(r"\(\s*[A-Z]{1,2}(?:\s*,\s*[A-Z]{1,2})*\s*\)")
RE_CODE = re.compile(r"^(?:([LD])\s*)?(\d{1,2})\s*[:.\-]\s*(.*)$")
RE_GUEST = re.compile(r"^guest\s+lecture\s*(?:\(\d+\))?\s*[:\-]?\s*(.*)$", re.I)
RE_FOOTNOTE_DATE = re.compile(r"^\*+\s*([A-Za-z]{3})[a-z]*\.?\s*(\d{1,2})(?:st|nd|rd|th)?\s*:\s*(.+)$")
RE_MDY = re.compile(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?")
RE_PREAMBLE = re.compile(r"^(lectures?|discussions?|labs?)\s*:\s*(.+)$", re.I)
DROPPED_NOTES: list[str] = []
STRIPPED_INITIALS: list[str] = []
RE_TIME = re.compile(r"(\d{1,2})(?::?(\d{2}))?\s*(am|pm)?\s*[-–]\s*(\d{1,2})(?::?(\d{2}))?\s*(am|pm)?", re.I)


class Report:
    ORDER = ["Ignored columns", "Skipped cells", "No-class entries", "Cleaned titles", "Class numbering",
             "Footnotes not imported", "Timeline rows skipped", "Speakers skipped", "Guest lectures vs speakers",
             "Yellow box", "Files"]

    def __init__(self) -> None:
        self.items: dict[str, list[str]] = {k: [] for k in self.ORDER}

    def add(self, section: str, msg: str) -> None:
        self.items.setdefault(section, []).append(msg)

    def print(self) -> None:
        print("\n=== Import report ===")
        for section in self.ORDER:
            items = self.items.get(section) or []
            if not items:
                continue
            print(f"\n{section}:")
            for it in items:
                print(f"  - {it}")


class Session:
    def __init__(self, date: dt.date, kind: str, title: str, held: bool = True, letter: str | None = None,
                 num: int | None = None, where: str = "") -> None:
        self.date, self.kind, self.title, self.held = date, kind, title, held
        self.letter, self.num, self.where = letter, num, where
        self.label = ""  # "Class 3", set by numbering

    @property
    def mmdd(self) -> str:
        return self.date.strftime("%m/%d")

    @property
    def code(self) -> str:
        return f"{self.letter or ''}{self.num}" if self.num is not None else ""


# --- input -------------------------------------------------------------------

def norm(cell: str) -> str:
    return cell.replace("\r", "").strip()


def read_csv(path: str) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [[norm(c) for c in row] for row in csv.reader(f)]


def fetch_tab(sheet_url: str, tab: str) -> list[list[str]]:
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", sheet_url)
    if not m:
        sys.exit(f"error: --sheet-url does not look like a Google Sheets link: {sheet_url}")
    url = f"https://docs.google.com/spreadsheets/d/{m.group(1)}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(tab)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read().decode("utf-8-sig")
            ok = resp.status == 200
    except Exception as e:  # noqa: BLE001
        ok, body = False, str(e)
    if not ok or body.lstrip().startswith("<"):
        sys.exit(
            f"error: could not read tab '{tab}' from the sheet (it is probably private).\n"
            "Share it as 'Anyone with the link can view', or download each tab with\n"
            "File > Download > Comma-separated values and pass --schedule/--timeline/--speakers."
        )
    return [[norm(c) for c in row] for row in csv.reader(io.StringIO(body))]


def cell(row: list[str], i: int | None) -> str:
    return row[i] if i is not None and i < len(row) else ""


def find_header(rows: list[list[str]], *needles: str) -> int | None:
    for i, row in enumerate(rows):
        lowered = [c.lower() for c in row]
        if all(any(n in c for c in lowered) for n in needles):
            return i
    return None


def col_index(header: list[str], *names: str) -> int | None:
    for i, c in enumerate(header):
        if any(c.lower().strip().startswith(n) for n in names):
            return i
    return None


def parse_mdy(text: str, year: int) -> dt.date | None:
    m = RE_MDY.search(text or "")
    if not m:
        return None
    mo, d, y = int(m.group(1)), int(m.group(2)), m.group(3)
    yy = year if not y else (int(y) if len(y) == 4 else 2000 + int(y))
    try:
        return dt.date(yy, mo, d)
    except ValueError:
        return None


# --- schedule tab ---------------------------------------------------------------

def clean_cell(raw: str, kind: str, where: str, report: Report) -> tuple[str, bool, str | None, int | None] | None:
    """-> (title, held, code_letter, code_num) or None when nothing should be listed."""
    kept = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if RE_OOT.match(line):
            DROPPED_NOTES.append(line)
            continue
        kept.append(line)
    text = re.sub(r"\s+", " ", " ".join(kept)).strip()
    if not text:
        report.add("Skipped cells", f"{where}: empty")
        return None
    if re.match(r"^cancell?ed\b", text, re.I):
        report.add("Skipped cells", f"{where}: cancelled")
        return None
    m = re.match(r"^no\s+class(?:es)?\s*(?:\(([^)]*)\))?\s*(.*)$", text, re.I)
    if m:
        reason, extra = (m.group(1) or "").strip(), (m.group(2) or "").strip()
        title = "No class" + (f": {reason.title()}" if reason else "")
        report.add("No-class entries", f"{where}: {title}" + (f"  (extra text not imported: '{extra}')" if extra else ""))
        return title, False, None, None

    STRIPPED_INITIALS.extend(RE_INITIALS.findall(text))
    text = re.sub(r"\s+", " ", RE_INITIALS.sub("", text)).strip()

    letter, num = None, None
    m = RE_CODE.match(text)
    if m:
        letter, num, text = m.group(1), int(m.group(2)), m.group(3).strip()
        if letter is None:
            letter = KIND_LETTER[kind]
            report.add("Cleaned titles", f"{where}: code '{num}:' has no L/D letter, assumed {letter}{num}")
    else:
        report.add("Cleaned titles", f"{where}: no L#/D# code in '{text}'")

    g = RE_GUEST.match(text)
    if g:
        name = g.group(1).strip(" -:")
        text = f"Guest Lecture: {name}" if name else "Guest Lecture"
        if not name:
            report.add("Cleaned titles", f"{where}: guest lecture without a speaker name")

    text = re.sub(r"[\s&:,\-–]+$", "", text).strip()
    for pat, repl in ABBREVIATIONS:
        text = pat.sub(repl, text)
    if not text:
        text = "TBD"
        report.add("Cleaned titles", f"{where}: empty title -> TBD")
    elif text[0].islower():
        text = text[0].upper() + text[1:]
    if re.search(r"potentially|tentative|\btbd\b|\btbc\b|\?", text, re.I):
        report.add("Cleaned titles", f"{where}: tentative — '{text}'")
    return text, True, letter, num


def parse_schedule(rows: list[list[str]], year: int, report: Report):
    header_i = next((i for i, r in enumerate(rows) if r and r[0].lower().startswith("date")), None)
    if header_i is None:
        sys.exit("error: schedule tab has no header row starting with 'Date'")
    preamble = [r[0] for r in rows[:header_i] if r and r[0]]
    header = rows[header_i]

    columns: list[tuple[int, str, int]] = []  # (col, kind, weekday)
    for i, name in enumerate(header):
        m = RE_COLUMN.match(name)
        if m:
            columns.append((i, KIND_ALIASES[m.group(1).lower()], WEEKDAYS[m.group(2).lower()]))
        elif name:
            report.add("Ignored columns", f"'{name}'")
    if not columns:
        sys.exit(f"error: no session columns found in header {header!r} (expected names like 'Lecture - Mon')")

    sessions: list[Session] = []
    footnotes: list[str] = []
    non_monday = False
    for row in rows[header_i + 1:]:
        if not row or not any(row):
            continue
        m = RE_WEEK.match(row[0])
        if not m:
            footnotes.append(" | ".join(c for c in row if c))
            continue
        mon = MONTHS.get(m.group(1).lower())
        if mon is None:
            report.add("Skipped cells", f"week '{row[0]}': unknown month")
            continue
        start = dt.date(year, mon, int(m.group(2)))
        if start.weekday() != 0:
            non_monday = True
        week = cell(row, 1) or row[0]
        for col, kind, weekday in columns:
            date = start + dt.timedelta(days=(weekday - start.weekday()) % 7)
            where = f"{week.strip()} / {header[col].strip()} ({date.strftime('%m/%d')})"
            cleaned = clean_cell(cell(row, col), kind, where, report)
            if cleaned is None:
                continue
            title, held, letter, num = cleaned
            sessions.append(Session(date, kind, title, held, letter, num, where))
    if DROPPED_NOTES:
        report.add("Skipped cells", f"dropped {len(DROPPED_NOTES)} staff-only note(s): " + ", ".join(sorted(set(DROPPED_NOTES))))
    if STRIPPED_INITIALS:
        report.add("Cleaned titles", f"removed staff initials from {len(STRIPPED_INITIALS)} cell(s): " + ", ".join(sorted(set(STRIPPED_INITIALS))))
    if non_monday:
        report.add("Cleaned titles", "some week ranges do not start on a Monday; dates were computed from the actual start weekday")
    sessions.sort(key=lambda s: s.date)  # stable: keeps column order within a day
    kinds_in_order = []
    for _, kind, _ in columns:
        if kind not in kinds_in_order:
            kinds_in_order.append(kind)
    return preamble, sessions, footnotes, kinds_in_order


def number_sessions(sessions: list[Session], keep_sheet_numbers: bool, report: Report) -> None:
    for kind in SECTION_TITLE:
        n = 0
        mapping = []
        for s in (x for x in sessions if x.kind == kind):
            if not s.held:
                continue
            n += 1
            s.label = s.code if (keep_sheet_numbers and s.code) else f"{CLASS_LABEL[kind]} {n}"
            if s.code and not keep_sheet_numbers and s.code != f"{KIND_LETTER[kind]}{n}":
                mapping.append(f"{s.code}→{s.label} ({s.mmdd})")
        if mapping:
            report.add("Class numbering", f"{SECTION_TITLE[kind]} renumbered by held sessions (sheet code→site): " + ", ".join(mapping))


def parse_footnotes(footnotes: list[str], year: int, report: Report) -> list[tuple[dt.date, str]]:
    deadlines = []
    for note in footnotes:
        m = RE_FOOTNOTE_DATE.match(note)
        if m and m.group(1).lower() in MONTHS:
            date = dt.date(year, MONTHS[m.group(1).lower()], int(m.group(2)))
            text = m.group(3).strip()
            deadlines.append((date, text[0].upper() + text[1:]))
        else:
            report.add("Footnotes not imported", note)
    return deadlines


# --- timeline tab ---------------------------------------------------------------

def parse_timeline(rows: list[list[str]], year: int, report: Report) -> list[tuple[dt.date, str]]:
    h = find_header(rows, "due", "action")
    if h is None:
        sys.exit("error: timeline tab has no header row with 'Action' and 'Due' columns")
    header = rows[h]
    i_grade, i_action, i_due = col_index(header, "grade type", "grade"), col_index(header, "action"), col_index(header, "due")
    out = []
    internal = 0
    seen = set()
    for row in rows[h + 1:]:
        action = cell(row, i_action)
        if not action:
            continue
        if action.startswith("*"):
            internal += 1
            continue
        date = parse_mdy(cell(row, i_due), year)
        if date is None:
            report.add("Timeline rows skipped", f"'{action}': no due date ('{cell(row, i_due)}')")
            continue
        text = re.sub(r"^students?\s*:\s*", "", action, flags=re.I).strip()
        text = re.sub(r"\s+", " ", text)
        grade = cell(row, i_grade).strip()
        if grade and not all(w in text.lower() for w in grade.lower().split()):
            text = f"{text} ({grade})"
        key = (date, text.lower())
        if key in seen:
            report.add("Timeline rows skipped", f"{date.strftime('%m/%d')} '{text}': duplicate of an earlier row")
            continue
        seen.add(key)
        out.append((date, text[0].upper() + text[1:]))
    if internal:
        report.add("Timeline rows skipped", f"{internal} internal team task(s) marked with '*' (not shown to students)")
    return out


# --- speakers tab ---------------------------------------------------------------

def parse_speakers(rows: list[list[str]], year: int, staff_first_names: set[str], report: Report) -> list[dict]:
    h = find_header(rows, "name", "institution")
    if h is None:
        sys.exit("error: speakers tab has no header row with 'Name' and 'Institution' columns")
    header = rows[h]
    idx = {k: col_index(header, k) for k in ("name", "institution", "topic", "format", "date", "confirmed")}
    speakers = []
    for row in rows[h + 1:]:
        name = re.sub(r"\s+", " ", cell(row, idx["name"])).strip()
        if not name:
            continue
        fmt, confirmed = cell(row, idx["format"]), cell(row, idx["confirmed"])
        date = parse_mdy(cell(row, idx["date"]), year)
        first = name.split()[0].lower()
        if first in staff_first_names:
            report.add("Speakers skipped", f"{name}: course staff")
            continue
        if confirmed.lower().startswith("n"):
            report.add("Speakers skipped", f"{name}: not confirmed")
            continue
        if date is None:
            report.add("Speakers skipped", f"{name}: no date")
            continue
        if not fmt:
            report.add("Speakers skipped", f"{name}: no format (in person / virtual) — not scheduled yet?")
            continue
        if len(name.split()) == 1:
            report.add("Speakers skipped", f"{name}: imported, but needs a full name")
        speakers.append({
            "name": name,
            "title": re.sub(r"\s+", " ", cell(row, idx["topic"])).strip(),
            "institution": re.sub(r"\s+", " ", cell(row, idx["institution"])).strip(),
            "link": "",
            "image": TALK_PLACEHOLDER,
            "_date": date,
        })
    speakers.sort(key=lambda s: s["_date"])
    return speakers


def cross_check_guests(sessions: list[Session], speakers: list[dict], report: Report) -> None:
    by_date: dict[dt.date, list[dict]] = {}
    for s in speakers:
        by_date.setdefault(s["_date"], []).append(s)
    matched = set()
    for s in sessions:
        if not s.held or not s.title.lower().startswith("guest lecture"):
            continue
        name = s.title.split(":", 1)[1].strip() if ":" in s.title else ""
        candidates = by_date.get(s.date, [])
        if not candidates:
            report.add("Guest lectures vs speakers", f"{s.mmdd} '{s.title}': no speaker with this date in the speakers tab — add to talks.yml by hand")
            continue
        best = candidates[0]
        if name:
            for c in candidates:
                if c["name"].lower() == name.lower():
                    best = c
                    break
            else:
                if len(candidates) == 1:
                    report.add("Guest lectures vs speakers", f"{s.mmdd}: schedule says '{name}', speakers tab says '{best['name']}' — using the speakers tab spelling")
        s.title = f"Guest Lecture: {best['name']}"
        matched.add(id(best))
    for sp in speakers:
        if id(sp) not in matched:
            report.add("Guest lectures vs speakers", f"{sp['_date'].strftime('%m/%d')} {sp['name']}: no 'Guest lecture' session on this date in the schedule tab")


# --- course.yml yellow box -------------------------------------------------------

def parse_meeting_line(value: str) -> tuple[str, str] | None:
    m = RE_TIME.search(value)
    if not m:
        return None
    days_part = value[:m.start()]
    tokens = [t for t in re.split(r"[/,&+\s]+", days_part.lower()) if t]
    if not tokens or any(t not in DAY_NAMES for t in tokens):
        return None
    days = " & ".join(dict.fromkeys(DAY_NAMES[t] for t in tokens))

    def clock(h: str, mi: str | None, mer: str | None) -> tuple[int, int, str]:
        hh, mm = int(h), int(mi or 0)
        if not (1 <= hh <= 12 and 0 <= mm < 60):
            raise ValueError
        meridiem = mer.upper() if mer else ("AM" if 8 <= hh <= 11 else "PM")
        return hh, mm, meridiem

    try:
        h1, m1, a1 = clock(m.group(1), m.group(2), m.group(3))
        h2, m2, a2 = clock(m.group(4), m.group(5), m.group(6))
    except ValueError:
        return None
    if a1 == a2:
        time = f"{h1}:{m1:02d} - {h2}:{m2:02d} {a2}"
    else:
        time = f"{h1}:{m1:02d} {a1} - {h2}:{m2:02d} {a2}"
    return days, time


def update_yellow_box(course: str, preamble: list[str], report: Report, dry_run: bool) -> bool:
    path = f"_data/{course}/course.yml"
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    yb = data.setdefault("yellow_box", {})
    sections = yb.setdefault("sections", [])
    changed = False
    for line in preamble:
        m = RE_PREAMBLE.match(line)
        if not m:
            continue
        kind = m.group(1).lower().rstrip("s")
        parsed = parse_meeting_line(m.group(2))
        if not parsed:
            report.add("Yellow box", f"could not parse '{line}'; set the {kind} days/time in Pages CMS")
            continue
        days, time = parsed
        target = next((s for s in sections if str(s.get("title", "")).lower().startswith(kind)), None)
        if target is None:
            target = {"title": SECTION_TITLE[kind], "date": "", "time": "", "location": "TBD"}
            # keep meeting sections together: insert after the last lecture/discussion/lab section
            after = [i for i, s in enumerate(sections) if str(s.get("title", "")).lower().startswith(tuple(SECTION_TITLE))]
            sections.insert(after[-1] + 1 if after else 0, target)
            report.add("Yellow box", f"added section '{SECTION_TITLE[kind]}' with location TBD")
        target["date"], target["time"] = days, time
        report.add("Yellow box", f"{target['title']}: {days}, {time}  (from '{line}')")
        changed = True
    if changed and not dry_run:
        Path(path).write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10000), encoding="utf-8")
        report.add("Files", path)
    return changed


# --- output --------------------------------------------------------------------

def schedule_class(s: Session) -> str:
    title = s.title
    m = re.match(r"^Guest Lecture:\s*(.+)$", title)
    if m:
        title = f"Guest Lecture ({m.group(1)})"
    return f"{s.label}: {title}" if s.label else title


def dump(data) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10000, default_flow_style=False)


def write_output(path: str, text: str, force: bool, dry_run: bool, report: Report) -> None:
    existing = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    if existing.strip() not in ("", "[]") and existing != text and not force:
        has_media = "video_src" in existing or ("image:" in existing and not any(p in existing for p in PLACEHOLDERS))
        sys.exit(
            f"error: {path} already has content that differs from this import"
            + (" (including real media)" if has_media else "")
            + ". Re-run with --force to overwrite it, or edit it in Pages CMS instead."
        )
    if dry_run:
        print(f"\n--- {path} (dry run) ---\n{text}")
        return
    Path(path).write_text(text, encoding="utf-8")
    report.add("Files", path)


def check_outputs(course: str, report: Report) -> int:
    problems = 0
    base = f"_data/{course}"
    sched = yaml.safe_load(Path(f"{base}/schedule.yml").read_text()) or []
    for sec in sched:
        last = ""
        for s in sec.get("sessions") or []:
            if not re.fullmatch(r"\d{2}/\d{2}", str(s.get("date", ""))) or not s.get("class"):
                print(f"  CHECK: bad session in '{sec.get('title')}': {s}"); problems += 1
            if str(s.get("date")) < last:
                print(f"  CHECK: '{sec.get('title')}' dates not in order at {s.get('date')}"); problems += 1
            last = str(s.get("date"))
    for lec in yaml.safe_load(Path(f"{base}/lectures.yml").read_text()) or []:
        if not lec.get("title") or not lec.get("video_poster"):
            print(f"  CHECK: lecture missing title/poster: {lec}"); problems += 1
    for talk in yaml.safe_load(Path(f"{base}/talks.yml").read_text()) or []:
        if not talk.get("name"):
            print(f"  CHECK: talk without name: {talk}"); problems += 1
    for name in ("schedule.yml", "lectures.yml", "talks.yml"):
        text = Path(f"{base}/{name}").read_text()
        for pat in (r"\bOOT\b", RE_INITIALS.pattern, r"\*\*"):
            if re.search(pat, text):
                print(f"  CHECK: {name} still contains /{pat}/"); problems += 1
    print(f"  check: {'OK' if not problems else str(problems) + ' problem(s)'}")
    return problems


# --- main ----------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--course", required=True)
    ap.add_argument("--term", required=True, help="current term code, e.g. f26")
    ap.add_argument("--schedule", help="CSV of the schedule tab")
    ap.add_argument("--timeline", help="CSV of the timeline & assignments tab")
    ap.add_argument("--speakers", help="CSV of the invited speakers tab")
    ap.add_argument("--sheet-url", help="Google Sheet URL (must be shared with anyone-with-the-link)")
    for key, tab in DEFAULT_TABS.items():
        ap.add_argument(f"--tab-{key}", default=tab, help=f"tab name for --sheet-url (default '{tab}')")
    ap.add_argument("--year", type=int, help="calendar year of the dates (default from the term code)")
    ap.add_argument("--keep-sheet-numbers", action="store_true")
    ap.add_argument("--lectures-include-discussions", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    course, term = args.course, args.term.lower()
    data_dir = f"_data/{course}"
    stub = f"{course}/{term}/index.html"
    if not Path(data_dir).is_dir():
        sys.exit(f"error: {data_dir}/ not found")
    if not Path(stub).exists() or not Path(stub).read_text(encoding="utf-8").startswith("---"):
        sys.exit(f"error: {stub} is not the live semester stub. Run scripts/new-semester.py {course} {term} first.")
    redirect = Path(f"{course}/index.html").read_text(encoding="utf-8")
    if f"./{term}/" not in redirect:
        sys.exit(f"error: {course}/index.html does not point at ./{term}/ — is {term} the current term?")
    m = re.fullmatch(r"[a-z]{1,2}(\d{2})", term)
    year = args.year or (2000 + int(m.group(1)) if m else None)
    if year is None:
        sys.exit("error: cannot infer the year from the term code; pass --year")

    def load(key: str) -> list[list[str]] | None:
        path = getattr(args, key)
        if path:
            return read_csv(path)
        if args.sheet_url:
            return fetch_tab(args.sheet_url, getattr(args, f"tab_{key}"))
        return None

    schedule_rows = load("schedule")
    if schedule_rows is None:
        sys.exit("error: --schedule CSV (or --sheet-url) is required")
    timeline_rows = load("timeline")
    speaker_rows = load("speakers")

    report = Report()
    course_info = yaml.safe_load(Path(f"{data_dir}/course.yml").read_text(encoding="utf-8")) or {}
    staff_first = {str(p.get("name", "")).split()[0].lower() for k in ("instructors", "GSIs", "IAs")
                   for p in (course_info.get(k) or []) if p.get("name")}

    preamble, sessions, footnotes, kinds = parse_schedule(schedule_rows, year, report)
    deadlines = parse_footnotes(footnotes, year, report)
    if timeline_rows is not None:
        deadlines += parse_timeline(timeline_rows, year, report)
    speakers = parse_speakers(speaker_rows, year, staff_first, report) if speaker_rows is not None else []
    if speakers:
        cross_check_guests(sessions, speakers, report)
    number_sessions(sessions, args.keep_sheet_numbers, report)

    # schedule.yml
    schedule_yaml = []
    for kind in kinds:
        items = [s for s in sessions if s.kind == kind]
        if not items:
            continue
        schedule_yaml.append({
            "title": SECTION_TITLE[kind],
            "sessions": [{"date": s.mmdd, "class": schedule_class(s)} for s in items],
        })
    if deadlines:
        deadlines.sort(key=lambda d: d[0])
        schedule_yaml.append({
            "title": DEADLINES_TITLE,
            "sessions": [{"date": d.strftime("%m/%d"), "class": text} for d, text in deadlines],
        })

    # lectures.yml
    lecture_kinds = {"lecture"} | ({"discussion"} if args.lectures_include_discussions else set())
    lectures_yaml = []
    for s in sessions:
        if not s.held or s.kind not in lecture_kinds:
            continue
        if s.title.lower().startswith("guest lecture"):
            title = s.title
        else:
            title = f"{'Lecture' if s.kind == 'lecture' else CLASS_LABEL[s.kind]}: {s.title}"
        lectures_yaml.append({"video_poster": LECTURE_PLACEHOLDER, "title": title, "description": ""})

    talks_yaml = [{k: v for k, v in sp.items() if not k.startswith("_")} for sp in speakers]

    print(f"Importing {course} {term} ({year}): {sum(s.held for s in sessions)} held sessions, "
          f"{len(deadlines)} deadlines, {len(lectures_yaml)} lecture skeletons, {len(talks_yaml)} speakers"
          f"{' [dry run]' if args.dry_run else ''}")
    write_output(f"{data_dir}/schedule.yml", dump(schedule_yaml), args.force, args.dry_run, report)
    write_output(f"{data_dir}/lectures.yml", dump(lectures_yaml), args.force, args.dry_run, report)
    if speaker_rows is not None:
        write_output(f"{data_dir}/talks.yml", dump(talks_yaml), args.force, args.dry_run, report)
    update_yellow_box(course, preamble, report, args.dry_run)

    report.print()
    if args.check and not args.dry_run:
        print("\nChecking written files:")
        if check_outputs(course, report):
            sys.exit(1)
    print("\nNext: review the report above, then finish in Pages CMS (students, grading, placeholder images, speaker links/logos).")


if __name__ == "__main__":
    main()

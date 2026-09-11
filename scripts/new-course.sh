#!/bin/bash
# Scaffold a completely new course site.
#
# Creates the data files, term folder, redirect, and Pages CMS config for a
# course that has never been taught before. After running, commit + push, then
# fill in the content via Pages CMS (Courses > <COURSE> group) and add the
# course to Courses > Course directory.
#
# Usage: scripts/new-course.sh <course-slug> <term> "<Course Title>"
#   e.g. scripts/new-course.sh rob204 f26 "Introduction to Human-Robot Systems"
set -euo pipefail

slug="${1:-}"
term="${2:-}"
title="${3:-}"
if [ -z "$slug" ] || [ -z "$term" ] || [ -z "$title" ]; then
  echo 'Usage: scripts/new-course.sh <course-slug> <term> "<Course Title>"' >&2
  echo '  e.g. scripts/new-course.sh rob204 f26 "Introduction to Human-Robot Systems"' >&2
  exit 1
fi
if [ -d "_data/$slug" ] || [ -d "$slug" ]; then
  echo "Course '$slug' already exists (_data/$slug or $slug/)." >&2
  exit 1
fi

# "rob204" -> "ROB 204"
prefix="$(echo "${slug//[0-9]/}" | tr '[:lower:]' '[:upper:]')"
digits="${slug//[a-z]/}"
number="$prefix $digits"

echo "Scaffolding $number: $title ($term)..."

# --- Term folder: shared css/js, empty asset dirs, page stub, redirect -------
mkdir -p "$slug/$term/img/labs" "$slug/$term/img/gps" "$slug/$term/img/talk_logos" "$slug/$term/snippets"
cp -R rob340/w25/css rob340/w25/js "$slug/$term/"
cp rob340/w25/lab.png "$slug/$term/lab.png"

cat > "$slug/$term/index.html" <<EOF
---
layout: course
course: $slug
---
EOF

cat > "$slug/index.html" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=./$term/" />
  <link rel="canonical" href="./$term/" />
  <title>$number</title>
</head>
<body>
  <p>Redirecting to the current semester: <a href="./$term/">$number</a></p>
</body>
</html>
EOF

# --- Skeleton data files (fill in via Pages CMS) -----------------------------
mkdir -p "_data/$slug"

cat > "_data/$slug/course.yml" <<EOF
title: '$number: $title'
instructors:
  - name: Patricia Alves-Oliveira
    url: https://patricialvesoliveira.com/
GSIs: []
IAs: []
department: Robotics Department
university: University of Michigan Ann Arbor
office: TBD
yellow_box:
  top-text: This course is running in TBD
  sections:
    - title: Lectures
      date: TBD
      time: TBD
      location: TBD
EOF

cat > "_data/$slug/head.yml" <<EOF
title: "$number | UMich"
description: "$number: $title at the University of Michigan."
image: "/$slug/$term/img/class-logo.png"
icon: "/$slug/$term/img/class-logo.png"
EOF

cat > "_data/$slug/main.yml" <<EOF
- name: Course Description
  content: |
    TBD
EOF

cp _data/rob340/social-links.yml "_data/$slug/social-links.yml"
echo "[]" > "_data/$slug/schedule.yml"
echo "[]" > "_data/$slug/grading.yml"
echo "[]" > "_data/$slug/lectures.yml"
echo "[]" > "_data/$slug/labs.yml"
echo "[]" > "_data/$slug/talks.yml"
echo "[]" > "_data/$slug/group_projects.yml"
printf "undergraduates: []\ngraduates: []\n" > "_data/$slug/students.yml"

# --- Pages CMS config: clone the rob340 media entry + content group ----------
python3 - "$slug" "$term" "$number" <<'PYEOF'
import re, sys

slug, term, number = sys.argv[1], sys.argv[2], sys.argv[3]
path = ".pages.yml"
lines = open(path).read().split("\n")

def indent(s): return len(s) - len(s.lstrip(" "))

def capture(start):
    """start line + all following lines with deeper indent."""
    base = indent(lines[start])
    end = start + 1
    while end < len(lines):
        l = lines[end]
        if l.strip() and indent(l) <= base:
            break
        end += 1
    return start, end

def substitute(block):
    block = [l.replace("rob340/w25", f"{slug}/{term}") for l in block]
    block = [l.replace("rob340", slug) for l in block]
    block = [l.replace("ROB 340", number) for l in block]
    return block

# media entry
m_start = next(i for i, l in enumerate(lines) if l.startswith("  - name: rob340"))
m_start, m_end = capture(m_start)
media_block = substitute(lines[m_start:m_end])

# content group
c_start = next(i for i, l in enumerate(lines) if l.strip() == "- name: rob340-current" and indent(l) == 6)
c_start, c_end = capture(c_start)
content_block = substitute(lines[c_start:c_end])

# insert media entry after the rob340 one, content group after rob340-current
out = lines[:m_end] + media_block + lines[m_end:c_end] + content_block + lines[c_end:]
open(path, "w").write("\n".join(out))
print(f"Added '{slug}' media entry and '{slug}-current' CMS group to .pages.yml")
PYEOF

echo ""
echo "Done. Next steps:"
echo "  1. Add a course logo:  $slug/$term/img/class-logo.png"
echo "  2. Commit and push:    git add -A && git commit -m 'Add $number' && git push"
echo "  3. In Pages CMS, fill in the content under Courses > $number (current semester)"
echo "  4. In Pages CMS, add the course under Courses > Course directory"

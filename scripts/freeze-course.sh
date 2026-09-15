#!/bin/bash
# Freeze a finished course semester into permanent static HTML.
# Replaces the semester's Jekyll stub with the fully rendered page, so it is
# copied verbatim on every future build and no longer depends on _data/<course>/.
#
# Usage: scripts/freeze-course.sh <course> <term>
#   e.g. scripts/freeze-course.sh rob340 w25
set -euo pipefail

course="${1:-}"
term="${2:-}"
if [ -z "$course" ] || [ -z "$term" ]; then
  echo "Usage: scripts/freeze-course.sh <course> <term>   e.g. scripts/freeze-course.sh rob340 w25" >&2
  exit 1
fi
if [ ! -f "$course/$term/index.html" ]; then
  echo "No such semester page: $course/$term/index.html" >&2
  exit 1
fi
if ! head -1 "$course/$term/index.html" | grep -q '^---$'; then
  echo "$course/$term/index.html has no front matter — it looks already frozen." >&2
  exit 1
fi

bundle exec jekyll build
cp "_site/$course/$term/index.html" "$course/$term/index.html"
echo "Frozen $course/$term — the page is now static. Commit the change."

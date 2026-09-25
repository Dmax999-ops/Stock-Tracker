#!/usr/bin/env bash
# Commit this job's own output files and push them -- reliably, even when other
# workflows have pushed in the meantime.
#
#   usage: bash scripts/commit_push.sh "commit message" path [path ...]
#
# Why: several jobs write to the repo on overlapping schedules. The old commit
# step did "rebase, and if that fails, give up", so one clash with another
# job's push failed the whole run (ETF rotation, 24 Sep). Each job only ever
# owns ITS OWN files, so there is no real conflict to resolve: this takes the
# latest main, puts this job's files on top, and pushes. Up to 8 tries.
set -u
msg="$1"; shift
git config user.name  "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

keep=()
for f in "$@"; do [ -e "$f" ] && keep+=("$f"); done
if [ ${#keep[@]} -eq 0 ]; then echo "no output files to commit"; exit 0; fi
stash=$(mktemp -d)
tar -cf "$stash/out.tar" "${keep[@]}"

for i in 1 2 3 4 5 6 7 8; do
  git fetch -q origin main || { sleep 5; continue; }
  git reset -q --hard origin/main
  tar -xf "$stash/out.tar"
  git add -- "${keep[@]}"
  if git diff --staged --quiet; then echo "no changes to commit"; exit 0; fi
  git commit -q -m "$msg"
  if git push -q origin HEAD:main; then echo "pushed on attempt $i"; exit 0; fi
  echo "push rejected (another job pushed first), retrying ($i/8)"
  sleep $(( 5 * i + RANDOM % 10 ))
done
echo "could not push after 8 attempts"; exit 1

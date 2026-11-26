#!/bin/sh
# Maintainers: point `stable` back at a known-good release tag (history and tags are never rewritten).
#   sh scripts/rollback.sh v0.2.0
set -eu
T="${1:?usage: rollback.sh <tag, e.g. v0.2.0>}"
git rev-parse -q --verify "refs/tags/$T" >/dev/null || { echo "no such tag: $T"; exit 1; }
git branch -f stable "$T"
git push --force-with-lease origin stable
echo "stable now points at $T. Next: fix forward on main and release a new patch, or revert the bad commits with git revert."

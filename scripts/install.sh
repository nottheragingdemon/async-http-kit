#!/bin/sh
# Install asynchttp with a fallback chain: newest release first, then older ones, until one installs and passes the smoke test.
#   sh scripts/install.sh              # newest tag, falling back through every older tag
#   sh scripts/install.sh v0.3.0 v0.2.0 # your own order
set -u
REPO="https://github.com/nottheragingdemon/async-http-kit"
if [ $# -gt 0 ]; then TAGS="$*"; else
  TAGS=$(git ls-remote --tags --refs "$REPO" 'v*' | sed 's#.*refs/tags/##' | sort -V -r)
fi
[ -n "$TAGS" ] || { echo "no release tags found"; exit 1; }
for T in $TAGS; do
  echo "trying $T ..."
  if pip install -q --force-reinstall "git+$REPO@$T" && python -c "import asynchttp, sys; print('asynchttp', asynchttp.__version__, 'OK')"; then
    echo "installed $T"; exit 0
  fi
  echo "$T failed, falling back"
done
echo "no version could be installed"; exit 1

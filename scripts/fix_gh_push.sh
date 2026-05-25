#!/usr/bin/env bash
# Strip blobs > 100MB from history so `git push` works on GitHub.
# DESTRUCTIVE: rewrites all commit hashes. Back up first.
#
# Usage:
#   bash scripts/fix_gh_push.sh
#
# After running:
#   git remote add origin <url>   # filter-repo removes the remote
#   git push -u origin main --force

set -euo pipefail

REPO_DIR="$(git rev-parse --show-toplevel)"
cd "$REPO_DIR"

echo "Current repo: $REPO_DIR"
echo "Current branch: $(git branch --show-current)"
echo "Current HEAD: $(git rev-parse HEAD)"
echo

# Show what would be removed
echo "Blobs > 100MB in current history:"
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectsize) %(objectname) %(rest)' \
  | awk '$1=="blob" && $2 > 100000000 {print $2, $4}' \
  | sort -n
echo

read -p "Proceed with destructive rewrite? [y/N] " ans
if [[ ! "$ans" =~ ^[Yy]$ ]]; then
  echo "Aborted."; exit 1
fi

# Back up remote URL since filter-repo strips it
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

# Strip files > 100MB
git filter-repo --force --strip-blobs-bigger-than 100M

# Restore remote
if [[ -n "$REMOTE_URL" ]]; then
  echo "Re-adding remote: $REMOTE_URL"
  git remote add origin "$REMOTE_URL"
fi

echo
echo "Done. New HEAD: $(git rev-parse HEAD)"
echo "To push: git push -u origin main --force"

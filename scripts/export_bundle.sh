#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mkdir -p dist
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="dist/fs42stream-scaffold-${stamp}.tar.gz"

tar \
  --exclude='./.git' \
  --exclude='./dist' \
  --exclude='./.pytest_cache' \
  --exclude='__pycache__' \
  -czf "$archive" \
  README.md HANDOFF.md LICENSE pyproject.toml config docs scripts src tests

printf '%s\n' "$archive"

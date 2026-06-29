#!/bin/sh
# install.sh — install / update the Agent Skills library (no git clone needed).
#
# Downloads this library and installs ONLY the skills it provides (top-level
# directories that contain a SKILL.md) into your agent skills directory. Each of
# THOSE skills is clean-replaced; any other skill you already have is left fully
# untouched — nothing else is deleted or overwritten.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/duysqubix/skills/main/install.sh | sh
#
# Env overrides:
#   AGENTS_SKILLS_DIR   target dir (default: ~/.agents/skills)
#   SKILLS_REPO         source repo (default: duysqubix/skills)
#   SKILLS_BRANCH       branch      (default: main)
set -eu

REPO="${SKILLS_REPO:-duysqubix/skills}"
BRANCH="${SKILLS_BRANCH:-main}"
DEST="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
TARBALL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"

say() { printf '%s\n' "$*"; }
die() { printf 'install: error: %s\n' "$*" >&2; exit 1; }

command -v tar >/dev/null 2>&1 || die "tar is required"
if   command -v curl >/dev/null 2>&1; then DL="curl -fsSL"
elif command -v wget >/dev/null 2>&1; then DL="wget -qO-"
else die "curl or wget is required"
fi

TMP="$(mktemp -d)" || die "could not create a temp dir"
trap 'rm -rf "$TMP"' EXIT INT TERM HUP

say "Downloading ${REPO}@${BRANCH} ..."
# shellcheck disable=SC2086
$DL "$TARBALL" | tar -xz -C "$TMP" \
  || die "could not download/extract ${TARBALL} (is ${REPO} public?)"

# GitHub extracts the repo into a single <repo>-<branch>/ directory.
SRC=""
for d in "$TMP"/*/; do
  [ -d "$d" ] || continue
  SRC="${d%/}"
  break
done
[ -n "$SRC" ] || die "could not locate the extracted repository in ${TMP}"

mkdir -p "$DEST" || die "could not create ${DEST}"

installed=0
for skill in "$SRC"/*/; do
  [ -f "${skill}SKILL.md" ] || continue           # only real skills (must have a SKILL.md)
  name="$(basename "$skill")"
  case "$name" in ""|.|..|.*) continue ;; esac     # never touch dotfiles / .git etc.
  rm -rf "${DEST:?}/${name}"                        # clean-replace ONLY this repo's skill
  cp -R "${SRC}/${name}" "${DEST}/${name}"
  installed=$((installed + 1))
  say "  + ${name}"
done

[ "$installed" -gt 0 ] || die "no skills (SKILL.md directories) found in ${REPO}@${BRANCH}"

say ""
say "Installed/updated ${installed} skill(s) into ${DEST}"
say "Your other skills in ${DEST} were left untouched."
say "Start a new agent session to pick them up."

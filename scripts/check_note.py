#!/usr/bin/env python3
"""Check that an Obsidian note's local links and embedded files exist."""

import argparse
import re
from pathlib import Path
from urllib.parse import unquote


WIKI_LINK = re.compile(r"\[\[([^\]]+)\]\]")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def visible_lines(content):
    fence_marker = None
    for number, line in enumerate(content.splitlines(), start=1):
        marker = FENCE.match(line)
        if marker:
            current = marker.group(1)
            if fence_marker is None:
                fence_marker = current
            elif current[0] == fence_marker[0] and len(current) >= len(fence_marker):
                fence_marker = None
            continue
        if fence_marker is None:
            yield number, line


def is_external(target):
    return bool(re.match(r"^[a-z][a-z0-9+.-]*://", target, re.I)) or target.startswith("mailto:")


def check_note(note, vault):
    files = [path for path in vault.rglob("*") if path.is_file() and ".obsidian" not in path.parts]
    names = {path.name for path in files}
    note_stems = {path.stem for path in files if path.suffix.lower() == ".md"}
    problems = []

    for number, line in visible_lines(note.read_text(encoding="utf-8")):
        for match in WIKI_LINK.finditer(line):
            target = unquote(match.group(1).split("|", 1)[0].split("#", 1)[0]).strip()
            if not target:
                continue
            path = Path(target)
            if path.is_absolute() or ".." in path.parts:
                problems.append(f"{number}: invalid wiki link path: {target}")
            elif "/" in target:
                candidates = (vault / path, note.parent / path)
                if not any(
                    candidate.is_file() or (not path.suffix and candidate.with_suffix(".md").is_file())
                    for candidate in candidates
                ):
                    problems.append(f"{number}: unresolved wiki link: {target}")
            elif target not in names and target not in note_stems:
                problems.append(f"{number}: unresolved wiki link: {target}")

        for match in MARKDOWN_LINK.finditer(line):
            target = unquote(match.group(1).strip().strip("<> ").split("#", 1)[0])
            if not target or is_external(target):
                continue
            path = Path(target)
            if not path.is_absolute():
                path = note.parent / path
            if not path.is_file():
                problems.append(f"{number}: missing local file: {target}")

    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", type=Path, help="Markdown note to inspect")
    parser.add_argument("--vault", type=Path, help="Obsidian vault root; defaults to the note's folder")
    args = parser.parse_args()
    note = args.note.resolve()
    vault = (args.vault or note.parent).resolve()
    if not note.is_file() or not vault.is_dir():
        parser.error("note and vault must exist")

    problems = check_note(note, vault)
    for problem in problems:
        print(problem)
    if problems:
        print(f"Found {len(problems)} unresolved local link(s).")
        return 1
    print("All local links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

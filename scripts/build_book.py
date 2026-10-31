#!/usr/bin/env python3
"""Generate mdBook Markdown sources from the top-level org files."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CLOSING_HASHES_RE = re.compile(r"\s+#+\s*$")
LOCAL_ORG_LINK_RE = re.compile(r"\]\((?:file:)?(?:\./)?([^)/:#]+)\.org(#[^)]*)?\)")


def natural_key(path: Path) -> tuple[tuple[int, object], ...]:
    """Sort names by embedded numbers, so chapter2 precedes chapter10."""
    parts = re.split(r"(\d+)", path.name.lower())
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part) for part in parts
    )


def normalize_headings(markdown: str) -> str:
    """Keep the first heading as H1 and demote all later headings by one."""
    normalized: list[str] = []
    in_fence = False
    seen_title = False

    for line in markdown.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            normalized.append(line)
            continue

        match = HEADING_RE.match(line) if not in_fence else None
        if match:
            hashes, text = match.groups()
            text = CLOSING_HASHES_RE.sub("", text)
            if not seen_title:
                seen_title = True
                line = f"# {text}"
            else:
                level = min(len(hashes) + 1, 6)
                line = f"{'#' * level} {text}"

        normalized.append(line)

    return "\n".join(normalized) + "\n"


def first_heading(markdown: str) -> str | None:
    """Return the first ATX heading outside a fenced code block."""
    in_fence = False
    for line in markdown.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            match = HEADING_RE.match(line)
            if match:
                return CLOSING_HASHES_RE.sub("", match.group(2))
    return None


def rewrite_local_org_links(markdown: str, org_stems: set[str]) -> str:
    """Point links to generated pages without touching external .org URLs."""

    def replace(match: re.Match[str]) -> str:
        stem, anchor = match.group(1), match.group(2) or ""
        if stem not in org_stems:
            return match.group(0)
        return f"]({stem}.md{anchor})"

    return LOCAL_ORG_LINK_RE.sub(replace, markdown)


def escape_summary_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def main() -> int:
    if not shutil.which("pandoc"):
        print("error: required command 'pandoc' not found", file=sys.stderr)
        return 1

    org_files = sorted(ROOT.glob("*.org"), key=natural_key)
    if not org_files:
        print(f"error: no *.org files found in {ROOT}", file=sys.stderr)
        return 1

    org_stems = {org.stem for org in org_files}

    SRC.mkdir(exist_ok=True)

    # Remove only generated Markdown; leave any asset files or directories.
    for generated in SRC.iterdir():
        if generated.is_file() and generated.suffix.lower() == ".md":
            generated.unlink()

    summary = ["# Summary", ""]

    for org in org_files:
        result = subprocess.run(
            [
                "pandoc",
                str(org),
                "--from=org",
                "--to=gfm",
                "--wrap=none",
                "--markdown-headings=atx",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            print(
                f"error: pandoc failed for {org}:\n{result.stderr}",
                file=sys.stderr,
            )
            return result.returncode or 1

        markdown = normalize_headings(result.stdout)
        markdown = rewrite_local_org_links(markdown, org_stems)
        title = first_heading(markdown)
        if title is None:
            print(f"error: no Markdown heading found in {org}", file=sys.stderr)
            return 1

        destination = SRC / f"{org.stem}.md"
        destination.write_text(markdown, encoding="utf-8")
        summary.append(
            f"- [{escape_summary_text(title)}]({destination.name})"
        )

    (SRC / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print(f"Generated mdBook sources in {SRC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

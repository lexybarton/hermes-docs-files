#!/usr/bin/env python3
"""
update-docs.py -- Sync the local Hermes Agent docs mirror.

Downloads the concatenated docs bundle (llms-full.txt) and the link
index (llms.txt) from hermes-agent.nousresearch.com, splits the bundle
back into individual per-page Markdown files at their original site
paths (mirroring "website/docs/..." under this folder -- e.g. the
"Installation" chapter, whose bundle marker reads
"website/docs/getting-started/installation.md", is written to
"getting-started/installation.md"), and writes a local copy of the
link index with relative .md links for offline browsing/grepping.

Usage:
    python update-docs.py [--root PATH] [--no-download]

Run it from anywhere; by default it writes into the folder this
script lives in. Use --no-download to re-split an already-downloaded
DONTREADWHOLEFILE-llms-full.txt without hitting the network (handy if
you already refreshed it another way, or want to re-run the split
after fixing a bug in this script).

Re-running is safe: existing files are overwritten in place, and
pages removed from the bundle are simply not re-written (stale files
from a previous run are not deleted automatically).
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path

FULL_URL = "https://hermes-agent.nousresearch.com/docs/llms-full.txt"
INDEX_URL = "https://hermes-agent.nousresearch.com/docs/llms.txt"
SITE_DOCS_BASE = "https://hermes-agent.nousresearch.com/docs/"

FULL_FILENAME = "DONTREADWHOLEFILE-llms-full.txt"
INDEX_FILENAME = "llms.txt"
LOCAL_INDEX_FILENAME = "llms.local.txt"

# Marker looks like: <!-- source: website/docs/getting-started/installation.md -->
SOURCE_RE = re.compile(r"^<!--\s*source:\s*(\S+)\s*-->\s*$", re.MULTILINE)
SOURCE_ROOT = "website/docs/"

# The generator glues sections together with a blank line, a bare
# "---" rule, and another blank line, immediately before the next
# marker (verified against the current bundle: every one of the 227
# sections ends with this exact separator, except the final one which
# has no trailing blank line after it).
SECTION_SEPARATOR = "\n\n---\n\n"
SECTION_SEPARATOR_FINAL = "\n\n---\n"


def fetch(url: str) -> str:
    print(f"Downloading {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-docs-sync/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def split_bundle(text: str, root: Path) -> int:
    """Split the concatenated bundle into individual files under root."""
    matches = list(SOURCE_RE.finditer(text))
    if not matches:
        print("No '<!-- source: ... -->' markers found -- nothing to split.", file=sys.stderr)
        return 0

    written = 0
    for i, m in enumerate(matches):
        source_path = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end]

        # Drop the section separator the generator inserts before the
        # next marker (or at end of file), rather than blindly
        # stripping trailing "---" -- pages can legitimately end with
        # their own horizontal rule.
        if chunk.endswith(SECTION_SEPARATOR):
            chunk = chunk[: -len(SECTION_SEPARATOR)]
        elif chunk.endswith(SECTION_SEPARATOR_FINAL):
            chunk = chunk[: -len(SECTION_SEPARATOR_FINAL)]

        chunk = chunk.strip("\n") + "\n"

        if not source_path.startswith(SOURCE_ROOT):
            print(f"  skip (unexpected source root): {source_path}", file=sys.stderr)
            continue

        rel_path = source_path[len(SOURCE_ROOT):]
        out_path = root / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(chunk, encoding="utf-8")
        written += 1

    return written


LINK_RE = re.compile(
    r"\[([^\]]+)\]\((https://hermes-agent\.nousresearch\.com/docs/[^)\s]*)\)"
)


def build_local_index(index_text: str) -> str:
    """Rewrite llms.txt links to relative local .md paths.

    "- [Computer Use](https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use)"
    becomes
    "- [Computer Use](./user-guide/features/computer-use.md)"
    """

    def repl(match: "re.Match[str]") -> str:
        label, url = match.group(1), match.group(2)
        if not url.startswith(SITE_DOCS_BASE):
            return match.group(0)
        rel = url[len(SITE_DOCS_BASE):]
        rel = rel.split("#", 1)[0].split("?", 1)[0].rstrip("/")
        if not rel:
            return match.group(0)
        return f"[{label}](./{rel}.md)"

    return LINK_RE.sub(repl, index_text)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Download and split the Hermes Agent docs bundle into a local mirror."
    )
    ap.add_argument(
        "--root",
        default=None,
        help="Docs folder to write into (default: the folder this script lives in)",
    )
    ap.add_argument(
        "--no-download",
        action="store_true",
        help=f"Reuse the local {FULL_FILENAME} / {INDEX_FILENAME} instead of downloading fresh copies",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    full_path = root / FULL_FILENAME
    index_path = root / INDEX_FILENAME

    if args.no_download:
        full_text = full_path.read_text(encoding="utf-8")
        index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    else:
        full_text = fetch(FULL_URL)
        full_path.write_text(full_text, encoding="utf-8")
        index_text = fetch(INDEX_URL)
        index_path.write_text(index_text, encoding="utf-8")

    count = split_bundle(full_text, root)
    print(f"Wrote {count} page files under {root}")

    if index_text:
        local_index = build_local_index(index_text)
        local_index_path = root / LOCAL_INDEX_FILENAME
        local_index_path.write_text(local_index, encoding="utf-8")
        print(f"Wrote local index: {local_index_path}")


if __name__ == "__main__":
    main()

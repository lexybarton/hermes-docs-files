# hermes-docs-files

Official docs from https://hermes-agent.nousresearch.com/docs/llms-full.txt, split into one Markdown file per page and mirrored at the same path the docs site uses (e.g. `getting-started/installation.md`, `user-guide/features/computer-use.md`).

## Layout

- Everything under `developer-guide/`, `getting-started/`, `guides/`, `integrations/`, `reference/`, `user-guide/` and `user-stories.mdx` -- the individual doc pages.
- `llms.local.txt` -- the site's link index (`llms.txt`), rewritten to relative local paths for offline navigation.
- `llms.txt` -- the original index, unmodified, for reference.
- `update-docs.py` -- downloads the latest bundle and re-splits it into the files above. Run `python update-docs.py` to refresh everything, or `python update-docs.py --no-download` to re-split a bundle you already have locally.
- `DONTREADWHOLEFILE-llms-full.txt` -- the raw concatenated bundle `update-docs.py` downloads and splits. It's the source of truth for the split, but redundant with the split files themselves -- don't read it directly (hence the name).

## Downloading just the docs

The repo's "Download ZIP" / `codeload` archive intentionally excludes `update-docs.py`, `DONTREADWHOLEFILE-llms-full.txt`, and `.github/` (see `.gitattributes`) -- so a plain zip download is just the doc pages plus this README and the LICENSE, nothing else. Clone the repo instead if you want the update tooling too.

## Staying up to date

A scheduled GitHub Action (`.github/workflows/update-docs.yml`) refreshes this mirror twice a day: it re-downloads the bundle, re-splits it, and pushes a commit only if something actually changed. If the page count drops by more than 10% in one run, it aborts without committing instead of silently deleting pages -- that's usually a sign the upstream bundle format changed rather than real doc removals. You can also trigger a refresh manually from the repo's Actions tab.

## License

MIT -- matching the license of the upstream Hermes Agent documentation.

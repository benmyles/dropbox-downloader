# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tool (`dbx-dl`) for downloading files/folders from Dropbox via the Dropbox API. Uses `uv` for dependency management and `docopt-ng` for CLI argument parsing.

## Commands

```sh
uv sync                                    # Install dependencies
uv run dbx-dl --help                       # Show CLI help
uv run dbx-dl download-recursive [<path>]  # Download files recursively
uv run dbx-dl du [<path>]                  # Show disk usage for path
uv run dbx-dl ls [<path>]                  # List folder contents
```

Must be run from the directory containing `dbx-dl.ini`.

## Configuration

`dbx-dl.ini` (gitignored) provides runtime config. See `dbx-dl.ini.dist` for the template. Keys:
- `api_key` — Dropbox API token
- `dl_dir` — local directory for downloaded files
- `to_dl` — optional CSV list of root-level folder/file names to download (filters at root level only)

## Architecture

Entry point: `dropbox_downloader/cli.py:main()` — parses CLI args via docopt, instantiates `DropboxDownloader`, and dispatches to the appropriate command method.

`DropboxDownloader` (cli.py) — Controller that loads config from `dbx-dl.ini`, initializes the Dropbox SDK client, and orchestrates commands. The `dl()` method uses a thread pool (up to 8 `DownloadWorker` threads) with a `Queue` to parallelize recursive downloads of top-level folders.

`Downloader` — Handles recursive folder traversal and file downloading. Skips files that already exist locally with matching size. Creates local directories as needed.

`DownloadWorker` — `Thread` subclass that pulls folder paths from a `Queue` and calls `Downloader.download_recursive()`.

`DiskUsage` — Recursively sums file sizes for a given Dropbox path via the API.

## Notes

- No test suite exists in this project.
- Dependencies: `dropbox` SDK and `docopt-ng` (see `pyproject.toml`).
- PascalCase filenames are used for class modules (e.g., `Downloader.py`, `DiskUsage.py`).

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tool (`dbx-dl`) for downloading files/folders from Dropbox via the Dropbox API. Uses `uv` for dependency management and `docopt-ng` for CLI argument parsing.

## Commands

```sh
uv sync                                    # Install dependencies
uv run dbx-dl --help                       # Show CLI help
uv run dbx-dl download-recursive [<path>]           # Download files recursively
uv run dbx-dl download-recursive --skip-noise [<path>]  # Download, skipping noise files
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

`DropboxDownloader` (cli.py) — Controller that loads config from `dbx-dl.ini`, initializes the Dropbox SDK client, and orchestrates commands. The `dl()` method uses a thread pool (up to 8 `DownloadWorker` threads) with a `Queue` to parallelize recursive downloads of top-level folders. Accepts `--skip-noise` flag and passes `SkipFilter`/`DownloadLogger` instances into `Downloader`.

`Downloader` — Handles recursive folder traversal and file downloading. Skips files that already exist locally with matching size. Creates local directories as needed. Consults `SkipFilter` before downloading and logs all activity via `DownloadLogger`.

`DownloadWorker` — `Thread` subclass that pulls folder paths from a `Queue` and calls `Downloader.download_recursive()`.

`SkipFilter` — Evaluates whether a Dropbox entry should be skipped when `--skip-noise` is active. Three rule categories: **build** (compiled files, caches, package dirs like `*.pyc`, `__pycache__`, `node_modules`, `.eggs`, etc.), **git** (`.git` directories), and **deleted** (`DeletedMetadata` entries, `.dropbox.cache`, Dropbox system files).

`DownloadLogger` — Thread-safe file logger that writes to `log/downloaded.log` (successful downloads and already-existing files) and `log/skipped.log` (skipped entries with the rule/reason).

`DiskUsage` — Recursively sums file sizes for a given Dropbox path via the API.

## Logging

When `download-recursive` runs, two log files are written under `log/` (gitignored):
- `log/downloaded.log` — every downloaded file and every already-existing file (with timestamps).
- `log/skipped.log` — every skipped entry with the skip rule/reason (e.g. `build: file extension .pyc`).

Each session writes a header line so successive runs are easy to distinguish.

## Notes

- No test suite exists in this project.
- Dependencies: `dropbox` SDK and `docopt-ng` (see `pyproject.toml`).
- PascalCase filenames are used for class modules (e.g., `Downloader.py`, `DiskUsage.py`, `SkipFilter.py`, `DownloadLogger.py`).

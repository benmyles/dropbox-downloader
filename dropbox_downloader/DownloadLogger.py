import os
import threading
from datetime import datetime, timezone
from pathlib import Path


class DownloadLogger:
    """Thread-safe logger that records downloaded and skipped files to disk.

    Log files are created under ``<base_path>/log/``.

    * ``downloaded.log`` – one line per successfully downloaded file.
    * ``skipped.log``    – one line per skipped entry, including the reason.
    """

    def __init__(self, base_path: str):
        log_dir = os.path.join(base_path, "log")
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        self._downloaded_path = os.path.join(log_dir, "downloaded.log")
        self._skipped_path = os.path.join(log_dir, "skipped.log")

        self._lock = threading.Lock()

        # Write a session header so successive runs are easy to distinguish.
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        header = "--- session started at {} ---".format(ts)
        self._append(self._downloaded_path, header)
        self._append(self._skipped_path, header)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_downloaded(self, dropbox_path: str, local_path: str) -> None:
        """Record a successful download."""
        ts = self._timestamp()
        line = "{} DOWNLOADED {} -> {}".format(ts, dropbox_path, local_path)
        self._append(self._downloaded_path, line)

    def log_already_exists(self, dropbox_path: str, local_path: str) -> None:
        """Record that a file was skipped because it already exists locally."""
        ts = self._timestamp()
        line = "{} EXISTS     {} (local: {})".format(ts, dropbox_path, local_path)
        self._append(self._downloaded_path, line)

    def log_skipped(self, dropbox_path: str, reason: str) -> None:
        """Record a skipped file/directory with the rule that triggered it."""
        ts = self._timestamp()
        line = "{} SKIPPED {} -- reason: {}".format(ts, dropbox_path, reason)
        self._append(self._skipped_path, line)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _append(self, filepath: str, line: str) -> None:
        with self._lock:
            with open(filepath, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

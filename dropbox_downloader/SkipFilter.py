import fnmatch
import os

from dropbox.files import DeletedMetadata


# File extensions considered build artifacts
_BUILD_EXTENSIONS = frozenset((
    # Python
    '.pyc', '.pyo', '.pyd',
    # C / C++ / general compiled
    '.o', '.obj', '.so', '.dylib', '.dll', '.a', '.lib',
    # Java / JVM
    '.class', '.jar', '.war', '.ear',
    # .NET
    '.exe', '.out',
    # Python packaging
    '.whl', '.egg',
))

# Directory names that are build / tooling artifacts
_BUILD_DIR_NAMES = frozenset((
    '__pycache__',
    'node_modules',
    '.tox',
    '.nox',
    '.mypy_cache',
    '.pytest_cache',
    '.ruff_cache',
    '.cache',
    '.eggs',
    '.build',
    '.gradle',
    'target',          # Rust / Maven
    'bower_components',
    '.sass-cache',
    '.parcel-cache',
    '.next',
    '.nuxt',
    '.turbo',
    'dist-newstyle',   # Haskell
    '__pypackages__',
    '.venv',
    'venv',
    'env',
))

# Glob-style patterns matched against the entry *name* (not full path)
_BUILD_NAME_GLOBS = (
    '*.egg-info',
)

# Directory / file names associated with version-control internals
_GIT_NAMES = frozenset((
    '.git',
))

# Dropbox system / trash artefacts checked against the *full lower-cased path*
_DROPBOX_TRASH_PATH_SEGMENTS = (
    '/.dropbox.cache/',
)

# Dropbox system file names
_DROPBOX_SYSTEM_NAMES = frozenset((
    '.dropbox',
    '.dropbox.attr',
))


class SkipFilter:
    """Decides whether a Dropbox entry should be skipped during download.

    Three rule categories (only evaluated when *skip_noise* is ``True``):

    * **build** – compiled files, caches and package manager directories
    * **git** – ``.git`` directories
    * **deleted** – Dropbox ``DeletedMetadata`` entries and trash / system files
    """

    def __init__(self, *, skip_noise: bool = False):
        self._skip_noise = skip_noise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def should_skip(self, entry) -> tuple[bool, str]:
        """Return ``(True, reason)`` if *entry* should be skipped, else ``(False, '')``.

        *entry* is a Dropbox metadata object (``FileMetadata``,
        ``FolderMetadata``, or ``DeletedMetadata``).
        """
        if not self._skip_noise:
            return False, ''

        name: str = entry.name
        path_lower: str = getattr(entry, 'path_lower', '') or ''

        # --- deleted / trashed -------------------------------------------
        if isinstance(entry, DeletedMetadata):
            return True, 'deleted: Dropbox DeletedMetadata entry'

        if name.lower() in _DROPBOX_SYSTEM_NAMES:
            return True, f'deleted: Dropbox system file ({name})'

        for segment in _DROPBOX_TRASH_PATH_SEGMENTS:
            if segment in path_lower:
                return True, f'deleted: path contains Dropbox trash segment ({segment.strip("/")})'

        # --- .git --------------------------------------------------------
        if name in _GIT_NAMES:
            return True, f'git: version-control directory ({name})'

        # --- build artifacts ---------------------------------------------
        _, ext = os.path.splitext(name)
        if ext.lower() in _BUILD_EXTENSIONS:
            return True, f'build: file extension {ext}'

        if name in _BUILD_DIR_NAMES:
            return True, f'build: build/cache directory ({name})'

        for glob in _BUILD_NAME_GLOBS:
            if fnmatch.fnmatch(name, glob):
                return True, f'build: name matches pattern ({glob})'

        # Check if any path component is a known build or git directory.
        # This catches files *inside* e.g. ``__pycache__/`` or ``.git/``
        # when traversal somehow reaches them individually.
        if path_lower:
            parts = path_lower.split('/')
            for part in parts:
                if part in _BUILD_DIR_NAMES:
                    return True, f'build: inside build/cache directory ({part})'
                if part in _GIT_NAMES:
                    return True, f'git: inside version-control directory ({part})'

        return False, ''

    def should_skip_path(self, path_lower: str, name: str) -> tuple[bool, str]:
        """Lightweight check using only *path_lower* and *name* strings.

        Useful when the full metadata object is not yet available (e.g. when
        deciding whether to recurse into a folder from the top-level list).
        """
        if not self._skip_noise:
            return False, ''

        if name.lower() in _DROPBOX_SYSTEM_NAMES:
            return True, f'deleted: Dropbox system file ({name})'

        for segment in _DROPBOX_TRASH_PATH_SEGMENTS:
            if segment in path_lower:
                return True, f'deleted: path contains Dropbox trash segment ({segment.strip("/")})'

        if name in _GIT_NAMES:
            return True, f'git: version-control directory ({name})'

        _, ext = os.path.splitext(name)
        if ext.lower() in _BUILD_EXTENSIONS:
            return True, f'build: file extension {ext}'

        if name in _BUILD_DIR_NAMES:
            return True, f'build: build/cache directory ({name})'

        for glob in _BUILD_NAME_GLOBS:
            if fnmatch.fnmatch(name, glob):
                return True, f'build: name matches pattern ({glob})'

        return False, ''

#!/usr/bin/env python3
"""Dropbox Downloader

Usage:
  dbx-dl download-recursive [--skip-noise] [<path>]
  dbx-dl du [<path>]
  dbx-dl ls [<path>]
  dbx-dl (-h | --help)
  dbx-dl --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --skip-noise  Skip build artifacts, .git dirs, and deleted/trashed files.
"""
import dropbox
import dropbox.exceptions
import os
import os.path

from docopt import docopt
from dropbox.files import FolderMetadata, FileMetadata
from configparser import ConfigParser
from queue import Queue

from dropbox_downloader.DiskUsage import DiskUsage
from dropbox_downloader.Downloader import Downloader
from dropbox_downloader.DownloadLogger import DownloadLogger
from dropbox_downloader.DownloadWorker import DownloadWorker
from dropbox_downloader.SkipFilter import SkipFilter


class DropboxDownloader:
    """Controlling class for console command."""

    def __init__(self, *, skip_noise: bool = False):
        self._base_path = os.getcwd()
        ini_settings = self._load_config()
        self._dbx = dropbox.Dropbox(ini_settings.get('main', 'api_key'))
        self._dl_dir = ini_settings.get('main', 'dl_dir')
        self._to_dl = str(ini_settings.get('main', 'to_dl')).split(',') or None
        self._skip_noise = skip_noise

    def dl(self, path: str = ''):
        """Recursively download all files in given path, or entire dropbox if none given"""
        skip_filter = SkipFilter(skip_noise=self._skip_noise)
        logger = DownloadLogger(self._base_path)
        d = Downloader(self._base_path, self._dbx, self._dl_dir, self._to_dl,
                       skip_filter=skip_filter, logger=logger)
        queue = Queue()

        files_and_folders = d.list_files_and_folders(path)
        n_files_and_folders = len(files_and_folders.entries)
        n_threads = n_files_and_folders if n_files_and_folders < 8 else 8

        # Create 8 ListWorker threads
        for x in range(n_threads):
            worker = DownloadWorker(d, queue)
            # Setting daemon to True will let the main thread exit even though the workers are blocking
            worker.daemon = True
            worker.start()

        for f in files_and_folders.entries:
            skip, reason = skip_filter.should_skip(f)
            if skip:
                entry_path = getattr(f, 'path_display', '') or getattr(f, 'path_lower', '') or f.name
                print('Skipping {} ({})'.format(entry_path, reason))
                logger.log_skipped(entry_path, reason)
                continue

            if isinstance(f, FolderMetadata):
                queue.put(f.path_display or f.path_lower)
            elif isinstance(f, FileMetadata):
                d.download_file(f)
            else:
                raise RuntimeError(
                    'Unexpected folder entry: {}\nExpected types: FolderMetadata, FileMetadata'.format(f))

        # Causes the main thread to wait for the queue to finish processing all the tasks
        queue.join()
        print('All files in {} downloaded'.format(path or 'your entire dropbox'))

    def du(self, path: str = ''):
        """Get disk usage (size) for path"""
        du = DiskUsage(self._dbx)
        du.du(path)

    def ls(self, path: str = ''):
        """Print contents of a given folder path in text columns"""
        files_and_folders = self._dbx.files_list_folder(path)
        print('Listing path "{}"...'.format(path))
        file_list = [{
            'id':         f.id,
            'name':       f.name,
            'path':       f.path_display or f.path_lower
        } for f in files_and_folders.entries]

        # get column sizes for formatting
        max_len_id = max(len(f['id']) for f in file_list)
        max_len_name = max(len(f['name']) for f in file_list)
        max_len_path = max(len(f['path']) for f in file_list)
        for f in file_list:
            print('{:>{}} {:>{}} {:>{}}'.format(
                f['id'], max_len_id, f['name'], max_len_name, f['path'], max_len_path))

    def _load_config(self) -> ConfigParser:
        """Load `dbx-dl.ini` config file from the current working directory.

        :return: ConfigParser
        """
        config = ConfigParser(allow_no_value=True)
        config_path = os.path.join(self._base_path, 'dbx-dl.ini')
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                'Config file not found: {}\n'
                'Make sure you run dbx-dl from the directory containing dbx-dl.ini'.format(config_path))
        with open(config_path) as f:
            config.read_file(f)

        return config


def main():
    arguments = docopt(__doc__, version='Dropbox Downloader')
    skip_noise = arguments.get('--skip-noise', False)
    dd = DropboxDownloader(skip_noise=skip_noise)
    if arguments['download-recursive']:
        dd.dl(arguments.get('<path>') or '')
    elif arguments.get('du'):
        dd.du(arguments.get('<path>') or '')
    elif arguments.get('ls'):
        dd.ls(arguments.get('<path>') or '')


if __name__ == '__main__':
    main()

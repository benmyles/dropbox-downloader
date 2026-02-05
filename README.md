# Dropbox Downloader

## Summary

#### Python CLI tool with two functions

1) Download all files and folders recursively for a given path, or entire
   Dropbox if no path is given. Files are placed in the `dl_dir` folder
   specified in the `dbx-dl.ini` file. May also specify `to_dl` csv list to
   download specific root files / folders by name.

2) Columnar list of all files / folders in a given `path`.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Dropbox API key

## Installation

```sh
LOCAL_PATH="/path/to/clone/repo" # change this to your preferred location

git clone git@github.com:digitalengineering/dropbox-downloader.git "$LOCAL_PATH"

cd "$LOCAL_PATH"
uv sync

cat > "$LOCAL_PATH/dbx-dl.ini" <<EOF
[main]
api_key = MyDropboxApiKey
dl_dir = $LOCAL_PATH/Download
to_dl = Folder 1,Folder B,Another Folder Name,onemore.txt
EOF
```

## Obtaining Dropbox Api Key

See here: https://www.dropbox.com/developers/apps

## Usage

Run all commands from the directory containing your `dbx-dl.ini` file.

```sh
# Show help
uv run dbx-dl --help

# Download entire dropbox to folder specified in "dl_dir" in "dbx-dl.ini" file
uv run dbx-dl download-recursive

# Download a specific path
uv run dbx-dl download-recursive "/path/to/folder"

# Show disk usage for a path
uv run dbx-dl du "/path/to/folder"

# List contents of root folder
uv run dbx-dl ls ""

# List contents of other folder
uv run dbx-dl ls "/path/to/folder"
```

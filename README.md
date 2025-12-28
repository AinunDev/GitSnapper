# GitSnapper

GitSnapper is a command-line utility that downloads all public GitHub repositories for a specified user as ZIP archives.

## Features

* Fetches all public repositories for a GitHub user
* Automatically downloads repositories as ZIP files
* Displays real-time download progress
* Skips repositories that have already been downloaded
* Gracefully handles network errors and timeouts

## Usage

You can run GitSnapper directly with Python:

```bash
python GitSnapper.py
```

Or, if you prefer a standalone executable, it has been compiled via Nuitka. You can also compile it yourself:

```bash
nuitka --standalone --windows-icon-from-ico=icon.png GitSnapper.py
```

After compilation, you can run the `.exe` without installing Python or any dependencies.

> **Note:** The executable may be flagged as a virus by some antivirus programs due to the compilation process. This is a false positive. The full source code is included, so you can review it or recompile it yourself to verify.

## Disclaimer

This project is provided as-is, without warranty of any kind. You are responsible for complying with GitHub’s Terms of Service, repository licenses, and all applicable laws. The author is not responsible for misuse, data loss, or any legal consequences resulting from the use of this software.

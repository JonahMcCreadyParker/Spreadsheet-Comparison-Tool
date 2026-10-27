# Back up and install the complete Windows application

Repository: https://github.com/JonahMcCreadyParker/Spreadsheet-Comparison-Tool

## What must be committed

Commit the source, tests, scripts, dependency files, documentation, `.gitignore`, `.gitattributes`, and **every file under `dist/SpreadsheetCompare/`**. The executable requires its adjacent `_internal` folder. That folder includes Python, Qt DLLs/plugins and compiled `.pyd` extension modules. No Python installation is needed to run this portable Windows x64 build on another compatible Windows device.

`.gitignore` permits this complete distribution while continuing to exclude `.venv`, `build`, test caches and temporary `artifacts`. The distribution exception deliberately follows `*.py[cod]`, which otherwise also ignores essential `.pyd` files. `.gitattributes` keeps executable/runtime files binary during checkout. Changing ignore rules does not automatically upload anything: files still need to be added, committed and pushed. Already tracked files stay tracked even when an ignore rule matches them.

The distribution is about 112 MiB in total; its largest individual file is about 20 MiB. Those are separate files, not a single 112 MiB Git blob. GitHub's per-file limit applies individually. Future large standalone ZIPs are better uploaded as GitHub Release assets. See https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github.

## First connect this working folder

At the time this guide was written, this project folder had no `.git` directory, although the GitHub repository already contained an initial backup. Preserve the existing remote history by cloning it to a **new sibling folder**, then copying the updated project files into that clone. Do not initialise a separate unrelated history or force-push over the backup.

PowerShell commands (the destination must not already exist):

```powershell
Set-Location 'C:\Users\Jonah\Documents'
git clone https://github.com/JonahMcCreadyParker/Spreadsheet-Comparison-Tool.git Spreadsheet_Comparison_Tool_GitHub
robocopy 'C:\Users\Jonah\Documents\Spreadsheet_Comparison_Tool' 'C:\Users\Jonah\Documents\Spreadsheet_Comparison_Tool_GitHub' /E /XD .git .venv build artifacts .pytest_cache __pycache__ /XF *.spec
# Robocopy exit codes 0–7 mean success; stop if its exit code is 8 or higher.
Set-Location 'C:\Users\Jonah\Documents\Spreadsheet_Comparison_Tool_GitHub'
git add --all
git status --short
git diff --cached --stat
git commit -m "Include complete portable Windows application"
git push origin main
```

Authenticate to GitHub when prompted. If Git requires an author identity, configure your Git name and email before committing. GitHub Desktop is an alternative: clone this existing repository, copy the project contents into that local clone, review the Changes list, Commit to main, then Push origin. Merely copying the folder or changing `.gitignore` does not publish the update.

Review the staged files before committing: the distribution must include `.exe`, `.dll`, **`.pyd`**, plugins and its other runtime files. Do not copy only the executable. The original working folder remains available; the clone becomes the Git-connected project folder for subsequent work. Copying with `/E` updates/adds files while preserving remote-only files such as LICENSE; it does not delete files. If files are intentionally removed from the application in a future version, also remove their stale copies in the clone before staging.

## Install on another Windows device

Clone the repository, or choose **Code → Download ZIP** on GitHub and fully extract it. Open:

```text
dist\SpreadsheetCompare\SpreadsheetCompare.exe
```

Keep `_internal` alongside the executable. A `.lnk` shortcut from the original computer may contain an absolute path; create a new local shortcut to this executable on the other device. The build is for Windows x64; it is not a macOS/Linux application.

For later updates to an existing clone, close the application, run `git pull --ff-only`, then reopen the executable. Alternatively download/extract a fresh ZIP into a new folder.

## Publishing future application changes

Work from the Git-connected clone. Rebuild the distribution after changing Python source:

```powershell
.\scripts\setup_windows.ps1
.\scripts\build_windows.ps1
git add --all
git diff --cached --stat
git commit -m "Update portable Windows application"
git push origin main
```

The build runs the test suite and packaged GUI smoke check. Commit the rebuilt distribution together with its source changes so other devices receive the matching application. Python and build tools are required only on the build workstation. A local commit is uploaded only after a successful git push; verify the latest commit on GitHub before installing on another device.

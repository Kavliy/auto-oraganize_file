# filesort

[中文说明](README.md) | English

`filesort` is a lightweight command-line tool that sorts top-level files in a selected directory into subfolders automatically.

Current features:

- Sort by modification date
- Sort by file extension
- Sort by regex pattern
- Save reusable presets
- Save global extension groups
- Undo the last organization run

## Scope

- Only processes top-level files in the selected directory
- Does not scan subdirectories recursively
- Category names are sanitized automatically to avoid invalid paths or nested output

## Requirements

- Python 3.6+
- Standard library only, no third-party dependencies

## Installation

```bash
git clone https://github.com/Kavliy/auto-oraganize_file.git
cd auto-oraganize_file
chmod +x filesort
```

You can also place `filesort` in your `PATH` for global use.

## Basic usage

```bash
filesort <target_dir> [OPTIONS]
filesort <target_dir> --undo
filesort --list presets|type-groups|all
filesort presets list
filesort groups list
```

By default, the tool shows a preview and asks for confirmation. Add `--execute` to run immediately.

## Options

| Option | Description |
| --- | --- |
| `-t`, `--by-type` | Sort by extension, applying saved extension groups by default |
| `-d`, `--by-date [FORMAT]` | Sort by modification time, default format is `%Y-%m` |
| `-p`, `--by-pattern PATTERN` | Sort by regex; capture group 1 becomes the category name |
| `--preset NAME` | Use a saved preset |
| `--save-preset NAME` | Save the current strategy as a preset |
| `--list presets\|type-groups\|all` | List saved presets, extension groups, or all config |
| `--list-preset` | List saved presets |
| `--remove-preset NAME` | Remove one saved preset |
| `--set-type-group NAME=ext1,ext2` | Save a global extension group |
| `--remove-type-group NAME` | Remove one extension group |
| `--list-type-groups` | List saved extension groups |
| `--no-type-groups` | Ignore global extension groups for the current by-type run |
| `-e`, `--execute` | Skip confirmation and execute immediately |
| `-u`, `--undo` | Undo the most recent organization run |
| `--completion SHELL` | Print a Tab-completion script for bash, zsh, or PowerShell |

## Examples

### 1. Sort by extension

```bash
filesort ~/Downloads --by-type
```

### 2. Sort by date

```bash
filesort ~/Documents --by-date
filesort ~/Photos --by-date %Y/%m
```

Notes:

- Formats such as `%Y/%m` are sanitized into a single directory name like `2026_04`

### 3. Sort by regex pattern

```bash
filesort ~/exports --by-pattern '^([^_]+).*'
```

For filenames like:

```text
QData一体机交易历史备库2026年Q2季度4月第三次巡检报告
QData一体机业务整合备库2026年Q2季度4月第三次巡检报告
QData一体机余额宝备库2026年Q2季度4月第三次巡检报告
```

you can group them with:

```bash
filesort ~/reports --by-pattern 'QData一体机(.+?)\d{4}年.*'
```

### 4. Save reusable presets

Save a frequently used regex strategy:

```bash
filesort ~/reports --by-pattern 'QData一体机(.+?)\d{4}年.*' --save-preset qdata-db
```

Reuse it later in any selected directory:

```bash
filesort ~/reports --preset qdata-db
```

Inspect and remove presets:

```bash
filesort presets list
filesort presets remove qdata-db
```

Notes:

- Presets save the strategy and its parameters
- They do not save the target directory path

### 5. Save global extension groups

Once configured, these groups are applied automatically whenever you run `-t`.

```bash
filesort --set-type-group images=jpg,jpeg,png,gif
filesort --set-type-group docs=pdf,doc,docx
```

Then simply run:

```bash
filesort ~/Downloads -t
```

Example behavior:

- `jpg`, `jpeg`, `png`, `gif` go to `images/`
- `pdf`, `doc`, `docx` go to `docs/`
- unmapped extensions still use their own extension, for example `mp4 -> mp4/`

Inspect and remove groups:

```bash
filesort groups list
filesort groups remove images
```

Temporarily ignore saved groups:

```bash
filesort ~/Downloads -t --no-type-groups
```

### 6. List saved config

```bash
filesort --list presets
filesort --list type-groups
filesort --list all
```

The older flags still work:

```bash
filesort --list-preset
filesort --remove-preset qdata-db
filesort --list-type-groups
filesort --remove-type-group images
```

### 7. Enable Tab completion

For the current PowerShell session:

```powershell
python filesort completion powershell | Out-String | Invoke-Expression
```

For the current bash session:

```bash
source <(python filesort completion bash)
```

For the current zsh session:

```zsh
source <(python filesort completion zsh)
```

## Undo

```bash
filesort ~/Downloads --undo
```

The current undo behavior supports:

- restoring files moved by the last run
- removing empty category directories automatically
- keeping incomplete undo records when some files cannot be restored, so you can fix the issue and run `--undo` again

## Configuration file

Presets and extension groups are stored in the same config file.

- Windows: `%APPDATA%\filesort\presets.json`
- Linux: `$XDG_CONFIG_HOME/filesort/presets.json`
- If `XDG_CONFIG_HOME` is not set, `~/.config/filesort/presets.json` is used

You can override the location with:

```bash
FILESORT_PRESETS_FILE=/path/to/presets.json
```

## Error handling

- Invalid regex patterns return a clean error message instead of a Python traceback
- Unsafe category names are sanitized automatically
- Conflicting extension-group assignments are rejected with a clear error

## Good fit

- first-pass cleanup for download folders
- archiving reports, screenshots, and exported files
- batch organization for files with consistent naming patterns
- personal workflows where you want to configure once and run quickly later

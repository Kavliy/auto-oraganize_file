### 这是一个自动整理文件的程序,能够按照时间/文件类型/模式匹配整理文件,并支持保存常用整理预设与扩展名分组
## This program automatically organizes files by date, file type, or pattern matching, and supports reusable presets plus saved extension groups

# filesort

A command-line tool that automatically sorts top-level files in a selected directory into subdirectories by various classification strategies.
一个可以通过多种分类策略自动将所选目录中的顶层文件排序到子目录中的命令行工具。

## Environment 环境

- **Python** 3.6+ (standard library only, no third-party dependencies)

## Installation 安装

Clone the repository and make the script executable:

```bash
git clone https://github.com/Kavliy/auto-oraganize_file
cd qreport_script
chmod +x filesort
```

Optionally, add the script to your `PATH` or create a symlink for global access.

## Usage 用法

```
filesort <target_dir> [OPTIONS]
filesort <target_dir> --undo
```

### Options 选择

| Option | Description |
|--------|-------------|
| `-d, --by-date [FORMAT]` | Group files by modification date. Default format: `%Y-%m`. Category names are sanitized to stay single-level. |
| `-t, --by-type` | Group files by extension (default strategy), applying saved type groups by default. |
| `-p, --by-pattern PATTERN` | Group files by regex pattern — capture group 1 becomes the category name after sanitization. |
| `--preset NAME` | Load a saved preset for the selected directory. |
| `--save-preset NAME` | Save the current strategy as a reusable preset. |
| `--set-type-group NAME=ext1,ext2` | Save a default extension group for `--by-type`, such as `images=jpg,jpeg,png`. |
| `--remove-type-group NAME` | Remove one saved type group. |
| `--list-type-groups` | List saved type groups. |
| `--no-type-groups` | Ignore saved global type groups for this run. |
| `-e, --execute` | Execute directly without preview or confirmation. |
| `-u, --undo` | Rollback the last organization operation. |

By default, the tool shows a preview and asks for confirmation (`y/N`) before making any changes. Only files directly inside the selected directory are processed; subdirectories are not scanned recursively. Presets save the strategy and its parameters, not the target directory path. Saved type groups act as the default behavior for `--by-type`.

## Examples 举例

### Group by file extension (default)

Sort files into subdirectories based on their extension:

```bash
$ ls ~/Downloads
report.pdf  notes.txt  photo.jpg  archive.zip  script.py

$ filesort ~/Downloads

Target: /home/user/Downloads
Files to organize: 5
Categories to create: 5

  [jpg] (1 file(s))
    photo.jpg -> jpg/
  [pdf] (1 file(s))
    report.pdf -> pdf/
  [py] (1 file(s))
    script.py -> py/
  [txt] (1 file(s))
    notes.txt -> txt/
  [zip] (1 file(s))
    archive.zip -> zip/

Proceed? (y/N): y
Done: 5 file(s) organized into 5 categories.

$ ls ~/Downloads
jpg/  pdf/  py/  txt/  zip/  .organize_log.json
```

### Group by modification date

```bash
$ filesort ~/Documents --by-date

Target: /home/user/Documents
Files to organize: 8
Categories to create: 3

  [2026-01] (3 file(s))
    meeting_notes.txt -> 2026-01/
    budget.xlsx -> 2026-01/
  [2026-03] (2 file(s))
    slides.pptx -> 2026-03/
  [2026-04] (3 file(s))
    draft.md -> 2026-04/
    photo.png -> 2026-04/
    export.csv -> 2026-04/

Proceed? (y/N): y
```

Custom date format:

```bash
$ filesort ~/photos --by-date %Y/%m   # sanitized into a single directory name like 2026_04
```

### Group by regex pattern

```bash
# Group files by their prefix (e.g., "project_report_2026.pdf" -> "project")
$ filesort ~/exports --by-pattern '^([^_]+).*'

# Group by date pattern in filename
$ filesort ~/logs --by-pattern '(\d{4}-\d{2}-\d{2})'
```

Unmatched files go to an `uncategorized` directory. Invalid path characters such as `/` and `\` are sanitized so every category stays within a single directory level.
❯ 假如有这样一个文件夹,里面存在文件:
  QData一体机交易历史备库2026年Q2季度4月第三次巡检报告,QData一体机业务整合备库2026年Q2季度4月第三次巡检
  报告,QData一体机余额宝备库2026年Q2季度4月第三次巡检报告,满足:按照库名自动分类

● 使用 --by-pattern 正则分组策略。

  文件名的结构是一致的：

  QData一体机  +  [库名]  +  2026年Q2季度4月第三次巡检报告

  只需用一个正则捕获中间的库名部分：

  $ filesort /path/to/dir --by-pattern 'QData一体机(.+?)\d{4}年.*'

  效果预览：

  Target: /path/to/dir
  Files to organize: 3
  Categories to create: 3

    [交易历史备库] (1 file(s))
      QData一体机交易历史备库2026年Q2季度4月第三次巡检报告 -> 交易历史备库/
    [业务整合备库] (1 file(s))
      QData一体机业务整合备库2026年Q2季度4月第三次巡检报告 -> 业务整合备库/
    [余额宝备库] (1 file(s))
      QData一体机余额宝备库2026年Q2季度4月第三次巡检报告 -> 余额宝备库/

  正则 QData一体机(.+?)\d{4}年.* 的含义：
  - QData一体机 — 匹配固定前缀
  - (.+?) — 捕获组1，非贪婪匹配库名
  - \d{4}年.* — 匹配年份及后续部分（确保不同季度/月份的巡检报告都能匹配）

### Execute without confirmation

```bash
$ filesort ~/Downloads --by-type --execute
Done: 12 file(s) organized into 4 categories.
```

### Save and reuse a preset

```bash
$ filesort ~/reports --by-pattern 'QData一体机(.+?)\d{4}年.*' --save-preset qdata-db
Saved preset 'qdata-db' in '/home/user/.config/filesort/presets.json'.
```

Later, apply the same strategy to any selected directory:

```bash
$ filesort ~/reports --preset qdata-db
```

### Save default extension groups for `--by-type`

```bash
$ filesort --set-type-group images=jpg,jpeg,png,gif
$ filesort --set-type-group docs=pdf,doc,docx
```

After that, a normal by-type run automatically uses those groups:

```bash
$ filesort ~/Downloads --by-type
```

You can inspect or remove them later:

```bash
$ filesort --list-type-groups
$ filesort --remove-type-group images
```

To temporarily ignore the saved groups:

```bash
$ filesort ~/Downloads --by-type --no-type-groups
```

### Undo the last operation

```bash
$ filesort ~/Downloads --undo
Undone: 5 file(s) moved back, strategy='by_type'.
```

Each undo restores files to their original locations and removes empty category directories. If a file cannot be restored because the original path is occupied or the organized copy is missing, the remaining undo entries stay in the log so you can fix the issue and run `--undo` again. Subsequent `--undo` calls roll back earlier operations one at a time.

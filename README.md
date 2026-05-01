# filesort

中文说明 | [English](README_EN.md)

`filesort` 是一个轻量的命令行文件整理工具，用来把所选目录中的顶层文件自动归类到子目录中。

当前支持：

- 按修改时间整理
- 按文件扩展名整理
- 按正则模式整理
- 保存常用整理预设
- 保存全局扩展名分组
- 撤销上一次整理

## 功能边界

- 只处理你指定目录下的顶层文件
- 不递归扫描子目录
- 分类目录名会自动净化，避免生成非法路径或多层目录

## 环境要求

- Python 3.6+
- 仅使用标准库，无第三方依赖

## 安装

```bash
git clone https://github.com/Kavliy/auto-oraganize_file.git
cd auto-oraganize_file
chmod +x filesort
```

你也可以把 `filesort` 放到 `PATH` 中，方便全局调用。

## 基本用法

```bash
filesort <target_dir> [OPTIONS]
filesort <target_dir> --undo
filesort --list presets|type-groups|all
filesort presets list
filesort groups list
```

默认会先显示预览，并要求确认；加上 `--execute` 可以直接执行。

## 命令选项

| 选项 | 说明 |
| --- | --- |
| `-t`, `--by-type` | 按扩展名整理，默认会应用已保存的扩展名分组 |
| `-d`, `--by-date [FORMAT]` | 按修改时间整理，默认格式为 `%Y-%m` |
| `-p`, `--by-pattern PATTERN` | 按正则分组，捕获组 1 作为分类名 |
| `--preset NAME` | 使用已保存的整理预设 |
| `--save-preset NAME` | 将当前整理策略保存为预设 |
| `--list presets\|type-groups\|all` | 查看已保存的预设、扩展名分组或全部配置 |
| `--list-preset` | 查看已保存的整理预设 |
| `--remove-preset NAME` | 删除一个整理预设 |
| `--set-type-group NAME=ext1,ext2` | 保存全局扩展名分组 |
| `--remove-type-group NAME` | 删除一个扩展名分组 |
| `--list-type-groups` | 查看当前扩展名分组 |
| `--no-type-groups` | 本次按扩展名整理时忽略全局扩展名分组 |
| `-e`, `--execute` | 跳过确认，直接执行 |
| `-u`, `--undo` | 撤销最近一次整理 |
| `--completion SHELL` | 输出 bash、zsh 或 PowerShell 的 Tab 补全脚本 |

## 示例

### 1. 按扩展名整理

```bash
filesort ~/Downloads --by-type
```

### 2. 按时间整理

```bash
filesort ~/Documents --by-date
filesort ~/Photos --by-date %Y/%m
```

说明：

- `%Y/%m` 这类格式会被自动净化成单层目录名，例如 `2026_04`

### 3. 按正则模式整理

```bash
filesort ~/exports --by-pattern '^([^_]+).*'
```

例如文件名：

```text
QData一体机交易历史备库2026年Q2季度4月第三次巡检报告
QData一体机业务整合备库2026年Q2季度4月第三次巡检报告
QData一体机余额宝备库2026年Q2季度4月第三次巡检报告
```

可以这样分类：

```bash
filesort ~/reports --by-pattern 'QData一体机(.+?)\d{4}年.*'
```

### 4. 保存常用预设

保存一个常用正则策略：

```bash
filesort ~/reports --by-pattern 'QData一体机(.+?)\d{4}年.*' --save-preset qdata-db
```

之后在任意目标目录复用：

```bash
filesort ~/reports --preset qdata-db
```

查看和删除：

```bash
filesort presets list
filesort presets remove qdata-db
```

说明：

- 预设只保存整理策略和参数
- 不保存目标目录路径

### 5. 设置全局扩展名分组

设置后，平时执行 `-t` 时会自动生效。

```bash
filesort --set-type-group images=jpg,jpeg,png,gif
filesort --set-type-group docs=pdf,doc,docx
```

之后直接：

```bash
filesort ~/Downloads -t
```

比如：

- `jpg`, `jpeg`, `png`, `gif` 会进入 `images/`
- `pdf`, `doc`, `docx` 会进入 `docs/`
- 其他未映射扩展名仍按原扩展名分类，如 `mp4 -> mp4/`

查看和删除：

```bash
filesort groups list
filesort groups remove images
```

本次临时忽略全局分组：

```bash
filesort ~/Downloads -t --no-type-groups
```

### 6. 统一查看配置

```bash
filesort --list presets
filesort --list type-groups
filesort --list all
```

旧参数仍然可用：

```bash
filesort --list-preset
filesort --remove-preset qdata-db
filesort --list-type-groups
filesort --remove-type-group images
```

### 7. 启用 Tab 补全

PowerShell 当前会话：

```powershell
python filesort completion powershell | Out-String | Invoke-Expression
```

bash 当前会话：

```bash
source <(python filesort completion bash)
```

zsh 当前会话：

```zsh
source <(python filesort completion zsh)
```

## 撤销整理

```bash
filesort ~/Downloads --undo
```

当前撤销机制支持：

- 恢复上一次整理移动的文件
- 自动清理空分类目录
- 如果部分文件回滚失败，会保留剩余记录，修复后可再次执行 `--undo`

## 配置文件位置

程序会把预设和扩展名分组保存在同一个配置文件中。

- Windows: `%APPDATA%\filesort\presets.json`
- Linux: `$XDG_CONFIG_HOME/filesort/presets.json`
- 如果未设置 `XDG_CONFIG_HOME`，则使用 `~/.config/filesort/presets.json`

也可以通过环境变量覆盖：

```bash
FILESORT_PRESETS_FILE=/path/to/presets.json
```

## 错误处理

- 无效正则不会抛出 Python traceback，而是返回清晰的错误提示
- 非法分类目录名会被自动净化
- 扩展名分组冲突会直接报错，避免不确定行为

## 适合的场景

- 下载目录初步整理
- 报告、截图、导出文件按规则归档
- 使用固定命名格式的批量文件整理
- 想要“配置一次，之后直接运行”的个人工作流

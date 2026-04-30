import os
import shutil
import sys

from organizer.strategies import (
    StrategyError,
    by_date,
    by_type,
    by_pattern,
    by_rules,
)
from organizer.undo import save_operation


INVALID_CATEGORY_CHARS = '<>:"/\\|?*'


def _scan_files(target_dir):
    """Return a sorted list of regular file paths in target_dir.
    Only scans the selected directory and skips subdirectories, hidden files,
    and the log file itself."""
    files = []
    for entry in os.listdir(target_dir):
        if entry.startswith("."):
            continue
        full = os.path.join(target_dir, entry)
        if os.path.isfile(full):
            files.append(full)
    return sorted(files)


def _resolve_conflict(dest_path):
    """If dest_path already exists, append (1), (2), etc. before the extension."""
    if not os.path.exists(dest_path):
        return dest_path
    base, ext = os.path.splitext(dest_path)
    counter = 1
    while True:
        new_path = f"{base}({counter}){ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def _normalize_category_name(category):
    """Convert strategy output into a safe single-directory category name."""
    text = str(category).strip()
    if not text:
        return "uncategorized"

    normalized = []
    previous_was_separator = False
    for char in text:
        if char.isspace():
            replacement = " "
        elif char in INVALID_CATEGORY_CHARS or ord(char) < 32:
            replacement = "_"
        else:
            replacement = char

        is_separator = replacement in {" ", "_"}
        if is_separator and previous_was_separator:
            continue
        normalized.append(replacement)
        previous_was_separator = is_separator

    safe_name = "".join(normalized).strip(" ._")
    if safe_name in {"", ".", ".."}:
        return "uncategorized"
    return safe_name


def _print_preview(groups, target_dir):
    """Print a preview of what would be moved."""
    total = sum(len(v) for v in groups.values())
    print(f"\nTarget: {target_dir}")
    print(f"Files to organize: {total}")
    print(f"Categories to create: {len(groups)}\n")
    for category, file_list in sorted(groups.items()):
        print(f"  [{category}] ({len(file_list)} file(s))")
        for f in file_list:
            print(f"    {os.path.basename(f)} -> {category}/")
    print()


def _execute_moves(groups, target_dir):
    """Execute file moves and return the move log entries."""
    moves_log = []
    for category, file_list in groups.items():
        cat_dir = os.path.join(target_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        for src in file_list:
            base_name = os.path.basename(src)
            dest = _resolve_conflict(os.path.join(cat_dir, base_name))
            try:
                shutil.move(src, dest)
                rel_src = os.path.relpath(src, target_dir)
                rel_dest = os.path.relpath(dest, target_dir)
                moves_log.append({"source": rel_src, "dest": rel_dest})
            except OSError as e:
                print(f"  Error moving {base_name}: {e}", file=sys.stderr)
    return moves_log


def organize(target_dir, strategy_name, strategy_args, execute=False):
    """Main entry point for file organization.

    Args:
        target_dir: Path to the directory to organize.
        strategy_name: One of 'by_date', 'by_type', 'by_pattern', 'by_rules'.
        strategy_args: Dict of keyword arguments for the strategy function.
        execute: If True, skip preview and confirmation.
    """
    target_dir = os.path.abspath(target_dir)

    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    files = _scan_files(target_dir)
    if not files:
        print(f"No files to organize in '{target_dir}'.")
        return

    # Dispatch to the selected strategy
    strategies = {
        "by_date": by_date,
        "by_type": by_type,
        "by_pattern": by_pattern,
        "by_rules": by_rules,
    }
    strategy_fn = strategies[strategy_name]
    try:
        raw_groups = strategy_fn(files, **strategy_args)
    except StrategyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    groups = {}
    for raw_category, file_list in raw_groups.items():
        category = _normalize_category_name(raw_category)
        groups.setdefault(category, []).extend(file_list)

    # Filter: skip files already in their target category directory
    filtered = {}
    for category, file_list in groups.items():
        kept = [
            f for f in file_list
            if os.path.relpath(os.path.dirname(f), target_dir) != category
        ]
        if kept:
            filtered[category] = kept

    if not filtered:
        print("All files are already organized. Nothing to do.")
        return

    # Preview
    _print_preview(filtered, target_dir)

    if not execute:
        try:
            response = input("Proceed? (y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return
        if response != "y":
            print("Cancelled.")
            return

    # Execute
    moves_log = _execute_moves(filtered, target_dir)
    if moves_log:
        save_operation(target_dir, strategy_name, moves_log)
        print(f"Done: {len(moves_log)} file(s) organized into "
              f"{len(filtered)} categories.")
    else:
        print("No files were moved.")

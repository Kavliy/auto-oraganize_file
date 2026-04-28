import json
import os
import shutil
import sys
from datetime import datetime, timezone

LOG_FILENAME = ".organize_log.json"


def _log_path(target_dir):
    return os.path.join(target_dir, LOG_FILENAME)


def _read_log(target_dir):
    path = _log_path(target_dir)
    if not os.path.isfile(path):
        return {"operations": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"operations": []}


def _write_log(target_dir, log_data):
    path = _log_path(target_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def save_operation(target_dir, strategy_name, moves):
    """Append an operation record to the undo log."""
    target_dir = os.path.abspath(target_dir)
    log_data = _read_log(target_dir)
    log_data.setdefault("operations", []).append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_dir": target_dir,
        "strategy": strategy_name,
        "moves": moves,
    })
    _write_log(target_dir, log_data)


def undo_last(target_dir):
    """Undo the most recent operation recorded in the log.
    Returns True if an operation was undone, False if there was nothing to undo."""
    target_dir = os.path.abspath(target_dir)
    log_data = _read_log(target_dir)

    if not log_data.get("operations"):
        print("Nothing to undo — no previous organization found.", file=sys.stderr)
        return False

    op = log_data["operations"].pop()
    moves = op.get("moves", [])
    created_dirs = set()

    if not moves:
        _write_log(target_dir, log_data)
        print("Undone, but no file moves were recorded in that operation.")
        return True

    failed = []
    # Build set of directories that were created (the parent dir of each dest)
    for m in moves:
        dest_parent = os.path.dirname(os.path.join(target_dir, m["dest"]))
        created_dirs.add(dest_parent)

    for m in moves:
        src = os.path.join(target_dir, m["dest"])
        dst = os.path.join(target_dir, m["source"])
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
        except OSError as e:
            failed.append((m["dest"], str(e)))

    # Remove empty category directories
    for d in sorted(created_dirs, key=lambda x: -len(x)):
        try:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
        except OSError:
            pass

    _write_log(target_dir, log_data)

    if failed:
        print(f"Undone with {len(failed)} error(s):", file=sys.stderr)
        for path, err in failed:
            print(f"  {path}: {err}", file=sys.stderr)
    else:
        print(f"Undone: {len(moves)} file(s) moved back, strategy='{op['strategy']}'.")

    return True

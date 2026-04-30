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
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)


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


def _build_operation_record(op, moves):
    """Copy an operation record while replacing the move list."""
    updated = dict(op)
    updated["moves"] = moves
    return updated


def _format_failure(move, message):
    return f"{move['dest']} -> {move['source']}: {message}"


def undo_last(target_dir):
    """Undo the most recent operation recorded in the log.
    Returns True if at least one file was restored, False otherwise."""
    target_dir = os.path.abspath(target_dir)
    log_data = _read_log(target_dir)

    if not log_data.get("operations"):
        print("Nothing to undo - no previous organization found.", file=sys.stderr)
        return False

    op = log_data["operations"][-1]
    moves = op.get("moves", [])
    created_dirs = set()

    if not moves:
        log_data["operations"].pop()
        _write_log(target_dir, log_data)
        print("Undone, but no file moves were recorded in that operation.")
        return True

    failed = []
    restored = 0

    # Track target directories so we can clean up any empty ones after restore.
    for move in moves:
        dest_parent = os.path.dirname(os.path.join(target_dir, move["dest"]))
        created_dirs.add(dest_parent)

    for move in moves:
        src = os.path.join(target_dir, move["dest"])
        dst = os.path.join(target_dir, move["source"])

        if not os.path.exists(src):
            failed.append((move, "moved file is missing from its organized location"))
            continue

        if os.path.exists(dst):
            failed.append((move, "original path already exists"))
            continue

        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            restored += 1
        except OSError as e:
            failed.append((move, str(e)))

    for directory in sorted(created_dirs, key=lambda value: -len(value)):
        try:
            if os.path.isdir(directory) and not os.listdir(directory):
                os.rmdir(directory)
        except OSError:
            pass

    if failed:
        log_data["operations"][-1] = _build_operation_record(
            op,
            [move for move, _ in failed],
        )
        _write_log(target_dir, log_data)
        print(
            f"Undo partially completed: restored {restored} file(s), "
            f"{len(failed)} file(s) still pending.",
            file=sys.stderr,
        )
        print("Resolve the issues below and run --undo again:", file=sys.stderr)
        for move, error in failed:
            print(f"  {_format_failure(move, error)}", file=sys.stderr)
        return restored > 0

    log_data["operations"].pop()
    _write_log(target_dir, log_data)
    print(f"Undone: {len(moves)} file(s) moved back, strategy='{op['strategy']}'.")
    return True

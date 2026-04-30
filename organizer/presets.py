import json
import os

PRESETS_ENV_VAR = "FILESORT_PRESETS_FILE"


class PresetError(ValueError):
    """Raised when preset storage or preset input is invalid."""


def _default_config_dir():
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            return appdata
        return os.path.join(os.path.expanduser("~"), "AppData", "Roaming")

    return os.getenv("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"),
        ".config",
    )


def preset_store_path():
    override = os.getenv(PRESETS_ENV_VAR)
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(_default_config_dir(), "filesort", "presets.json")


def _read_store(path):
    if not os.path.isfile(path):
        return {"presets": {}}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise PresetError(f"Could not read preset store '{path}': {e}") from e

    presets = data.get("presets")
    if not isinstance(presets, dict):
        raise PresetError(f"Preset store '{path}' is invalid.")
    return data


def _write_store(path, data):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(temp_path, path)


def _normalize_preset_name(name):
    normalized = str(name).strip()
    if not normalized:
        raise PresetError("Preset name cannot be empty.")
    return normalized


def save_preset(name, strategy_name, strategy_args):
    """Save or update a preset and return its storage path plus overwrite state."""
    preset_name = _normalize_preset_name(name)
    path = preset_store_path()
    data = _read_store(path)
    presets = data.setdefault("presets", {})
    existed = preset_name in presets
    presets[preset_name] = {
        "strategy": strategy_name,
        "strategy_args": dict(strategy_args),
    }
    _write_store(path, data)
    return path, existed


def load_preset(name):
    """Load a preset and return its strategy name and args."""
    preset_name = _normalize_preset_name(name)
    path = preset_store_path()
    data = _read_store(path)
    preset = data.get("presets", {}).get(preset_name)
    if preset is None:
        raise PresetError(f"Preset '{preset_name}' was not found.")

    strategy_name = preset.get("strategy")
    strategy_args = preset.get("strategy_args", {})
    if not isinstance(strategy_name, str) or not isinstance(strategy_args, dict):
        raise PresetError(f"Preset '{preset_name}' is invalid.")

    return strategy_name, strategy_args

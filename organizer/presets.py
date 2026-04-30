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
        return {
            "presets": {},
            "type_groups": {},
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise PresetError(f"Could not read preset store '{path}': {e}") from e

    presets = data.get("presets", {})
    type_groups = data.get("type_groups", {})
    if not isinstance(presets, dict) or not isinstance(type_groups, dict):
        raise PresetError(f"Preset store '{path}' is invalid.")

    data.setdefault("presets", {})
    data.setdefault("type_groups", {})
    return data


def _write_store(path, data):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(temp_path, path)


def _normalize_name(name, label):
    normalized = str(name).strip()
    if not normalized:
        raise PresetError(f"{label} cannot be empty.")
    return normalized


def _normalize_extension(extension):
    normalized = str(extension).strip().lower().lstrip(".")
    if not normalized:
        raise PresetError("Extension names cannot be empty.")
    if any(char.isspace() for char in normalized) or "," in normalized or "=" in normalized:
        raise PresetError(f"Invalid extension '{extension}'.")
    return normalized


def _normalize_extension_list(extensions):
    normalized = []
    seen = set()
    for extension in extensions:
        value = _normalize_extension(extension)
        if value in seen:
            continue
        normalized.append(value)
        seen.add(value)
    if not normalized:
        raise PresetError("Type groups must include at least one extension.")
    return normalized


def _normalize_type_groups(groups):
    if groups is None:
        return {}
    if not isinstance(groups, dict):
        raise PresetError("Type groups are invalid.")

    normalized = {}
    owners = {}
    for name, extensions in groups.items():
        group_name = _normalize_name(name, "Type group name")
        if not isinstance(extensions, list):
            raise PresetError(f"Type group '{group_name}' is invalid.")

        normalized_extensions = _normalize_extension_list(extensions)
        for extension in normalized_extensions:
            owner = owners.get(extension)
            if owner and owner != group_name:
                raise PresetError(
                    f"Extension '{extension}' is already assigned to type group '{owner}'."
                )
            owners[extension] = group_name
        normalized[group_name] = normalized_extensions

    return normalized


def save_preset(name, strategy_name, strategy_args):
    """Save or update a preset and return its storage path plus overwrite state."""
    preset_name = _normalize_name(name, "Preset name")
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
    preset_name = _normalize_name(name, "Preset name")
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


def load_type_groups():
    """Return the configured type-group mapping."""
    path = preset_store_path()
    data = _read_store(path)
    return _normalize_type_groups(data.get("type_groups", {}))


def save_type_group(name, extensions):
    """Save or update one type group and return its storage path plus overwrite state."""
    group_name = _normalize_name(name, "Type group name")
    normalized_extensions = _normalize_extension_list(extensions)

    path = preset_store_path()
    data = _read_store(path)
    type_groups = _normalize_type_groups(data.get("type_groups", {}))
    existed = group_name in type_groups
    type_groups[group_name] = normalized_extensions
    data["type_groups"] = _normalize_type_groups(type_groups)
    _write_store(path, data)
    return path, existed


def remove_type_group(name):
    """Remove one type group and return the storage path."""
    group_name = _normalize_name(name, "Type group name")
    path = preset_store_path()
    data = _read_store(path)
    type_groups = _normalize_type_groups(data.get("type_groups", {}))
    if group_name not in type_groups:
        raise PresetError(f"Type group '{group_name}' was not found.")

    del type_groups[group_name]
    data["type_groups"] = type_groups
    _write_store(path, data)
    return path

import os
import re
from datetime import datetime


class StrategyError(ValueError):
    """Raised when a strategy receives invalid user input."""


def by_date(files, fmt="%Y-%m"):
    """Group files by modification date using the given strftime format."""
    groups = {}
    for filepath in files:
        mtime = os.path.getmtime(filepath)
        category = datetime.fromtimestamp(mtime).strftime(fmt)
        groups.setdefault(category, []).append(filepath)
    return groups


def _build_type_group_lookup(type_groups):
    if type_groups is None:
        return {}
    if not isinstance(type_groups, dict):
        raise StrategyError("Type-group configuration is invalid.")

    lookup = {}
    for category, extensions in type_groups.items():
        if not isinstance(extensions, list):
            raise StrategyError(f"Type group '{category}' is invalid.")
        for extension in extensions:
            normalized = str(extension).strip().lower().lstrip(".")
            if not normalized:
                raise StrategyError(f"Type group '{category}' contains an empty extension.")
            owner = lookup.get(normalized)
            if owner and owner != category:
                raise StrategyError(
                    f"Extension '{normalized}' is assigned to multiple type groups."
                )
            lookup[normalized] = category
    return lookup


def by_type(files, type_groups=None):
    """Group files by their extension, with optional extension-to-group mapping."""
    extension_lookup = _build_type_group_lookup(type_groups)
    groups = {}
    for filepath in files:
        _, ext = os.path.splitext(filepath)
        normalized = ext.lstrip(".").lower()
        if normalized:
            category = extension_lookup.get(normalized, normalized)
        else:
            category = "no_extension"
        groups.setdefault(category, []).append(filepath)
    return groups


def by_pattern(files, pattern):
    """Group files by a regex pattern. Capture group 1 determines the category.
    Unmatched files go to 'uncategorized'."""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        raise StrategyError(f"Invalid regex pattern for --by-pattern: {e}") from e
    groups = {}
    for filepath in files:
        filename = os.path.basename(filepath)
        m = regex.match(filename)
        category = m.group(1) if m else "uncategorized"
        groups.setdefault(category, []).append(filepath)
    return groups


def by_rules(files, rules_file):
    """Custom rules-based classification. Not yet implemented."""
    raise NotImplementedError(
        "Custom rules (--rules) is planned but not yet implemented."
    )

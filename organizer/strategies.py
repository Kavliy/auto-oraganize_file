import os
import re
from datetime import datetime


def by_date(files, fmt="%Y-%m"):
    """Group files by modification date using the given strftime format."""
    groups = {}
    for filepath in files:
        mtime = os.path.getmtime(filepath)
        category = datetime.fromtimestamp(mtime).strftime(fmt)
        groups.setdefault(category, []).append(filepath)
    return groups


def by_type(files):
    """Group files by their extension (lowercased, without dot)."""
    groups = {}
    for filepath in files:
        _, ext = os.path.splitext(filepath)
        category = ext.lstrip(".").lower() if ext else "no_extension"
        groups.setdefault(category, []).append(filepath)
    return groups


def by_pattern(files, pattern):
    """Group files by a regex pattern. Capture group 1 determines the category.
    Unmatched files go to 'uncategorized'."""
    regex = re.compile(pattern)
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

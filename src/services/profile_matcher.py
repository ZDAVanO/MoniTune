"""
Profile matching service for MoniTune.
Resolves active process executable paths against configured profiles
(exact executable match or deepest parent directory match) and checks
for ignored processes (transient/tray apps that shouldn't deactivate profiles).
"""

import os
import logging
from typing import Any, Dict, Iterable, Optional, Tuple

logger = logging.getLogger(__name__)


def _extract_profile_data(data: Any) -> Tuple[bool, Dict[str, int]]:
    """
    Extracts (is_enabled, brightness_data) from profile data.
    Supports both legacy format:
        {"DISPLAY1": 80}
    and structured format:
        {"enabled": True, "brightness_data": {"DISPLAY1": 80}}
    """
    if not isinstance(data, dict):
        return False, {}

    if "brightness_data" in data and isinstance(data["brightness_data"], dict):
        return bool(data.get("enabled", True)), data["brightness_data"]

    # Legacy format: data itself is the brightness dictionary
    is_enabled = bool(data.get("enabled", True))
    br_data = {k: v for k, v in data.items() if k != "enabled" and isinstance(v, (int, float))}
    return is_enabled, br_data


def match_profile(
    profiles_data: Dict[str, Any],
    exe_path: str
) -> Tuple[Optional[str], Optional[Dict[str, int]]]:
    """
    Finds the best matching profile for an executable path.

    Lookup strategy:
    1. Exact match on normalized executable path (case-insensitive on Windows).
       If an exact match exists and is disabled, returns (None, None).
    2. Deepest parent directory match (prefers the most specific folder path).
       If the deepest matching rule is disabled, returns (None, None).

    Returns:
        (matched_key, brightness_dict) or (None, None) if no match found or disabled.
    """
    if not profiles_data or not exe_path:
        return None, None

    exe_path_norm = os.path.normcase(os.path.normpath(exe_path))

    # 1. Exact match (check raw key first for performance, then normalized)
    if exe_path in profiles_data:
        enabled, br_dict = _extract_profile_data(profiles_data[exe_path])
        return (exe_path, br_dict) if enabled else (None, None)

    for key, data in profiles_data.items():
        if os.path.normcase(os.path.normpath(key)) == exe_path_norm:
            enabled, br_dict = _extract_profile_data(data)
            return (key, br_dict) if enabled else (None, None)

    # 2. Parent folder match: prefer the longest / deepest matching directory
    best_match_key = None
    best_match_len = -1
    best_match_data = None

    for key, data in profiles_data.items():
        key_norm = os.path.normcase(os.path.normpath(key))
        # Ensure trailing separator so we match full folder boundaries
        folder = key_norm if key_norm.endswith(os.sep) else key_norm + os.sep

        if exe_path_norm.startswith(folder):
            if len(folder) > best_match_len:
                best_match_len = len(folder)
                best_match_key = key
                best_match_data = data

    if best_match_key is not None:
        enabled, br_dict = _extract_profile_data(best_match_data)
        if enabled:
            return best_match_key, br_dict
        return None, None

    return None, None


def is_ignored_process(
    ignored_patterns: Optional[Iterable[str]],
    exe_path: Optional[str]
) -> bool:
    """
    Checks if an executable path matches any pattern in ignored_patterns.

    Matching strategy:
    1. Filename / base process name match (e.g. 'EarTrumpet.exe' or 'EarTrumpet').
    2. Exact normalized path match.
    3. Parent directory match (e.g. 'C:\\Program Files\\WindowsApps').

    Returns:
        True if exe_path matches any ignored pattern, False otherwise.
    """
    if not ignored_patterns or not exe_path:
        return False

    exe_path_norm = os.path.normcase(os.path.normpath(exe_path))
    exe_name = os.path.basename(exe_path_norm)

    for pattern in ignored_patterns:
        if not pattern:
            continue
        cleaned = pattern.strip().strip('"').strip("'")
        if not cleaned:
            continue

        # Single filename / process name without directory separators
        if os.sep not in cleaned and "/" not in cleaned:
            pat_norm = os.path.normcase(cleaned)
            if pat_norm == exe_name or f"{pat_norm}.exe" == exe_name:
                return True
            continue

        # Full path or directory path
        pat_norm = os.path.normcase(os.path.normpath(cleaned))
        if pat_norm == exe_path_norm:
            return True

        folder = pat_norm if pat_norm.endswith(os.sep) else pat_norm + os.sep
        if exe_path_norm.startswith(folder):
            return True

    return False


"""
Profile matching service for MoniTune.
Resolves active process executable paths against configured profiles
(exact executable match or deepest parent directory match).
"""

import os
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def match_profile(
    profiles_data: Dict[str, Any],
    exe_path: str
) -> Tuple[Optional[str], Optional[Dict[str, int]]]:
    """
    Finds the best matching profile for an executable path.

    Lookup strategy:
    1. Exact match on normalized executable path (case-insensitive on Windows).
    2. Deepest parent directory match (prefers the most specific folder path).

    Returns:
        (matched_key, brightness_dict) or (None, None) if no match found.
    """
    if not profiles_data or not exe_path:
        return None, None

    exe_path_norm = os.path.normcase(os.path.normpath(exe_path))

    # 1. Exact match (check raw key first for performance, then normalized)
    if exe_path in profiles_data:
        return exe_path, profiles_data[exe_path]

    for key, data in profiles_data.items():
        if os.path.normcase(os.path.normpath(key)) == exe_path_norm:
            return key, data

    # 2. Parent folder match: prefer the longest / deepest matching directory
    best_match_key = None
    best_match_len = -1

    for key, data in profiles_data.items():
        key_norm = os.path.normcase(os.path.normpath(key))
        # Ensure trailing separator so we match full folder boundaries
        folder = key_norm if key_norm.endswith(os.sep) else key_norm + os.sep

        if exe_path_norm.startswith(folder):
            if len(folder) > best_match_len:
                best_match_len = len(folder)
                best_match_key = key

    if best_match_key is not None:
        return best_match_key, profiles_data[best_match_key]

    return None, None

"""
Migration script for MoniTune monitor settings in the Windows Registry.

Automatically identifies connected displays (laptop screen vs external displays)
after driver reinstallations or GPU changes, matches them to previous configurations,
and updates registry keys (names, layout order, brightness schedules, profiles, etc.).
"""

import argparse
import datetime
import json
import logging
import os
import subprocess
import sys
import time
import winreg
from pathlib import Path

# Add 'src' to python path to access existing utilities
REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import psutil
import screen_brightness_control as sbc
from utils import monitor_utils, reg_utils
import config as cfg

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MonitorMigration")


def is_laptop_display(sbc_info, monitor_obj=None) -> bool:
    """Determine if a monitor is a built-in laptop screen."""
    # Check method
    method = ""
    if monitor_obj:
        method = monitor_obj.method
    elif sbc_info and "method" in sbc_info:
        method = str(sbc_info["method"])

    if "WMI" in method:
        return True

    # Check serial / UID pattern
    serial = ""
    if monitor_obj:
        serial = str(monitor_obj.serial or "")
    elif sbc_info:
        serial = str(sbc_info.get("serial") or "")

    if "UID" in serial.upper() and ("&" in serial or serial.startswith("5&")):
        return True

    # Check manufacturer
    mfg_id = ""
    if sbc_info:
        mfg_id = str(sbc_info.get("manufacturer_id") or "").upper()
    if mfg_id in ["CMN", "BOE", "AUO", "LGD", "SHP", "CSO"]:
        return True

    return False


def get_current_displays():
    """Returns detected active displays with metadata."""
    monitors = monitor_utils.get_monitors()
    displays = []
    for m in monitors:
        sbc_match = None
        for s in sbc.list_monitors_info():
            if s.get("serial") == m.serial or s.get("name") == m.name:
                sbc_match = s
                break

        is_laptop = is_laptop_display(sbc_match, m)
        display_type = "Laptop Display" if is_laptop else "External Monitor"
        displays.append({
            "index": m.index,
            "serial": str(m.serial),
            "name": m.name,
            "model": m.model,
            "manufacturer": m.manufacturer,
            "method": m.method,
            "is_laptop": is_laptop,
            "display_type": display_type,
            "resolution": f"{m.resolution[0]}x{m.resolution[1]}" if m.resolution else "Unknown",
            "refresh_rate": f"{m.refresh_rate}Hz" if m.refresh_rate else "Unknown",
        })
    return displays


def read_registry_settings():
    """Reads all monitor-related settings from MoniTune registry key."""
    settings = {
        "CustomMonitorNames": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "CustomMonitorNames"),
        "MonitorsOrder": reg_utils.reg_read_list(cfg.REGISTRY_PATH, "MonitorsOrder"),
        "HiddenDisplays": reg_utils.reg_read_list(cfg.REGISTRY_PATH, "HiddenDisplays"),
        "ExcludedHzRates": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "ExcludedHzRates"),
        "BrightnessValues": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "BrightnessValues"),
        "ManualBrightnessValues": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "ManualBrightnessValues"),
        "ContrastValues": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "ContrastValues"),
        "TimeAdjustmentData": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "TimeAdjustmentData"),
        "ProfilesData": reg_utils.reg_read_dict(cfg.REGISTRY_PATH, "ProfilesData"),
    }
    return settings


def backup_registry_settings(settings, backup_dir=None):
    """Creates a timestamped JSON backup file and registry backup key."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_dir is None:
        backup_dir = REPO_ROOT / "backups"
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = Path(backup_dir) / f"monitune_backup_{timestamp}.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    # Also save to registry backup key
    backup_reg_path = f"{cfg.REGISTRY_PATH}_Backup_{timestamp}"
    reg_utils.create_reg_key(backup_reg_path)
    for key, val in settings.items():
        if isinstance(val, dict):
            reg_utils.reg_write_dict(backup_reg_path, key, val)
        elif isinstance(val, list):
            reg_utils.reg_write_list(backup_reg_path, key, val)

    logger.info(f"Registry backup created at: {backup_file}")
    logger.info(f"Registry backup key created at: HKCU\\{backup_reg_path}")
    return backup_file


def collect_registry_serials(settings):
    """Collects all monitor serials present across registry settings with metadata."""
    serials_info = {}

    def ensure_serial(s):
        s_str = str(s).strip()
        if s_str and s_str not in serials_info:
            serials_info[s_str] = {
                "custom_name": None,
                "in_order": False,
                "in_time_adj": False,
                "in_manual_brightness": False,
                "in_excluded_hz": False,
                "in_contrast": False,
                "in_brightness_values": False,
                "is_laptop_hint": False,
                "score": 0,
            }
        return s_str

    for s, name in settings.get("CustomMonitorNames", {}).items():
        s_str = ensure_serial(s)
        serials_info[s_str]["custom_name"] = name
        serials_info[s_str]["score"] += 10
        if any(w in str(name).lower() for w in ["laptop", "internal", "built-in", "integrated"]):
            serials_info[s_str]["is_laptop_hint"] = True

    for s in settings.get("MonitorsOrder", []):
        s_str = ensure_serial(s)
        serials_info[s_str]["in_order"] = True
        serials_info[s_str]["score"] += 5

    for time_str, data in settings.get("TimeAdjustmentData", {}).items():
        if isinstance(data, dict):
            for s in data:
                s_str = ensure_serial(s)
                serials_info[s_str]["in_time_adj"] = True
                serials_info[s_str]["score"] += 8

    for s in settings.get("ManualBrightnessValues", {}):
        s_str = ensure_serial(s)
        serials_info[s_str]["in_manual_brightness"] = True
        serials_info[s_str]["score"] += 3

    for s in settings.get("ExcludedHzRates", {}):
        s_str = ensure_serial(s)
        serials_info[s_str]["in_excluded_hz"] = True
        serials_info[s_str]["score"] += 2

    for s in settings.get("ContrastValues", {}):
        s_str = ensure_serial(s)
        serials_info[s_str]["in_contrast"] = True

    for s in settings.get("BrightnessValues", {}):
        s_str = ensure_serial(s)
        serials_info[s_str]["in_brightness_values"] = True
        serials_info[s_str]["score"] += 1

    # Check UID pattern for laptop hint
    for s_str, info in serials_info.items():
        if ("UID" in s_str.upper() and "&" in s_str) or s_str.startswith("5&"):
            info["is_laptop_hint"] = True

    return serials_info


def calculate_migration_mapping(current_displays, reg_serials_info):
    """
    Computes old_serial -> new_serial mapping based on display types and configuration scores.
    """
    current_serials = {d["serial"] for d in current_displays}
    mapping = {}  # old_serial -> new_serial

    # Identify orphaned serials in registry (serials that are not currently connected)
    orphaned = {s: info for s, info in reg_serials_info.items() if s not in current_serials}

    # Match displays
    for display in current_displays:
        new_serial = display["serial"]
        if new_serial in reg_serials_info and reg_serials_info[new_serial]["score"] >= 10:
            # Already configured properly
            continue

        if display["is_laptop"]:
            # Match with best orphaned laptop serial
            laptop_candidates = [
                (s, info) for s, info in orphaned.items()
                if info["is_laptop_hint"] and s not in mapping
            ]
            if laptop_candidates:
                # Sort by configuration score descending
                laptop_candidates.sort(key=lambda x: x[1]["score"], reverse=True)
                best_old_serial, _ = laptop_candidates[0]
                mapping[best_old_serial] = new_serial
        else:
            # Match external displays
            external_candidates = [
                (s, info) for s, info in orphaned.items()
                if not info["is_laptop_hint"] and s not in mapping
            ]
            if external_candidates:
                external_candidates.sort(key=lambda x: x[1]["score"], reverse=True)
                best_old_serial, _ = external_candidates[0]
                mapping[best_old_serial] = new_serial

    return mapping


def apply_mapping_to_settings(settings, mapping, cleanup_stale_brightness=True, active_serials=None):
    """
    Applies the old_serial -> new_serial replacement across all settings dictionaries and lists.
    """
    new_settings = {}

    def replace_serial(s):
        return mapping.get(s, s)

    # 1. CustomMonitorNames: {serial: name}
    custom_names = {}
    for s, val in settings.get("CustomMonitorNames", {}).items():
        custom_names[replace_serial(s)] = val
    new_settings["CustomMonitorNames"] = custom_names

    # 2. MonitorsOrder: [serial1, serial2, ...]
    monitors_order = [replace_serial(s) for s in settings.get("MonitorsOrder", [])]
    # Remove duplicates preserving order
    dedup_order = []
    for s in monitors_order:
        if s not in dedup_order:
            dedup_order.append(s)
    new_settings["MonitorsOrder"] = dedup_order

    # 3. HiddenDisplays: [serial1, serial2, ...]
    hidden = [replace_serial(s) for s in settings.get("HiddenDisplays", [])]
    new_settings["HiddenDisplays"] = list(dict.fromkeys(hidden))

    # 4. ExcludedHzRates: {serial: [rates]}
    excluded_hz = {}
    for s, val in settings.get("ExcludedHzRates", {}).items():
        excluded_hz[replace_serial(s)] = val
    new_settings["ExcludedHzRates"] = excluded_hz

    # 5. ManualBrightnessValues: {serial: int}
    manual_b = {}
    for s, val in settings.get("ManualBrightnessValues", {}).items():
        manual_b[replace_serial(s)] = val
    new_settings["ManualBrightnessValues"] = manual_b

    # 6. ContrastValues: {serial: int}
    contrast = {}
    for s, val in settings.get("ContrastValues", {}).items():
        contrast[replace_serial(s)] = val
    new_settings["ContrastValues"] = contrast

    # 7. TimeAdjustmentData: {time_str: {serial: int}}
    time_adj = {}
    for t_str, subdict in settings.get("TimeAdjustmentData", {}).items():
        if isinstance(subdict, dict):
            new_subdict = {}
            for s, b_val in subdict.items():
                new_subdict[replace_serial(s)] = b_val
            time_adj[t_str] = new_subdict
        else:
            time_adj[t_str] = subdict
    new_settings["TimeAdjustmentData"] = time_adj

    # 8. ProfilesData: {exe_path: {serial: int}}
    profiles = {}
    for exe, subdict in settings.get("ProfilesData", {}).items():
        if isinstance(subdict, dict):
            new_subdict = {}
            for s, b_val in subdict.items():
                new_subdict[replace_serial(s)] = b_val
            profiles[exe] = new_subdict
        else:
            profiles[exe] = subdict
    new_settings["ProfilesData"] = profiles

    # 9. BrightnessValues: {serial: int}
    brightness = {}
    for s, val in settings.get("BrightnessValues", {}).items():
        target = replace_serial(s)
        # If cleanup requested, only keep active serials or mapped targets
        if cleanup_stale_brightness and active_serials:
            if target in active_serials:
                brightness[target] = val
        else:
            brightness[target] = val
    new_settings["BrightnessValues"] = brightness

    return new_settings


def write_registry_settings(new_settings):
    """Writes updated settings dictionaries and lists back into Windows Registry."""
    reg_path = cfg.REGISTRY_PATH
    for key, val in new_settings.items():
        if isinstance(val, dict):
            reg_utils.reg_write_dict(reg_path, key, val)
        elif isinstance(val, list):
            reg_utils.reg_write_list(reg_path, key, val)
    logger.info("Successfully updated MoniTune registry settings.")


def get_running_monitune_processes():
    """Finds all running MoniTune processes."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "exe"]):
        try:
            name = (p.info["name"] or "").lower()
            if "monitune" in name and not name.endswith(".py"):
                procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs


def stop_monitune(procs):
    """Terminates running MoniTune processes."""
    for p in procs:
        try:
            logger.info(f"Terminating MoniTune process (PID {p.pid})...")
            p.terminate()
            p.wait(timeout=3)
        except Exception as e:
            try:
                p.kill()
            except Exception:
                pass


def restart_monitune(exe_path):
    """Relaunches MoniTune executable using os.startfile on Windows."""
    target = exe_path if (exe_path and os.path.exists(exe_path)) else (REPO_ROOT / "dist" / "MoniTune.exe")
    if os.path.exists(str(target)):
        logger.info(f"Relaunching MoniTune from: {target}")
        if sys.platform == "win32":
            os.startfile(str(target))
        else:
            subprocess.Popen([str(target)], cwd=str(Path(target).parent))
    else:
        logger.warning("Could not locate MoniTune.exe to relaunch.")


def run_migration(apply_changes=False, restart_app=False, manual_map=None):
    print("=" * 60)
    print("       MoniTune Display Settings Migration Tool")
    print("=" * 60)

    # 1. Detect currently active monitors
    displays = get_current_displays()
    print(f"\n[+] Currently Connected Displays ({len(displays)}):")
    for d in displays:
        print(f"    - Index {d['index']}: {d['display_type']}")
        print(f"      Serial:       {d['serial']}")
        print(f"      Name:         {d['name']} (Model: {d['model']}, Mfg: {d['manufacturer']})")
        print(f"      Method:       {d['method']} ({d['resolution']} @ {d['refresh_rate']})")

    # 2. Read registry settings
    current_settings = read_registry_settings()
    reg_serials_info = collect_registry_serials(current_settings)
    print(f"\n[+] Displays Found in Registry ({len(reg_serials_info)}):")
    for s, info in reg_serials_info.items():
        status = "CONNECTED" if any(d["serial"] == s for d in displays) else "DISCONNECTED"
        custom_name_str = f" ('{info['custom_name']}')" if info['custom_name'] else ""
        laptop_hint = " [Laptop Screen]" if info['is_laptop_hint'] else " [External]"
        print(f"    - {s}{custom_name_str}{laptop_hint} -> Status: {status} (Config score: {info['score']})")

    # 3. Determine migration mapping
    if manual_map:
        mapping = manual_map
    else:
        mapping = calculate_migration_mapping(displays, reg_serials_info)

    if not mapping:
        print("\n[*] No migration required: All connected displays match your registry settings.")
        return

    print("\n[+] Proposed Migration Mapping:")
    for old_s, new_s in mapping.items():
        old_name = reg_serials_info.get(old_s, {}).get("custom_name") or "Unnamed"
        print(f"    OLD: {old_s} ('{old_name}')")
        print(f"     --> NEW: {new_s}")

    # 4. Generate updated settings
    active_serials = {d["serial"] for d in displays}
    new_settings = apply_mapping_to_settings(
        current_settings, mapping, cleanup_stale_brightness=True, active_serials=active_serials
    )

    print("\n[+] Preview of Changes:")
    print("    - MonitorsOrder:")
    print(f"        Before: {current_settings['MonitorsOrder']}")
    print(f"        After:  {new_settings['MonitorsOrder']}")
    print("    - CustomMonitorNames:")
    print(f"        Before: {current_settings['CustomMonitorNames']}")
    print(f"        After:  {new_settings['CustomMonitorNames']}")
    print("    - TimeAdjustmentData:")
    print(f"        Before timestamps: {list(current_settings['TimeAdjustmentData'].keys())}")
    for t in list(new_settings['TimeAdjustmentData'].keys())[:2]:
        print(f"        Sample ({t}): {new_settings['TimeAdjustmentData'][t]}")
    print("    - ManualBrightnessValues:")
    print(f"        Before: {current_settings['ManualBrightnessValues']}")
    print(f"        After:  {new_settings['ManualBrightnessValues']}")
    print("    - BrightnessValues (Cleaned up):")
    print(f"        Before: {current_settings['BrightnessValues']}")
    print(f"        After:  {new_settings['BrightnessValues']}")

    # 5. Check running MoniTune processes
    running_procs = get_running_monitune_processes()
    exe_path = running_procs[0].info["exe"] if running_procs else None

    if not apply_changes:
        print("\n[!] DRY RUN MODE: No changes were written to the registry.")
        print("    To apply these changes, run with: --apply")
        if running_procs:
            print(f"    Notice: MoniTune.exe is currently running (PIDs: {[p.pid for p in running_procs]}).")
            print("    Add --restart to automatically stop and restart MoniTune during migration.")
        return

    # If applying:
    if running_procs:
        if restart_app:
            logger.info("Stopping running MoniTune instance before applying registry changes...")
            stop_monitune(running_procs)
            time.sleep(0.5)
        else:
            logger.warning(
                "MoniTune is currently running! Modifying the registry while MoniTune is active may cause "
                "settings to be overwritten upon MoniTune exit. Please close MoniTune or pass --restart."
            )

    # Backup first
    backup_file = backup_registry_settings(current_settings)

    # Write changes
    write_registry_settings(new_settings)
    print("\n[SUCCESS] Migration applied successfully!")

    # Restart if requested
    if restart_app and exe_path:
        restart_monitune(exe_path)


def main():
    parser = argparse.ArgumentParser(description="Migrate MoniTune display settings in Windows Registry.")
    parser.add_argument("--apply", action="store_true", help="Apply changes to the registry (default is dry-run)")
    parser.add_argument("--restart", action="store_true", help="Automatically close and restart MoniTune if running")
    parser.add_argument("--from-serial", type=str, help="Explicit old monitor serial to replace")
    parser.add_argument("--to-serial", type=str, help="Explicit new monitor serial to replace with")
    parser.add_argument("--backup-only", action="store_true", help="Only create a backup of current registry settings")
    args = parser.parse_args()

    if args.backup_only:
        settings = read_registry_settings()
        backup_registry_settings(settings)
        return

    manual_map = None
    if args.from_serial and args.to_serial:
        manual_map = {args.from_serial: args.to_serial}

    run_migration(apply_changes=args.apply, restart_app=args.restart, manual_map=manual_map)


if __name__ == "__main__":
    main()

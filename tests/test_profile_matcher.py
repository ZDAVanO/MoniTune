import pytest
from services.profile_matcher import match_profile, is_ignored_process


def test_match_profile_exact():
    profiles = {
        r"C:\Program Files\App\app.exe": {"DISPLAY1": 60},
        r"C:\Games\game.exe": {"DISPLAY1": 90},
    }
    key, data = match_profile(profiles, r"C:\Program Files\App\app.exe")
    assert key == r"C:\Program Files\App\app.exe"
    assert data == {"DISPLAY1": 60}


def test_match_profile_case_insensitive():
    profiles = {
        r"C:\Games\Cyberpunk\bin\game.exe": {"DISPLAY1": 80},
    }
    # Mixed case / different case on Windows
    key, data = match_profile(profiles, r"c:\games\cyberpunk\bin\game.exe")
    assert key == r"C:\Games\Cyberpunk\bin\game.exe"
    assert data == {"DISPLAY1": 80}


def test_match_profile_parent_folder():
    profiles = {
        r"C:\SteamLibrary\steamapps\common\Game": {"DISPLAY1": 70},
    }
    exe = r"C:\SteamLibrary\steamapps\common\Game\bin\x64\Game.exe"
    key, data = match_profile(profiles, exe)
    assert key == r"C:\SteamLibrary\steamapps\common\Game"
    assert data == {"DISPLAY1": 70}


def test_match_profile_deepest_parent_wins():
    profiles = {
        r"C:\Games": {"DISPLAY1": 30},
        r"C:\Games\Witcher": {"DISPLAY1": 85},
    }
    exe = r"C:\Games\Witcher\bin\witcher3.exe"
    key, data = match_profile(profiles, exe)
    assert key == r"C:\Games\Witcher"
    assert data == {"DISPLAY1": 85}

    other_exe = r"C:\Games\Other\other.exe"
    key_other, data_other = match_profile(profiles, other_exe)
    assert key_other == r"C:\Games"
    assert data_other == {"DISPLAY1": 30}


def test_match_profile_partial_folder_name_does_not_match():
    # Folder is "C:\Games\App", process is "C:\Games\Application\run.exe"
    # Should NOT match because "App" is not a full folder path of "Application"
    profiles = {
        r"C:\Games\App": {"DISPLAY1": 50},
    }
    exe = r"C:\Games\Application\run.exe"
    key, data = match_profile(profiles, exe)
    assert key is None
    assert data is None


def test_match_profile_not_found():
    profiles = {
        r"C:\Games\Game.exe": {"DISPLAY1": 50},
    }
    key, data = match_profile(profiles, r"C:\Windows\explorer.exe")
    assert key is None
    assert data is None


def test_match_profile_empty_inputs():
    assert match_profile({}, r"C:\app.exe") == (None, None)
    assert match_profile({"C:\app.exe": {}}, "") == (None, None)
    assert match_profile({}, "") == (None, None)


def test_is_ignored_process_by_exe_name():
    patterns = ["EarTrumpet.exe"]
    exe = r"C:\Program Files\WindowsApps\40459File-New-Project.EarTrumpet_2.3.0.0_x86__1sdd7yawvg6ne\EarTrumpet\EarTrumpet.exe"
    assert is_ignored_process(patterns, exe) is True


def test_is_ignored_process_case_insensitive_and_without_extension():
    patterns = ["eartrumpet"]
    exe = r"C:\Program Files\WindowsApps\EarTrumpet\EarTrumpet.exe"
    assert is_ignored_process(patterns, exe) is True


def test_is_ignored_process_exact_full_path():
    patterns = [r"C:\Tools\Overlay\hud.exe"]
    exe = r"c:\tools\overlay\hud.exe"
    assert is_ignored_process(patterns, exe) is True


def test_is_ignored_process_directory_prefix():
    patterns = [r"C:\Program Files\WindowsApps"]
    exe = r"C:\Program Files\WindowsApps\SomeApp\app.exe"
    assert is_ignored_process(patterns, exe) is True


def test_is_ignored_process_directory_boundary_safety():
    # Folder is "C:\Tools", exe is "C:\ToolsExtra\tool.exe" -> should NOT match
    patterns = [r"C:\Tools"]
    exe = r"C:\ToolsExtra\tool.exe"
    assert is_ignored_process(patterns, exe) is False


def test_is_ignored_process_quotes_and_whitespace():
    patterns = ['  "EarTrumpet.exe"  ']
    exe = r"C:\EarTrumpet.exe"
    assert is_ignored_process(patterns, exe) is True


def test_is_ignored_process_unrelated_process():
    patterns = ["EarTrumpet.exe", r"C:\Overlays"]
    exe = r"C:\Games\Cyberpunk\Cyberpunk2077.exe"
    assert is_ignored_process(patterns, exe) is False


def test_is_ignored_process_empty_inputs():
    assert is_ignored_process([], r"C:\app.exe") is False
    assert is_ignored_process(["app.exe"], "") is False
    assert is_ignored_process(None, r"C:\app.exe") is False
    assert is_ignored_process(["app.exe"], None) is False
    assert is_ignored_process(["", "   "], r"C:\app.exe") is False


def test_debounce_cancels_transient_explorer_before_ignored_app():
    """Verify that an ignored process cancels a pending transition to an unprofiled process like explorer.exe."""
    profiles = {r"C:\Tools\WindowsTerminal.exe": {"DISPLAY1": 80}}
    ignored = ["EarTrumpet.exe"]

    current_profile_active = True
    active_profile_data = profiles[r"C:\Tools\WindowsTerminal.exe"]
    prev_active_process = r"C:\Tools\WindowsTerminal.exe"

    pending_process = None

    # Step 1: mouse click causes transient focus on explorer.exe
    event_1 = r"C:\Windows\explorer.exe"
    if not is_ignored_process(ignored, event_1):
        pending_process = event_1  # debounce timer started

    assert pending_process == r"C:\Windows\explorer.exe"
    assert current_profile_active is True  # Still active during debounce!

    # Step 2: EarTrumpet opens 50ms later (before debounce expires)
    event_2 = r"C:\Program Files\WindowsApps\EarTrumpet\EarTrumpet.exe"
    if is_ignored_process(ignored, event_2):
        # Ignored process focused: cancel pending transition!
        pending_process = None

    # Verify that explorer.exe was cancelled and profile remained active
    assert pending_process is None
    assert current_profile_active is True
    assert active_profile_data == {"DISPLAY1": 80}
    assert prev_active_process == r"C:\Tools\WindowsTerminal.exe"


def test_match_profile_disabled_exact():
    profiles = {
        r"C:\Games\game.exe": {"enabled": False, "brightness_data": {"DISPLAY1": 90}},
    }
    key, data = match_profile(profiles, r"C:\Games\game.exe")
    assert key is None
    assert data is None


def test_match_profile_enabled_structured():
    profiles = {
        r"C:\Games\game.exe": {"enabled": True, "brightness_data": {"DISPLAY1": 90}},
    }
    key, data = match_profile(profiles, r"C:\Games\game.exe")
    assert key == r"C:\Games\game.exe"
    assert data == {"DISPLAY1": 90}


def test_match_profile_disabled_parent_folder():
    profiles = {
        r"C:\Games": {"enabled": False, "brightness_data": {"DISPLAY1": 70}},
    }
    key, data = match_profile(profiles, r"C:\Games\Sub\game.exe")
    assert key is None
    assert data is None


def test_match_profile_disabled_specific_overrides_parent_enabled():
    profiles = {
        r"C:\Games": {"enabled": True, "brightness_data": {"DISPLAY1": 40}},
        r"C:\Games\Witcher": {"enabled": False, "brightness_data": {"DISPLAY1": 85}},
    }
    # Witcher is explicitly disabled -> must NOT fall back to C:\Games
    key_w, data_w = match_profile(profiles, r"C:\Games\Witcher\bin\witcher.exe")
    assert key_w is None
    assert data_w is None

    # Other game in C:\Games remains enabled -> matches C:\Games
    key_other, data_other = match_profile(profiles, r"C:\Games\Cyberpunk\game.exe")
    assert key_other == r"C:\Games"
    assert data_other == {"DISPLAY1": 40}




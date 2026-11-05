import pytest
from services.profile_matcher import match_profile


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

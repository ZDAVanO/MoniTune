import pytest
from services.brightness_coordinator import BrightnessCoordinator


# ==============================================================================
# МАТРИЦЯ 1: Визначення активності режиму енергозбереження (Power Saving)
# ==============================================================================
@pytest.mark.parametrize(
    "enable_limits, mode, manual_state, win_saver, expected_active",
    [
        # Майстер-перемикач вимкнено -> ніколи не активний
        (False, "windows", False, True, False),
        (False, "windows", True, True, False),
        (False, "manual", True, False, False),
        (False, "manual", True, True, False),

        # Режим "windows": слідує суто за станом Windows 11
        (True, "windows", False, True, True),     # Вінда в режимі енергозбереження -> ТАК
        (True, "windows", False, False, False),   # Вінда на 220V без режиму -> НІ
        (True, "windows", True, False, False),    # Ручна кнопка ігнорується в режимі "windows"

        # Режим "manual": слідує суто за ручною кнопкою-листочком у додатку
        (True, "manual", True, False, True),      # Ручна кнопка увімкнена -> ТАК
        (True, "manual", True, True, True),       # Ручна кнопка увімкнена -> ТАК
        (True, "manual", False, True, False),     # Ручна кнопка вимкнена, вінда в режимі -> ігноруємо вінду, НІ
        (True, "manual", False, False, False),    # Ручна кнопка вимкнена -> НІ
    ],
)
def test_power_saving_effective_matrix(enable_limits, mode, manual_state, win_saver, expected_active):
    coordinator = BrightnessCoordinator()
    is_active = coordinator.is_power_saving_effective(
        enable_limits=enable_limits,
        mode=mode,
        manual_state=manual_state,
        is_windows_energy_saver=win_saver,
    )
    assert is_active == expected_active


# ==============================================================================
# МАТРИЦЯ 2: Визначення цільової яскравості (Розклад vs Ручне vs Ліміт)
# ==============================================================================
@pytest.mark.parametrize(
    "enable_schedule, schedule_val, restore_last, manual_val, is_power_saving, limit, expected_brightness",
    [
        # Сценарій: Тільки ручне значення (розклад вимкнено)
        (False, None, True, 75, False, 100, 75),
        (False, None, True, 75, True, 15, 15),   # Ручне зрізано лімітом
        (False, None, True, 10, True, 15, 10),   # Ручне нижче ліміту -> 10

        # Сценарій: Розклад увімкнено -> перемагає ручне значення
        (True, 60, True, 80, False, 100, 60),
        (True, 60, True, 80, True, 15, 15),      # Розклад (60) зрізано лімітом (15)
        (True, 10, True, 80, True, 15, 10),      # Розклад (10) нижче ліміту -> 10

        # Сценарій: Розклад увімкнено, але для монітора немає слота -> падає на ручне
        (True, None, True, 80, False, 100, 80),

        # Сценарій: Немає цільового значення (restore_last вимкнено або manual is None) -> екран не чіпається (None)
        (False, None, False, 80, False, 100, None),
        (True, None, True, None, False, 100, None),
    ],
)
def test_resolve_brightness_schedule_and_manual(
    enable_schedule, schedule_val, restore_last, manual_val, is_power_saving, limit, expected_brightness
):
    schedule = {"MON1": schedule_val} if schedule_val is not None else {}
    manual = {"MON1": manual_val} if manual_val is not None else {}
    limits = {"MON1": limit}

    result = BrightnessCoordinator.resolve_brightness(
        active_serials=["MON1"],
        schedule_data=schedule,
        manual_data=manual,
        enable_schedule=enable_schedule,
        restore_last_brightness=restore_last,
        is_power_saving=is_power_saving,
        limits=limits,
    )
    if expected_brightness is None:
        assert "MON1" not in result, "Якщо немає цільового значення, монітор не чіпається"
    else:
        assert result.get("MON1") == expected_brightness


@pytest.mark.parametrize(
    "profile_val, schedule_val, manual_val, is_power_saving, limit, expected_brightness",
    [
        # Профіль перемагає розклад і ручне значення
        (90, 60, 40, False, 100, 90),
        # Профіль зрізається лімітом Power Saving
        (90, 60, 40, True, 25, 25),
        # Профіль нижче ліміту не зрізається
        (20, 60, 40, True, 25, 20),
    ],
)
def test_resolve_brightness_profile_priority(
    profile_val, schedule_val, manual_val, is_power_saving, limit, expected_brightness
):
    profile = {"MON1": profile_val}
    schedule = {"MON1": schedule_val}
    manual = {"MON1": manual_val}
    limits = {"MON1": limit}

    res = BrightnessCoordinator.resolve_brightness(
        active_serials=["MON1"],
        profile_data=profile,
        schedule_data=schedule,
        manual_data=manual,
        is_power_saving=is_power_saving,
        limits=limits,
    )
    assert res.get("MON1") == expected_brightness


# ==============================================================================
# МАТРИЦЯ 3: Зв'язування моніторів (Link monitors) з дельтою та лімітами
# ==============================================================================
@pytest.mark.parametrize(
    "master_serial, new_master_val, current_values, limits, is_power_saving, expected_values",
    [
        # Сценарій A: Звичайне збільшення без обмежень (+20%)
        (
            "MON1", 70,
            {"MON1": 50, "MON2": 40},
            {"MON1": 100, "MON2": 100},
            False,
            {"MON1": 70, "MON2": 60},  # MON2 теж зріс на +20
        ),
        # Сценарій B: MON2 має ліміт 15% і не повинен його перевищити
        (
            "MON1", 80,
            {"MON1": 50, "MON2": 15},
            {"MON1": 100, "MON2": 15},
            True,
            {"MON1": 80, "MON2": 15},  # MON1 виріс до 80, MON2 уперся в 15 і не пускає вище
        ),
        # Сценарій C: Зменшення яскравості (-30%)
        (
            "MON1", 20,
            {"MON1": 50, "MON2": 40},
            {"MON1": 100, "MON2": 100},
            False,
            {"MON1": 20, "MON2": 10},  # Обидва зменшились на 30
        ),
        # Сценарій D: Зменшення з нульовим порогом (не може бути менше 0)
        (
            "MON1", 10,
            {"MON1": 50, "MON2": 20},
            {"MON1": 100, "MON2": 100},
            False,
            {"MON1": 10, "MON2": 0},   # MON2 clamp до 0 (20 - 40 = -20 -> 0)
        ),
        # Сценарій E: MON1 (ведучий) теж має ліміт станції і користувач намагається виставити більше
        (
            "MON1", 50,
            {"MON1": 10, "MON2": 10},
            {"MON1": 15, "MON2": 15},
            True,
            {"MON1": 15, "MON2": 15},  # MON1 сам обрізається до 15, MON2 відповідно +5 -> 15
        ),
    ],
)
def test_linked_monitors_matrix(
    master_serial, new_master_val, current_values, limits, is_power_saving, expected_values
):
    coordinator = BrightnessCoordinator()
    result = coordinator.calculate_linked_change(
        master_serial=master_serial,
        new_master_value=new_master_val,
        current_values=current_values,
        limits=limits,
        is_power_saving=is_power_saving,
    )
    assert result == expected_values


# ==============================================================================
# МАТРИЦЯ 4: Поведінка при старті програми (Startup)
# ==============================================================================
@pytest.mark.parametrize(
    "restore_last, time_adj_startup, schedule_val, saved_manual, is_blackout, limit, expected_startup",
    [
        # Запуск зі звичайним розкладом
        (True, True, 60, 80, False, 100, 60),      # Розклад на старті активний -> 60
        (True, True, 60, 80, True, 15, 15),        # Розклад на старті активний, але блекаут -> 15

        # Запуск тільки з відновленням останньої ручної яскравості (розклад на старті вимкнений)
        (True, False, 60, 80, False, 100, 80),     # Відновили останню ручну 80
        (True, False, 60, 80, True, 15, 15),       # Відновили 80, але зрізали до 15

        # Нічого не відновлювати -> None (не чіпати екран)
        (False, False, None, 80, False, 100, None),
        (False, False, None, 80, True, 15, None),
    ],
)
def test_startup_brightness_matrix(
    restore_last, time_adj_startup, schedule_val, saved_manual, is_blackout, limit, expected_startup
):
    coordinator = BrightnessCoordinator()
    result = coordinator.resolve_startup_brightness(
        restore_last_brightness=restore_last,
        time_adjustment_startup=time_adj_startup,
        schedule_value=schedule_val,
        saved_manual_value=saved_manual,
        is_power_saving=is_blackout,
        power_saving_limit=limit,
    )
    assert result == expected_startup


# ==============================================================================
# ТЕСТ 5: Життєвий цикл збереження та відновлення яскравості (State Preservation)
# ==============================================================================
def test_power_saving_lifecycle_preservation():
    """
    Повний цикл:
    1. Працюємо на 85% ручної яскравості.
    2. Увімкнувся блекаут (ліміт 15%) -> яскравість стала 15%, але pre_saving запам'ятав 85%.
    3. Під час блекауту користувач посунув повзунок на 10% (економить станцію ще більше).
    4. Блекаут закінчився -> система відновлює початкові 85% (а не 10% і не 15%).
    """
    coordinator = BrightnessCoordinator()

    # 1. Початковий стан
    serial = "MON1"
    initial_manual = 85
    limits = {"MON1": 15}

    # 2. Вхід у режим збереження
    coordinator.enter_power_saving(
        current_brightness={serial: initial_manual},
        limits=limits,
    )
    assert coordinator.get_active_limit(serial) == 15
    assert coordinator.get_pre_saving_brightness(serial) == 85

    # 3. Ручне коригування під час блекауту до 10%
    clamped_val = coordinator.clamp_value(serial, 10)
    assert clamped_val == 10
    # pre_saving не повинен зіпсуватися!
    assert coordinator.get_pre_saving_brightness(serial) == 85

    # 4. Вихід із режиму збереження без активного профілю і без розкладу
    restored = coordinator.exit_power_saving()
    assert restored[serial] == 85, "Має відновитися первинна яскравість 85%"


def test_enter_power_saving_prefers_live_over_stale_manual():
    """
    Користувацький кейс:
    Жива яскравість задана розкладом (Display 1 = 65%, Samsung = 50%).
    Старі ручні значення в реєстрі випадково збереглися як 22% і 11%.
    Ліміти: Samsung = 15%, Display 1 = 100% (без обмежень).

    Очікування:
    - Samsung отримує min(50, 15) = 15% (а не 11!).
    - Display 1 отримує min(65, 100) = 65% (а не 22!).
    - pre_saving зберігає 50% і 65%.
    """
    coordinator = BrightnessCoordinator()
    live = {"DISPLAY1": 65, "SAMSUNG": 50}
    manual = {"DISPLAY1": 22, "SAMSUNG": 11}
    limits = {"SAMSUNG": 15}

    targets = coordinator.enter_power_saving(
        live_brightness=live,
        fallback_brightness=manual,
        limits=limits,
    )

    assert targets["DISPLAY1"] == 65, "DISPLAY1 не має ліміту, повинен залишитися 65"
    assert targets["SAMSUNG"] == 15, "SAMSUNG має зрізатися до 15, а не брати застарілі 11"
    assert coordinator.get_pre_saving_brightness("SAMSUNG") == 50
    assert coordinator.get_pre_saving_brightness("DISPLAY1") == 65


def test_record_pre_saving_brightness():
    coordinator = BrightnessCoordinator()
    # First record should succeed
    coordinator.record_pre_saving_brightness("MON1", 75)
    assert coordinator.get_pre_saving_brightness("MON1") == 75

    # Subsequent record should not overwrite original pre-saving brightness
    coordinator.record_pre_saving_brightness("MON1", 30)
    assert coordinator.get_pre_saving_brightness("MON1") == 75


def test_remove_monitor_cleans_up():
    coordinator = BrightnessCoordinator()
    coordinator.record_pre_saving_brightness("MON1", 75)
    coordinator.active_limits["MON1"] = 30

    coordinator.remove_monitor("MON1")
    assert coordinator.get_pre_saving_brightness("MON1") is None
    assert coordinator.get_active_limit("MON1") == 100  # defaults to 100 when absent


@pytest.mark.parametrize("task_times,current_time,expected", [
    ([], "12:00", None),
    (["08:00", "14:00", "20:00"], "14:00", "14:00"),  # Exact match
    (["08:00", "14:00", "20:00"], "15:30", "14:00"),  # Between tasks
    (["08:00", "14:00", "20:00"], "07:59", "20:00"),  # Before earliest -> wrap to previous day latest
    (["08:00", "14:00", "20:00"], "00:00", "20:00"),  # Midnight wrap
    (["08:00", "14:00", "20:00"], "23:59", "20:00"),  # After latest
    (["12:00"], "11:59", "12:00"),                     # Single slot wrap
    (["12:00"], "12:01", "12:00"),                     # Single slot past
])
def test_get_recent_task_time(task_times, current_time, expected):
    result = BrightnessCoordinator.get_recent_task_time(task_times, current_time)
    assert result == expected


def test_resolve_brightness_multiple_monitors():
    serials = ["MON1", "MON2", "MON3"]
    # MON1 has schedule, MON2 has no schedule slot (falls back to manual), MON3 has no data at all
    schedule = {"MON1": 60}
    manual = {"MON1": 80, "MON2": 45}

    res = BrightnessCoordinator.resolve_brightness(
        active_serials=serials,
        schedule_data=schedule,
        manual_data=manual,
        enable_schedule=True,
        restore_last_brightness=True,
    )
    assert res == {"MON1": 60, "MON2": 45}
    assert "MON3" not in res, "MON3 не має цільового значення і не повинен бути змінений"


def test_resolve_brightness_power_saving_clamping():
    serials = ["MON1", "MON2"]
    schedule = {"MON1": 90, "MON2": 40}
    limits = {"MON1": 20, "MON2": 50}

    res = BrightnessCoordinator.resolve_brightness(
        active_serials=serials,
        schedule_data=schedule,
        enable_schedule=True,
        is_power_saving=True,
        limits=limits,
    )
    assert res == {"MON1": 20, "MON2": 40}


def test_enter_power_saving_skips_unknown_monitors():
    coordinator = BrightnessCoordinator()
    # MON1 is known, MON2 has neither live nor fallback
    live = {"MON1": 70}
    limits = {"MON1": 15, "MON2": 20}

    targets = coordinator.enter_power_saving(live_brightness=live, limits=limits)
    assert targets == {"MON1": 15}
    assert "MON2" not in targets, "Монітор без відомої яскравості не повинен отримувати 50%"


def test_resolve_brightness_partial_profile():
    serials = ["MON1", "MON2"]
    # MON1 is in profile, MON2 is not -> MON2 falls back to schedule
    profile = {"MON1": 95}
    schedule = {"MON1": 50, "MON2": 65}

    res = BrightnessCoordinator.resolve_brightness(
        active_serials=serials,
        profile_data=profile,
        schedule_data=schedule,
    )
    assert res == {"MON1": 95, "MON2": 65}


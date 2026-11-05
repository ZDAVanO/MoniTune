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
# МАТРИЦЯ 2: Пріоритет джерел яскравості (Профіль vs Розклад vs Ручне vs Ліміт)
# ==============================================================================
@pytest.mark.parametrize(
    "enable_profiles, profile_val, enable_schedule, schedule_val, manual_val, is_power_saving, limit, expected_brightness",
    [
        # Сценарій: Тільки ручне значення (профілі і розклад вимкнені)
        (False, None, False, None, 75, False, 100, 75),
        (False, None, False, None, 75, True, 15, 15),  # Ручне зрізано лімітом станції
        (False, None, False, None, 10, True, 15, 10),  # Ручне нижче ліміту -> залишається 10

        # Сценарій: Розклад увімкнено (профілі вимкнені) -> Розклад перемагає ручне значення
        (False, None, True, 60, 80, False, 100, 60),
        (False, None, True, 60, 80, True, 15, 15),     # Розклад (60) зрізано лімітом (15)
        (False, None, True, 10, 80, True, 15, 10),     # Розклад (10) нижче ліміту (15) -> 10

        # Сценарій: Профіль увімкнено і є збіг -> Профіль перемагає і розклад, і ручне
        (True, 100, True, 50, 70, False, 100, 100),   # Гра дає 100%
        (True, 100, True, 50, 70, True, 15, 15),      # Гра дає 100%, але ліміт станції 15% -> строго 15%
        (True, 12, True, 50, 70, True, 15, 12),       # Гра дає 12% (нічний фільм) -> залишається 12%

        # Сценарій: Профілі увімкнені глобально, але для поточного exe немає профілю (profile_val is None)
        (True, None, True, 65, 80, False, 100, 65),    # Падає на розклад (65)
        (True, None, False, None, 80, False, 100, 80), # Падає на ручне (80)
        (True, None, True, 65, 80, True, 15, 15),      # Падає на розклад, зрізаний до 15
    ],
)
def test_brightness_priority_matrix(
    enable_profiles, profile_val, enable_schedule, schedule_val, manual_val, is_power_saving, limit, expected_brightness
):
    coordinator = BrightnessCoordinator()
    result = coordinator.resolve_brightness(
        enable_profiles=enable_profiles,
        profile_value=profile_val,
        enable_schedule=enable_schedule,
        schedule_value=schedule_val,
        manual_value=manual_val,
        is_power_saving=is_power_saving,
        power_saving_limit=limit,
    )
    assert result == expected_brightness


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

        # Нічого не відновлювати -> дефолт 50
        (False, False, None, 80, False, 100, 50),
        (False, False, None, 80, True, 15, 15),    # Дефолт 50, але ліміт 15 -> 15
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

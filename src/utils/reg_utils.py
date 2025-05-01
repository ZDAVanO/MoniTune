import win32api, win32con
import winreg
import json

import logging
logger = logging.getLogger(__name__)



startup_reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"



def is_dark_theme():
    try:
        key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize', 0, win32con.KEY_READ)
        value, _ = win32api.RegQueryValueEx(key, 'AppsUseLightTheme')
        win32api.RegCloseKey(key)
        return (value == 0)
    except Exception:
        logger.error("Error checking dark theme: ", exc_info=True)
        return False
    

    
# Перевірка, чи існує ключ реєстру
def key_exists(path):
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ)
        return True
    except FileNotFoundError:
        return False

# Створення ключа реєстру
def create_reg_key(path):
    try:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
    except Exception as e:
        logger.error(f"Error creating registry key: {e}")





def reg_write_bool(reg_path, dword_name, value):
    try:
        if not key_exists(reg_path):
            create_reg_key(reg_path)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, dword_name, 0, winreg.REG_DWORD, int(value))
    except Exception as e:
        logger.error(f"Error writing to registry: {e}")


def reg_read_bool(reg_path, dword_name, def_value=True):
    try:
        if not key_exists(reg_path):
            create_reg_key(reg_path)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ) as key:
            try:
                value, _ = winreg.QueryValueEx(key, dword_name)
                return bool(value)
            except FileNotFoundError:
                return def_value
    except Exception as e:
        logger.error(f"Error reading from registry: {e}")
        return def_value


def reg_write_list(reg_path, dword_name, list):
    try:
        order_str = ",".join(map(str, list))

        if not key_exists(reg_path):
            create_reg_key(reg_path)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, dword_name, 0, winreg.REG_SZ, order_str)
        winreg.CloseKey(key)
    except Exception as e:
        logger.error(f"Error writing to registry: {e}")



def reg_read_list(reg_path, dword_name):
    try:
        if not key_exists(reg_path):
            create_reg_key(reg_path)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
        
        try:
            value, _ = winreg.QueryValueEx(key, dword_name)
            raw_list = value.split(",")  # Розбиваємо рядок на список
            
            filtered_list = []  # Створюємо порожній список для відфільтрованих значень
            for item in raw_list:
                cleaned_item = item.strip()  # Видаляємо зайві пробіли
                if cleaned_item:  # Перевіряємо, чи не порожнє значення
                    filtered_list.append(cleaned_item)
            
        except FileNotFoundError:
            filtered_list = []

        winreg.CloseKey(key)

        return filtered_list
    
    except Exception as e:
        logger.error(f"Error reading from registry: {e}")
        return []






def reg_write_dict(reg_path, dword_name, dict_value):
    try:
        dict_str = json.dumps(dict_value)

        if not key_exists(reg_path):
            create_reg_key(reg_path)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, dword_name, 0, winreg.REG_SZ, dict_str)
        winreg.CloseKey(key)
    except Exception as e:
        logger.error(f"Error writing to registry: {e}")


def reg_read_dict(reg_path, dword_name):
    try:
        if not key_exists(reg_path):
            create_reg_key(reg_path)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
        
        try:
            value, _ = winreg.QueryValueEx(key, dword_name)
            dict_value = json.loads(value)
        except FileNotFoundError:
            dict_value = {}

        winreg.CloseKey(key)

        return dict_value
    
    except Exception as e:
        logger.error(f"Error reading from registry: {e}")
        return {}


def delete_reg_key(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            subkeys = []
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, i)
                    subkeys.append(subkey)
                    i += 1
                except OSError:
                    break

            for subkey in subkeys:
                delete_reg_key(f"{path}\\{subkey}")

        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        logger.info(f"Successfully deleted registry key: {path}")
    except FileNotFoundError:
        logger.warning(f"Registry key not found: {path}")
    except Exception as e:
        logger.error(f"Error deleting registry key: {e}")



def add_to_startup(app_name, exe_path):
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_reg_path, 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, startup_reg_path)

    winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(reg_key)
    logger.info(f"{app_name} has been added to startup with path {exe_path}")


def remove_from_startup(app_name):
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(reg_key, app_name)
        winreg.CloseKey(reg_key)
        logger.info(f"{app_name} has been removed from startup")
    except FileNotFoundError:
        logger.warning(f"Registry key not found")
    except FileNotFoundError:
        logger.warning(f"{app_name} not found in startup")



if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO, 
                        format='[%(asctime)s] [%(levelname)s] %(message)s', 
                        datefmt="%H:%M:%S")

    print(is_dark_theme())

    # delete_reg_key(r"Software\MoniTune")



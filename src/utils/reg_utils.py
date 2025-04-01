import win32api, win32con
import winreg
import json

def is_dark_theme():
    try:
        key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize', 0, win32con.KEY_READ)
        value, _ = win32api.RegQueryValueEx(key, 'AppsUseLightTheme')
        win32api.RegCloseKey(key)
        return value == 0
    except Exception:
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
        print(f"Error creating registry key: {e}")





def reg_write_bool(reg_path, dword_name, value):
    try:
        if not key_exists(reg_path):
            create_reg_key(reg_path)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, dword_name, 0, winreg.REG_DWORD, int(value))
    except Exception as e:
        print(f"Error writing to registry: {e}")


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
        print(f"Error reading from registry: {e}")
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
        print(f"Error writing to registry: {e}")



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
        print(f"Error reading from registry: {e}")
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
        print(f"Error writing to registry: {e}")


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
        print(f"Error reading from registry: {e}")
        return {}






if __name__ == '__main__':
    print(is_dark_theme())
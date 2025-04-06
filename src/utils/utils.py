import ctypes
import psutil

import time



class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_time():
    """Повертає час (у секундах), протягом якого ПК був неактивним"""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        current_time = ctypes.windll.kernel32.GetTickCount()  # Час у мілісекундах
        idle_time = (current_time - lii.dwTime) / 1000.0  # Конвертація в секунди
        return idle_time
    else:
        return None  # Помилка отримання даних


def is_laptop():
    battery = psutil.sensors_battery()
    return battery is not None



if __name__ == "__main__":
    print("is_laptop:", is_laptop())
    while True:
        idle_seconds = get_idle_time()
        print(f"Комп'ютер був неактивним {idle_seconds:.2f} секунд")
        
        if idle_seconds > 60:  # Якщо більше 60 секунд бездіяльності
            print("Комп'ютер у стані idle!")

        time.sleep(1)



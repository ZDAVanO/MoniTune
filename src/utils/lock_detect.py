import win32gui
import win32con
import win32ts
import win32api

import threading

WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8

class LockDetect:
    def __init__(self, callback):
        self.callback = callback
        self.hWnd = None

    def _wnd_proc(self, hWnd, msg, wParam, lParam):
        if msg == WM_WTSSESSION_CHANGE:
            if wParam == WTS_SESSION_LOCK:
                self.callback("locked")
            elif wParam == WTS_SESSION_UNLOCK:
                self.callback("unlocked")
        return win32gui.DefWindowProc(hWnd, msg, wParam, lParam)

    def run(self):
        hInstance = win32api.GetModuleHandle(None)
        className = "LockDetectClass"

        wndClass = win32gui.WNDCLASS()
        wndClass.hInstance = hInstance
        wndClass.lpszClassName = className
        wndClass.lpfnWndProc = self._wnd_proc
        win32gui.RegisterClass(wndClass)

        self.hWnd = win32gui.CreateWindow(wndClass.lpszClassName, "SessionWatcher", 0, 0, 0, 0, 0, 0, 0, hInstance, None)
        win32ts.WTSRegisterSessionNotification(self.hWnd, win32ts.NOTIFY_FOR_THIS_SESSION)

        try:
            win32gui.PumpMessages()
        finally:
            win32gui.DestroyWindow(self.hWnd)

# Приклад використання
if __name__ == "__main__":
    import threading

    def on_session_change(state):
        print(f"Стан сесії змінився: {state}")
    
    listener = LockDetect(on_session_change)
    threading.Thread(target=listener.run, daemon=True).start()
    print("Слухач запущено.")
    
    try:
        while True:
            pass  # Головний потік може виконувати інші завдання
    except KeyboardInterrupt:
        print("Завершення програми.")

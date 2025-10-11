import win32con
import win32gui
import win32api
import win32process
import ctypes
import ctypes.wintypes
import psutil


user32 = ctypes.windll.user32

EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0

WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)


def get_active_process():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return hwnd, pid, process.name(), process.exe()
    except Exception as e:
        return f"Error: {e}", None


def get_process_info(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        name = psutil.Process(pid).name()
        exe_path = psutil.Process(pid).exe()
        return {
            "hwnd": hwnd,
            "pid": pid,
            "name": name,
            "exe_path": exe_path,
        }
    except Exception:
        return None


class ActiveProcessListener:
    def __init__(self, callback):
        self.callback = callback
        self.hook = None
        self._win_event_proc = WinEventProcType(self._callback)
        self._running = False
        self._thread_id = None # Додаємо для збереження thread id

    def _callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if hwnd:
            info = get_process_info(hwnd)
            if info:
                self.callback(info)

    def run(self):
        self._thread_id = win32api.GetCurrentThreadId() # Зберігаємо thread id
        self.hook = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            0,
            self._win_event_proc,
            0,
            0,
            WINEVENT_OUTOFCONTEXT
        )
        if not self.hook:
            print("Failed to set hook")
            return
        self._running = True
        try:
            msg = ctypes.wintypes.MSG()
            while self._running and user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self.hook:
                user32.UnhookWinEvent(self.hook)
                self.hook = None
            self._thread_id = None

    def stop(self):
        self._running = False
        # user32.PostThreadMessageW(win32api.GetCurrentThreadId(), win32con.WM_QUIT, 0, 0)
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, win32con.WM_QUIT, 0, 0)


if __name__ == "__main__":
    import threading

    print(psutil.Process().exe())

    def on_active_window_change(pi):
        print(f"Active window changed: {pi}")

    listener = ActiveProcessListener(on_active_window_change)
    threading.Thread(target=listener.run, daemon=True).start()
    print("process listener is running.")
    try:
        while True:
            pass  # Main thread can perform other tasks
    except KeyboardInterrupt:
        listener.stop()
        print("exit.")

"""
Módulo para bloquear la entrada de teclado evasiva mediante hooks de Windows (WH_KEYBOARD_LL).
Bloquea teclas del sistema (Win, Alt+Tab, Alt+Esc, Ctrl+Esc) permitiendo el resto.
"""
import sys
import ctypes
import ctypes.wintypes

WH_KEYBOARD_LL = 13
LRESULT = ctypes.c_int64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Prototipos estrictos para 64-bit
kernel32.GetModuleHandleW.restype = ctypes.wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = [ctypes.wintypes.LPCWSTR]

user32.SetWindowsHookExW.restype = ctypes.c_void_p  # HHOOK
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.wintypes.HMODULE, ctypes.wintypes.DWORD]

user32.UnhookWindowsHookEx.restype = ctypes.wintypes.BOOL
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]

user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]

user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]

class KeyboardBlocker:
    """Bloquea combinaciones evasivas del SO en Windows."""
    def __init__(self):
        self.hook_id = None
        self.hook_func = HOOKPROC(self._hook_callback)

    def _hook_callback(self, nCode, wParam, lParam):
        if nCode >= 0:
            kbd = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk = kbd.vkCode
            flags = kbd.flags

            # Win izquierdo (0x5B) o derecho (0x5C)
            if vk in (0x5B, 0x5C):
                return 1
            
            # Alt (LLKHF_ALTDOWN = 0x20) presionado
            if (flags & 0x20):
                if vk == 0x09:  # Alt + Tab
                    return 1
                if vk == 0x1B:  # Alt + Esc
                    return 1

            # Ctrl + Esc (VK_ESCAPE = 0x1B, VK_CONTROL = 0x11)
            if vk == 0x1B:
                if user32.GetAsyncKeyState(0x11) & 0x8000:
                    return 1

        return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

    def start(self) -> None:
        if sys.platform == "win32" and not self.hook_id:
            h_mod = kernel32.GetModuleHandleW(None)
            self.hook_id = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.hook_func, h_mod, 0)
            if not self.hook_id:
                print(f"[KeyboardBlocker] Error fijando hook: {ctypes.GetLastError()}")

    def stop(self) -> None:
        if sys.platform == "win32" and self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None

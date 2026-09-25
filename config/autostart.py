"""
Módulo de Gestión de Autoarranque con Windows en el Registro (HKCU).
Sincroniza la clave de inicio automático en HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.
"""

from __future__ import annotations
import sys
import winreg
from pathlib import Path


REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SmartBreak"


def is_autostart_enabled() -> bool:
    """Consulta si la clave de autoarranque existe en el registro de Windows para SmartBreak."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[Autostart] Error consultando registro: {e}")
        return False


def set_autostart(enabled: bool) -> bool:
    """
    Configura o elimina la clave de autoarranque en el registro de Windows del usuario actual.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                if getattr(sys, "frozen", False):
                    # Ejecutable compilado con PyInstaller
                    exe_path = f'"{sys.executable}"'
                else:
                    # Entorno de desarrollo local
                    run_py = Path(__file__).resolve().parent.parent / "run.py"
                    exe_path = f'"{sys.executable}" "{run_py}"'

                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                print(f"[Autostart] Autoarranque registrado en Windows: {exe_path}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    print("[Autostart] Clave de autoarranque eliminada del registro.")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"[Autostart] Error modificando registro de Windows: {e}")
        return False

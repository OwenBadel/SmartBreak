"""
Pruebas Unitarias para Integraciones de Sistema: Autoarranque en Registro y Single-Instance.
"""

import unittest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
from config.autostart import is_autostart_enabled, set_autostart
from run import check_single_instance, MUTEX_NAME
from ui.lock_window import SecondaryLockOverlay


app = QApplication.instance() or QApplication([])


class TestSystemIntegrations(unittest.TestCase):
    """Pruebas de autoarranque en Windows y control de procesos."""

    def test_autostart_functions_callable(self):
        """Verifica que las funciones de registro de Windows no arrojen excepciones no controladas."""
        enabled = is_autostart_enabled()
        self.assertIsInstance(enabled, bool)

        # Prueba segura de deshabilitación sin modificar claves de otros programas
        res = set_autostart(False)
        self.assertTrue(res)

    def test_single_instance_mutex(self):
        """Verifica que el mutex Win32 se cree adecuadamente en Windows."""
        if sys.platform == "win32":
            handle = check_single_instance()
            # El handle no debe ser None a menos que otra instancia esté corriendo activamente
            if handle is not None:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(handle)

    def test_secondary_lock_overlay_init(self):
        """Verifica que la capa de bloqueo secundaria se inicialice correctamente."""
        screens = QGuiApplication.screens()
        if screens:
            overlay = SecondaryLockOverlay(screens[0])
            self.assertIsNotNone(overlay)
            self.assertTrue(overlay.windowFlags() & 0x00000800)  # FramelessWindowHint
            overlay.close()


if __name__ == "__main__":
    unittest.main()

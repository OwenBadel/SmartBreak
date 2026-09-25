"""
Punto de Entrada Principal para SmartBreak.
Inicializa el ciclo de vida de la aplicación Qt, la bandeja del sistema y el orquestador.
Incluye protección de instancia única con Win32 Mutex y configuración High-DPI.
"""

from __future__ import annotations
import sys
import os
import ctypes
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

# Asegurar que el directorio raíz del proyecto esté en el sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import Settings
from core.orchestrator import SmartBreakOrchestrator


MUTEX_NAME = "Local\\SmartBreak_SingleInstance_Mutex"


def check_single_instance() -> ctypes.c_void_p | None:
    """Verifica si ya existe otra instancia de SmartBreak en ejecución mediante Win32 Mutex."""
    if sys.platform != "win32":
        return None
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        return None
    return mutex


def main():
    """Inicialización y ejecución de SmartBreak."""
    # Control de instancia única (BUG-11)
    mutex_handle = check_single_instance()
    if mutex_handle is None:
        print("[SmartBreak] Ya existe una instancia de SmartBreak en ejecución. Saliendo...")
        sys.exit(0)

    # Configuración de escalado High-DPI para nitidez en pantallas modernas
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Configuración de metadatos de la aplicación
    app.setApplicationName("SmartBreak")
    app.setApplicationDisplayName("")  # Permite formato de títulos estricto sin duplicación
    app.setOrganizationName("Lemon Software Factory")
    
    # REGLA CRUCIAL PARA TRAY APPS:
    # Evitar que la aplicación se cierre al destruir la ventana de bloqueo o el diálogo de configuración
    app.setQuitOnLastWindowClosed(False)

    # Cargar icono oficial si existe en local o empaquetado
    possible_icon_paths = [
        PROJECT_ROOT / "assets" / "icon.ico",
        Path(getattr(sys, "_MEIPASS", "")) / "assets" / "icon.ico",
        Path(sys.executable).parent / "_internal" / "assets" / "icon.ico",
        Path(sys.executable).parent / "assets" / "icon.ico",
    ]
    icon_path = None
    for p in possible_icon_paths:
        if p.exists():
            icon_path = p
            break

    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    print("[SmartBreak] Iniciando arquitectura en segundo plano...")
    
    # Cargar configuración y lanzar el orquestador
    settings = Settings.load()
    orchestrator = SmartBreakOrchestrator(settings)
    
    # Vincular icono al tray
    if icon_path:
        orchestrator.tray.icon_path = str(icon_path)

    # Iniciar servicios de monitoreo y bandeja
    orchestrator.start()

    # Si se pasa el argumento --trigger-now, abrir inmediatamente la pantalla de pausa activa
    if "--trigger-now" in sys.argv:
        from PyQt6.QtCore import QTimer
        print("[SmartBreak] Parámetro --trigger-now detectado. Desplegando pantalla de ejercicio...")
        QTimer.singleShot(600, lambda: orchestrator.signals.trigger_break.emit("Prueba manual inmediata"))

    print("[SmartBreak] Sistema activo en la bandeja de Windows (System Tray).")
    
    # Iniciar bucle de eventos principal de PyQt6
    exit_code = app.exec()

    # Liberar mutex
    if mutex_handle:
        try:
            ctypes.windll.kernel32.CloseHandle(mutex_handle)
        except Exception:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

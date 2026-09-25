"""
Orquestador Central de SmartBreak.
Coordina el VisionWorker desacoplado en segundo plano, la interacción
con el System Tray y el despliegue de la pantalla de bloqueo estricto en PyQt6.
"""

from __future__ import annotations
import time
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

try:
    from config.settings import Settings
    from core.vision_worker import VisionWorker
    from ui.lock_window import LockWindow
    from ui.config_dialog import ConfigDialog
    from ui.status_dialog import StatusDialog
    from ui.tray_manager import TrayManager
    from vision.camera_manager import get_available_cameras
except ImportError:
    from ..config.settings import Settings
    from .vision_worker import VisionWorker
    from ..ui.lock_window import LockWindow
    from ..ui.config_dialog import ConfigDialog
    from ..ui.status_dialog import StatusDialog
    from ..ui.tray_manager import TrayManager
    from ..vision.camera_manager import get_available_cameras


class OrchestratorSignals(QObject):
    """Puente de señales para comunicar hilos secundarios con el hilo de PyQt6."""
    trigger_break = pyqtSignal(str)       # Razón del bloqueo
    show_status = pyqtSignal()            # Mostrar diálogo de estado
    open_config = pyqtSignal()            # Abrir diálogo de configuración
    shutdown_app = pyqtSignal()           # Salir de la aplicación


class SmartBreakOrchestrator(QObject):
    """
    Controlador maestro del ciclo de vida de SmartBreak.
    """

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__()
        self.settings = settings or Settings.load()

        # Worker de visión desacoplado en segundo plano (QThread)
        self.worker = VisionWorker(self.settings)
        self.worker.frame_ready.connect(self._on_frame_ready_main_thread)
        self.worker.passive_status_updated.connect(self._on_passive_status_updated)
        self.worker.trigger_break.connect(self._on_trigger_break_signal)
        self.worker.camera_switched.connect(self._on_camera_switched)

        # Puente de señales de usuario
        self.signals = OrchestratorSignals()
        self.signals.trigger_break.connect(self._on_trigger_break_main_thread)
        self.signals.show_status.connect(self._on_show_status_main_thread)
        self.signals.open_config.connect(self._on_open_config_main_thread)
        self.signals.shutdown_app.connect(self._on_shutdown_main_thread)

        # Control de Estado
        self.is_running: bool = False
        self.is_in_active_break: bool = False

        # Ventanas y Diálogos
        self.lock_window: Optional[LockWindow] = None
        self.config_dialog: Optional[ConfigDialog] = None
        self.status_dialog: Optional[StatusDialog] = None

        # System Tray
        self.tray = TrayManager(
            on_show_status=lambda: self.signals.show_status.emit(),
            on_force_break=lambda: self.signals.trigger_break.emit("Forzado manualmente por el usuario"),
            on_open_config=lambda: self.signals.open_config.emit(),
            on_exit_app=lambda: self.signals.shutdown_app.emit()
        )

    # Propiedades delegadas para compatibilidad con tests y extensiones
    @property
    def fatigue_tracker(self):
        return self.worker.fatigue_tracker

    @property
    def pose_detector(self):
        return self.worker.pose_detector

    @property
    def posture_analyzer(self):
        return self.worker.posture_analyzer

    @property
    def exercise_verifier(self):
        return self.worker.exercise_verifier

    def start(self) -> None:
        """Inicia la bandeja de sistema y el worker de visión en segundo plano."""
        self.is_running = True
        self.tray.start()

        # Notificación inicial en Windows
        self.tray.notify(
            "SmartBreak Activo",
            f"Monitoreando postura. Pausa cada {self.settings.max_sitting_minutes}m sentado o {self.settings.max_bad_posture_minutes}m mala postura."
        )

        # Iniciar hilo de visión (arranca en modo pasivo 1-2 FPS)
        self.worker.start()

    def _on_trigger_break_signal(self, reason: str) -> None:
        """Reenvía la señal del worker al hilo principal Qt."""
        self.signals.trigger_break.emit(reason)

    def _on_passive_status_updated(self, summary: dict) -> None:
        """Actualiza el texto flotante de la bandeja del sistema."""
        status_text = (
            f"SmartBreak | Sentado: {int(summary['sitting_minutes'])}m / {self.settings.max_sitting_minutes}m | "
            f"Mala postura: {int(summary['bad_posture_minutes'])}m"
        )
        self.tray.update_tooltip(status_text)

    def _on_camera_switched(self, cam_idx: int, cam_name: str) -> None:
        """Notificación cuando el worker cambia de cámara automáticamente."""
        self.tray.notify("Cámara Conectada", f"Señal detectada en {cam_name} (#{cam_idx}).")

    def _on_frame_ready_main_thread(self, annotated_frame, status) -> None:
        """Recibe el fotograma procesado por el worker y lo pasa a la ventana de bloqueo."""
        if self.is_in_active_break and self.lock_window:
            self.lock_window.update_exercise_status(annotated_frame, status)

    def _on_trigger_break_main_thread(self, reason: str) -> None:
        """Despliega la pantalla de bloqueo estricto en el hilo de la UI."""
        if self.is_in_active_break:
            return

        # Cerrar diálogos modales abiertos si los hubiera (BUG-09)
        if self.config_dialog and self.config_dialog.isVisible():
            self.config_dialog.reject()
            self.config_dialog = None
        if self.status_dialog and self.status_dialog.isVisible():
            self.status_dialog.reject()
            self.status_dialog = None

        self.is_in_active_break = True
        print(f"[Orchestrator] Mostrando pantalla de bloqueo estricto. Razón: {reason}")

        # Conmutar worker al modo activo de alto rendimiento a 30 FPS
        self.worker.set_active_break_mode(True)

        # Instanciar y configurar ventana de bloqueo
        self.lock_window = LockWindow(self.settings)
        self.lock_window.break_completed.connect(self._on_break_completed)
        self.lock_window.emergency_unlocked.connect(self._on_emergency_unlocked)

        # Mostrar en todos los monitores disponibles
        self.lock_window.show_across_all_screens()

    def _on_break_completed(self) -> None:
        """Callback cuando el usuario cumple exitosamente el ejercicio."""
        print("[Orchestrator] Pausa activa completada con éxito.")
        self._cleanup_break_session()

        self.tray.notify(
            "¡Pausa Activa Completada!",
            "Excelente trabajo. Tu postura y circulación han sido restablecidas. ¡Sigue programando!"
        )

    def _on_emergency_unlocked(self) -> None:
        """Callback si se activó la anulación de emergencia."""
        print("[Orchestrator] Pausa anulada por emergencia.")
        self._cleanup_break_session()

    def _cleanup_break_session(self) -> None:
        """Detiene el modo activo del worker y regresa al modo pasivo silencioso."""
        self.worker.set_active_break_mode(False)
        self.worker.reset_fatigue()
        self.is_in_active_break = False
        if self.lock_window:
            self.lock_window = None

    def _on_show_status_main_thread(self) -> None:
        """Muestra el estado actual de fatiga con la interfaz StatusDialog."""
        summary = self.fatigue_tracker.get_status_summary()
        cam_idx = self.settings.camera_index
        cam_name = f"Cámara #{cam_idx}"
        try:
            cams = get_available_cameras()
            for idx, name in cams:
                if idx == cam_idx:
                    cam_name = name
                    break
        except Exception:
            pass

        self.status_dialog = StatusDialog(
            summary=summary,
            exercise_type=self.settings.exercise_type,
            summary_provider=self.fatigue_tracker.get_status_summary,
            camera_index=cam_idx,
            camera_name=cam_name
        )
        self.status_dialog.exec()
        self.status_dialog = None

    def _on_open_config_main_thread(self) -> None:
        """Abre la ventana de configuración."""
        self.config_dialog = ConfigDialog(self.settings)
        self.config_dialog.settings_updated.connect(self._on_settings_updated)
        self.config_dialog.exec()
        self.config_dialog = None

    def _on_settings_updated(self, new_settings: Settings) -> None:
        """Actualiza los parámetros activos del orquestador y del worker."""
        self.settings = new_settings
        self.worker.update_settings(new_settings)
        print("[Orchestrator] Parámetros de configuración actualizados correctamente.")

    def _on_shutdown_main_thread(self) -> None:
        """Cierre ordenado de la aplicación."""
        print("[Orchestrator] Cerrando SmartBreak...")
        self.is_running = False
        self.worker.stop()
        self.tray.stop()
        QApplication.quit()

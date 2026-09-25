"""
Ventana de Bloqueo Estricto a Pantalla Completa para SmartBreak en PyQt6.
Estilo Deportivo de Alto Impacto (Fitness / Athletic Tech) con Máxima Legibilidad.
Diseñado para que cada métrica, etiqueta y botón se distinga con total claridad.
"""

from __future__ import annotations
import time
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut, QGuiApplication
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QProgressBar, QPushButton, QApplication, QGraphicsDropShadowEffect
)

try:
    from ui.video_canvas import VideoCanvas
    from config.settings import Settings
    from vision.exercise_verifier import ExerciseStatus
except ImportError:
    from .video_canvas import VideoCanvas
    from ..config.settings import Settings
    from ..vision.exercise_verifier import ExerciseStatus


class SecondaryLockOverlay(QWidget):
    """
    Capa de bloqueo estricto para monitores secundarios en estaciones multi-pantalla.
    Impide evadir la pausa activa en pantallas adyacentes.
    """
    def __init__(self, target_screen, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartBreak - Bloqueo Secundario")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Window
        )
        self.setStyleSheet("""
            QWidget {
                background-color: #080A0F;
                color: #FFFFFF;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
        """)
        # Fijar al monitor asignado
        self.setGeometry(target_screen.geometry())

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        badge_box = QHBoxLayout()
        badge_lbl = QLabel("⚡ SMARTBREAK • MONITOR PROTEGIDO")
        badge_lbl.setStyleSheet("""
            color: #CCFF00;
            font-size: 13px;
            font-weight: 900;
            letter-spacing: 2px;
            background-color: rgba(204, 255, 0, 0.12);
            border: 1px solid rgba(204, 255, 0, 0.4);
            border-radius: 16px;
            padding: 6px 18px;
        """)
        badge_box.addStretch()
        badge_box.addWidget(badge_lbl)
        badge_box.addStretch()
        layout.addLayout(badge_box)

        title = QLabel("PAUSA ACTIVA EN PANTALLA PRINCIPAL")
        title.setStyleSheet("font-size: 32px; font-weight: 900; color: #FFFFFF; letter-spacing: -0.5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Ponte de pie y completa el ejercicio frente a la cámara en tu monitor principal para desbloquear.")
        sub.setStyleSheet("font-size: 16px; color: #94A3B8; font-weight: 600;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

    def keyPressEvent(self, event) -> None:
        event.ignore()

    def closeEvent(self, event) -> None:
        event.accept()


class LockWindow(QWidget):
    """
    Pantalla de bloqueo estricto a pantalla completa con estética deportiva.
    Diseño fitness de alto contraste con tarjetas de rendimiento y telemetría clara.
    """

    break_completed = pyqtSignal()
    emergency_unlocked = pyqtSignal()

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.unlocked_authorized: bool = False
        self.secondary_overlays: list[SecondaryLockOverlay] = []

        # Configuración de Ventana Estricta: Sin marco, siempre al frente y a pantalla completa
        self.setWindowTitle("Pausa Activa Obligatoria - SmartBreak")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self) -> None:
        """Construye la interfaz de usuario con temática deportiva de alto rendimiento."""
        self.setStyleSheet("""
            QWidget {
                background-color: #080A0F;
                color: #FFFFFF;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            
            /* Tarjetas Deportivas de Fibra de Carbono */
            QFrame.card {
                background-color: #111522;
                border: 2px solid #1E2638;
                border-radius: 18px;
            }
            QFrame.card:hover {
                border: 2px solid #2B3852;
            }
            
            /* Tipografía y Encabezados Deportivos */
            QLabel.brand-badge {
                color: #CCFF00;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 2.5px;
                background-color: rgba(204, 255, 0, 0.12);
                border: 1px solid rgba(204, 255, 0, 0.4);
                border-radius: 20px;
                padding: 5px 16px;
            }
            QLabel.title {
                font-size: 34px;
                font-weight: 900;
                color: #FFFFFF;
                letter-spacing: -0.5px;
            }
            QLabel.subtitle {
                font-size: 15px;
                font-weight: 500;
                color: #94A3B8;
            }
            
            /* Métricas Numéricas Gigantes (Estilo Marcador Deportivo) */
            QLabel.metric-value {
                font-size: 42px;
                font-weight: 900;
                color: #CCFF00;
                letter-spacing: -1px;
            }
            QLabel.metric-unit {
                font-size: 16px;
                font-weight: 700;
                color: #00F0FF;
            }
            QLabel.metric-label {
                font-size: 11px;
                font-weight: 800;
                color: #718096;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }
            
            /* Barra de Progreso Neón Segmentada */
            QProgressBar {
                background-color: #1A2030;
                border: 1px solid #2D3748;
                border-radius: 10px;
                text-align: center;
                height: 22px;
                font-size: 12px;
                font-weight: 900;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F0FF, stop:1 #CCFF00);
                border-radius: 9px;
            }
            
            /* Botón de Emergencia Táctico */
            QPushButton.emergency-btn {
                background-color: rgba(255, 45, 85, 0.08);
                border: 2px solid rgba(255, 45, 85, 0.35);
                color: #FF5E7E;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
                padding: 10px 20px;
                border-radius: 10px;
            }
            QPushButton.emergency-btn:hover {
                background-color: #FF2D55;
                border: 2px solid #FF2D55;
                color: #FFFFFF;
            }
            QPushButton.emergency-btn:pressed {
                background-color: #D61B40;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 28, 40, 28)
        main_layout.setSpacing(20)

        # -------------------------------------------------------------
        # 1. Cabecera Deportiva de Alto Impacto
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        # Badge superior
        badge_box = QHBoxLayout()
        badge_lbl = QLabel("⚡ SMARTBREAK • ATHLETIC RECOVERY SYSTEM")
        badge_lbl.setProperty("class", "brand-badge")
        badge_box.addWidget(badge_lbl)
        badge_box.addStretch()
        title_box.addLayout(badge_box)

        # Título principal de gran peso visual
        self.title_lbl = QLabel("¡HORA DE ENTRENAR! DESBLOQUEO POR MOVIMIENTO")
        self.title_lbl.setProperty("class", "title")
        title_box.addWidget(self.title_lbl)

        # Subtítulo explicativo con máxima claridad
        self.sub_lbl = QLabel("Ponte de pie frente a la cámara y completa el objetivo físico para desbloquear tu equipo.")
        self.sub_lbl.setProperty("class", "subtitle")
        title_box.addWidget(self.sub_lbl)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Botón de desbloqueo de emergencia táctico
        self.emergency_btn = QPushButton("⚠️ ANULACIÓN DE EMERGENCIA")
        self.emergency_btn.setProperty("class", "emergency-btn")
        self.emergency_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.emergency_btn.clicked.connect(self._handle_emergency_click)
        header_layout.addWidget(self.emergency_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        main_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. Contenido Central: Video Canvas (70%) + Panel de Telemetría (30%)
        # -------------------------------------------------------------
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # Lienzo del Video con Brackets Deportivos
        self.video_canvas = VideoCanvas(self)
        content_layout.addWidget(self.video_canvas, stretch=7)

        # Sidebar de Rendimiento Atlético
        sidebar_frame = QFrame(self)
        sidebar_frame.setProperty("class", "card")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(24, 24, 24, 24)
        sidebar_layout.setSpacing(18)

        # Tarjeta 1: Objetivo de Entrenamiento
        ex_box = QVBoxLayout()
        ex_tag = QLabel("OBJETIVO DE ENTRENAMIENTO")
        ex_tag.setProperty("class", "metric-label")
        ex_box.addWidget(ex_tag)

        ex_name = "ESTIRAMIENTO OVERHEAD" if self.settings.exercise_type == "overhead_stretch" else "SENTADILLAS PROFUNDAS"
        self.exercise_name_lbl = QLabel(ex_name)
        self.exercise_name_lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #CCFF00; letter-spacing: 0.5px;")
        ex_box.addWidget(self.exercise_name_lbl)

        self.exercise_desc_lbl = QLabel(
            "Eleva ambos brazos rectos hacia el techo manteniendo la espalda erguida."
            if self.settings.exercise_type == "overhead_stretch"
            else "Flexiona las rodillas a 90° con la espalda recta y regresa a posición de pie."
        )
        self.exercise_desc_lbl.setWordWrap(True)
        self.exercise_desc_lbl.setStyleSheet("color: #CBD5E1; font-size: 13px; font-weight: 500; line-height: 1.4;")
        ex_box.addWidget(self.exercise_desc_lbl)
        sidebar_layout.addLayout(ex_box)

        # Tarjeta 2: Monitor de Bipedestación
        standing_box = QVBoxLayout()
        lbl_std = QLabel("MONITOR BIOMECÁNICO")
        lbl_std.setProperty("class", "metric-label")
        standing_box.addWidget(lbl_std)

        self.standing_status_lbl = QLabel("🪑 USUARIO EN ESCRITORIO")
        self.standing_status_lbl.setStyleSheet("""
            background-color: rgba(255, 45, 85, 0.15);
            border: 1px solid #FF2D55;
            color: #FF2D55;
            font-size: 13px;
            font-weight: 900;
            padding: 8px 14px;
            border-radius: 8px;
            letter-spacing: 1px;
        """)
        standing_box.addWidget(self.standing_status_lbl)
        sidebar_layout.addLayout(standing_box)

        # Tarjeta 3: Marcador Numérico y Barra de Desempeño
        score_box = QVBoxLayout()
        self.metric_label = QLabel("META DE DESBLOQUEO")
        self.metric_label.setProperty("class", "metric-label")
        score_box.addWidget(self.metric_label)

        # Contador de dígitos grandes
        counter_layout = QHBoxLayout()
        self.metric_value_lbl = QLabel("00")
        self.metric_value_lbl.setProperty("class", "metric-value")
        counter_layout.addWidget(self.metric_value_lbl)

        self.metric_unit_lbl = QLabel("/ 60 SEG")
        self.metric_unit_lbl.setProperty("class", "metric-unit")
        counter_layout.addWidget(self.metric_unit_lbl)
        counter_layout.addStretch()
        score_box.addLayout(counter_layout)

        # Barra de progreso deportiva
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        score_box.addWidget(self.progress_bar)
        sidebar_layout.addLayout(score_box)

        sidebar_layout.addStretch()

        # Tarjeta 4: Checklist Ergonómico Rápido
        tips_box = QFrame()
        tips_box.setStyleSheet("""
            background-color: #161C2C;
            border: 1px solid #253147;
            border-radius: 12px;
            padding: 12px;
        """)
        tips_layout = QVBoxLayout(tips_box)
        tips_layout.setSpacing(6)

        tips_title = QLabel("🔥 CLAVES DE RENDIMIENTO")
        tips_title.setStyleSheet("font-size: 11px; font-weight: 900; color: #00F0FF; letter-spacing: 1px;")
        tips_layout.addWidget(tips_title)

        tip1 = QLabel("✓ Espalda recta y mirada al frente")
        tip1.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")
        tip2 = QLabel("✓ Piernas extendidas (Ángulo > 165°)")
        tip2.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")
        tip3 = QLabel("✓ Respiración rítmica y profunda")
        tip3.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")
        
        tips_layout.addWidget(tip1)
        tips_layout.addWidget(tip2)
        tips_layout.addWidget(tip3)
        sidebar_layout.addWidget(tips_box)

        content_layout.addWidget(sidebar_frame, stretch=3)
        main_layout.addLayout(content_layout)

    def _setup_shortcuts(self) -> None:
        """Atajo de soporte para anulación controlada (Ctrl + Shift + Alt + U)."""
        emergency_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Alt+U"), self)
        emergency_shortcut.activated.connect(self._trigger_emergency_unlock)

    def keyPressEvent(self, event) -> None:
        """
        Intercepta y bloquea teclas del sistema (Esc, Alt+F4, Tab, etc.)
        para asegurar que el usuario cumpla el objetivo de ejercicio.
        """
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Alt, Qt.Key.Key_Tab, Qt.Key.Key_Close):
            event.ignore()
            return
        event.ignore()

    def show_across_all_screens(self) -> None:
        """Despliega la ventana de entrenamiento en el monitor principal y bloquea todos los monitores secundarios."""
        screens = QGuiApplication.screens()
        primary = QGuiApplication.primaryScreen()

        if primary:
            self.setGeometry(primary.geometry())

        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        # Limpiar overlays anteriores si hubieran quedado
        self._close_secondary_overlays()

        # Desplegar overlay de bloqueo en monitores secundarios
        for scr in screens:
            if primary and scr == primary:
                continue
            overlay = SecondaryLockOverlay(scr)
            overlay.showFullScreen()
            overlay.raise_()
            self.secondary_overlays.append(overlay)

    def _close_secondary_overlays(self) -> None:
        """Cierra todas las pantallas de bloqueo secundarias."""
        for overlay in self.secondary_overlays:
            try:
                overlay.close()
            except Exception:
                pass
        self.secondary_overlays.clear()

    def closeEvent(self, event) -> None:
        """Evita el cierre arbitrario hasta la confirmación de desbloqueo."""
        if self.unlocked_authorized:
            self._close_secondary_overlays()
            event.accept()
        else:
            event.ignore()

    def update_exercise_status(self, frame_bgr: np.ndarray, status: ExerciseStatus) -> None:
        """
        Recibe la telemetría biomecánica del motor de visión y refresca el HUD.
        """
        # Actualizar el lienzo deportivo con el feed de cámara
        self.video_canvas.update_frame(
            frame_bgr=frame_bgr,
            feedback=status.feedback_message,
            progress=status.progress_percent,
            is_standing=status.is_standing,
            knee_angle=status.knee_angle
        )

        # Actualizar tarjeta de bipedestación
        if status.is_standing:
            self.standing_status_lbl.setText(f"⚡ DE PIE • {status.knee_angle:.1f}°")
            self.standing_status_lbl.setStyleSheet("""
                background-color: rgba(204, 255, 0, 0.15);
                border: 1px solid #CCFF00;
                color: #CCFF00;
                font-size: 13px;
                font-weight: 900;
                padding: 8px 14px;
                border-radius: 8px;
                letter-spacing: 1px;
            """)
        else:
            self.standing_status_lbl.setText(f"🪑 EN ESCRITORIO • {status.knee_angle:.1f}°")
            self.standing_status_lbl.setStyleSheet("""
                background-color: rgba(255, 45, 85, 0.15);
                border: 1px solid #FF2D55;
                color: #FF2D55;
                font-size: 13px;
                font-weight: 900;
                padding: 8px 14px;
                border-radius: 8px;
                letter-spacing: 1px;
            """)

        # Actualizar dígitos grandes según ejercicio
        if status.current_exercise == "squats":
            self.metric_label.setText("REPETICIONES COMPLETADAS")
            self.metric_value_lbl.setText(f"{status.completed_reps:02d}")
            self.metric_unit_lbl.setText(f"/ {status.target_reps:02d} REPS")
        else:
            self.metric_label.setText("TIEMPO EN ESTIRAMIENTO")
            self.metric_value_lbl.setText(f"{int(status.elapsed_seconds):02d}")
            self.metric_unit_lbl.setText(f"/ {int(status.target_seconds):02d} SEG")

        self.progress_bar.setValue(int(status.progress_percent))

        # Validación de cumplimiento del objetivo
        if status.is_unlocked and not self.unlocked_authorized:
            self._handle_unlock_success()

    def _handle_unlock_success(self) -> None:
        """Secuencia de celebración deportiva y desbloqueo autorizado."""
        self.unlocked_authorized = True
        self.title_lbl.setText("🎉 ¡OBJETIVO CUMPLIDO! PAUSA COMPLETADA")
        self.title_lbl.setStyleSheet("color: #CCFF00; font-size: 34px; font-weight: 900;")
        self.sub_lbl.setText("Excelente trabajo. Circulación activada y postura reiniciada. Regresando a tu escritorio...")
        self.sub_lbl.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")

        # Pausa de 1.2 segundos para apreciar la confirmación de éxito y cerrar
        QTimer.singleShot(1200, self._finalize_unlock)

    def _finalize_unlock(self) -> None:
        """Cierra la ventana y emite señal de desbloqueo."""
        self._close_secondary_overlays()
        self.break_completed.emit()
        self.close()

    def _handle_emergency_click(self) -> None:
        """Anulación de emergencia manual."""
        self._trigger_emergency_unlock()

    def _trigger_emergency_unlock(self) -> None:
        """Desbloqueo de urgencia."""
        self.unlocked_authorized = True
        self._close_secondary_overlays()
        self.emergency_unlocked.emit()
        self.close()

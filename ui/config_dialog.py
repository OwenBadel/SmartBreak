"""
Diálogo Deportivo de Configuración de Intervalos y Opciones para SmartBreak.
Cumple estrictamente con las directivas de frontend:
- Prohibición de alturas fijas en etiquetas de texto.
- Sub-controles con flechas ▲ y ▼ explícitas en QSpinBox y QComboBox.
- Feedback de valores numéricos en tiempo real para todos los sliders.
- Formato estricto de título: 'Configuración de Rendimiento - SmartBreak'.
- Cero contenedores esqueleto o placeholders vacíos.
"""

from __future__ import annotations
import sys
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QComboBox, QCheckBox, QPushButton, QFrame, QSlider, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor
try:
    from config.settings import Settings
except ImportError:
    from ..config.settings import Settings

try:
    from vision.camera_manager import get_available_cameras
except ImportError:
    from ..vision.camera_manager import get_available_cameras

try:
    from config.autostart import set_autostart, is_autostart_enabled
except ImportError:
    from ..config.autostart import set_autostart, is_autostart_enabled


def _get_asset_path(filename: str) -> str:
    """Obtiene la ruta absoluta en formato URL seguro para hojas de estilo Qt."""
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    if hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "assets"
        if bundled.exists():
            assets_dir = bundled
    file_path = assets_dir / filename
    return file_path.as_posix()


class AutoDetectCameraComboBox(QComboBox):
    """QComboBox que escanea y actualiza automáticamente los dispositivos de video antes de desplegarse."""
    def __init__(self, on_before_popup=None, parent=None):
        super().__init__(parent)
        self._on_before_popup = on_before_popup

    def showPopup(self):
        if self._on_before_popup:
            self._on_before_popup()
        super().showPopup()


class ConfigDialog(QDialog):
    """Ventana de ajustes ergonómicos con feedback interactivo y controles deportivos."""

    settings_updated = pyqtSignal(Settings)

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        
        # Formato de título único estricto: '{Nombre Ventana} - {Nombre App}'
        self.setWindowTitle("Configuración de Rendimiento - SmartBreak")
        self.setMinimumSize(580, 600)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._init_ui()

    def _apply_shadow(self, widget: QFrame) -> None:
        """Aplica una sombra suave y moderna tipo web al contenedor."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        widget.setGraphicsEffect(shadow)

    def _init_ui(self) -> None:
        spin_up_url = _get_asset_path("spin_up.png")
        spin_down_url = _get_asset_path("spin_down.png")
        combo_down_url = _get_asset_path("combo_down.png")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #080A0F;
                color: #FFFFFF;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }}
            
            QFrame.card {{
                background-color: #111522;
                border: 2px solid #1E2638;
                border-radius: 14px;
            }}
            
            QLabel.section-tag {{
                color: #CCFF00;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1.5px;
            }}
            QLabel.field-label {{
                color: #E2E8F0;
                font-size: 13px;
                font-weight: 700;
            }}
            QLabel.slider-feedback {{
                color: #CCFF00;
                font-size: 14px;
                font-weight: 900;
                background-color: #161C2C;
                border: 1px solid #28354D;
                border-radius: 6px;
                padding: 4px 10px;
                min-width: 60px;
            }}
            
            /* QSlider Deportivo */
            QSlider::groove:horizontal {{
                height: 8px;
                background-color: #1A2234;
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F0FF, stop:1 #CCFF00);
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background-color: #FFFFFF;
                border: 2px solid #CCFF00;
                width: 18px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: #CCFF00;
                border: 2px solid #FFFFFF;
            }}

            /* QSpinBox con Sub-controles y Flechas Visibles */
            QSpinBox {{
                background-color: #161C2C;
                border: 2px solid #28354D;
                border-radius: 8px;
                color: #CCFF00;
                font-size: 14px;
                font-weight: 900;
                padding: 6px 10px;
                min-height: 34px;
            }}
            QSpinBox:hover {{
                border: 2px solid #3B4B6E;
            }}
            QSpinBox:focus {{
                border: 2px solid #CCFF00;
                background-color: #1B2338;
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 26px;
                height: 18px;
                background-color: #1E283D;
                border-left: 1px solid #2B3852;
                border-bottom: 1px solid #2B3852;
                border-top-right-radius: 6px;
            }}
            QSpinBox::up-button:hover {{
                background-color: #2D3D5E;
            }}
            QSpinBox::up-arrow {{
                image: url({spin_up_url});
                width: 10px;
                height: 10px;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 26px;
                height: 18px;
                background-color: #1E283D;
                border-left: 1px solid #2B3852;
                border-bottom-right-radius: 6px;
            }}
            QSpinBox::down-button:hover {{
                background-color: #2D3D5E;
            }}
            QSpinBox::down-arrow {{
                image: url({spin_down_url});
                width: 10px;
                height: 10px;
            }}

            /* QComboBox con Flecha Visible */
            QComboBox {{
                background-color: #161C2C;
                border: 2px solid #28354D;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 800;
                padding: 4px 10px;
                min-height: 28px;
            }}
            QComboBox:hover {{
                border: 2px solid #3B4B6E;
            }}
            QComboBox:focus {{
                border: 2px solid #00F0FF;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #28354D;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #1E283D;
            }}
            QComboBox::drop-down:hover {{
                background-color: #2D3D5E;
            }}
            QComboBox::down-arrow {{
                image: url({combo_down_url});
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #111522;
                border: 2px solid #28354D;
                selection-background-color: #CCFF00;
                selection-color: #080A0F;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                padding: 6px;
            }}
            
            /* QCheckBox */
            QCheckBox {{
                color: #E2E8F0;
                font-size: 13px;
                font-weight: 700;
                spacing: 12px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid #3B4B6E;
                border-radius: 6px;
                background-color: #161C2C;
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid #CCFF00;
            }}
            QCheckBox::indicator:checked {{
                background-color: #CCFF00;
                border: 2px solid #CCFF00;
            }}

            /* Botonera */
            QPushButton.primary-btn {{
                background-color: #CCFF00;
                color: #080A0F;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 1.5px;
                border: none;
                border-radius: 10px;
                padding: 8px 18px;
                min-height: 32px;
            }}
            QPushButton.primary-btn:hover {{
                background-color: #E0FF4F;
            }}
            QPushButton.cancel-btn {{
                background-color: #161C2C;
                color: #94A3B8;
                border: 2px solid #28354D;
                border-radius: 10px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 800;
                min-height: 32px;
            }}
            QPushButton.cancel-btn:hover {{
                background-color: #1F283E;
                color: #FFFFFF;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        # -------------------------------------------------------------
        # Encabezado
        # -------------------------------------------------------------
        head_box = QVBoxLayout()
        head_box.setSpacing(2)
        
        badge = QLabel("⚡ SMARTBREAK • PARÁMETROS BIOMÉTRICOS")
        badge.setStyleSheet("color: #00F0FF; font-size: 11px; font-weight: 900; letter-spacing: 2px;")
        head_box.addWidget(badge)

        title = QLabel("CONFIGURACIÓN DE RENDIMIENTO")
        title.setStyleSheet("font-size: 18px; font-weight: 900; color: #FFFFFF;")
        head_box.addWidget(title)

        subtitle = QLabel("Personaliza tus umbrales ergonómicos y el ejercicio para desbloquear.")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        head_box.addWidget(subtitle)
        main_layout.addLayout(head_box)

        # -------------------------------------------------------------
        # Tarjeta 1: Monitoreo de Carga y Fatiga con Feedback en Tiempo Real
        # -------------------------------------------------------------
        card_fatigue = QFrame()
        card_fatigue.setProperty("class", "card")
        self._apply_shadow(card_fatigue)
        fatigue_layout = QVBoxLayout(card_fatigue)
        fatigue_layout.setContentsMargins(14, 10, 14, 10)
        fatigue_layout.setSpacing(6)

        tag_1 = QLabel("1. MONITOREO DE CARGA Y POSTURA")
        tag_1.setProperty("class", "section-tag")
        fatigue_layout.addWidget(tag_1)

        # Control 1: Tiempo Sentado Máximo (Slider + Label Dinámico)
        col_sit = QVBoxLayout()
        col_sit.setSpacing(4)
        lbl_sit_title = QLabel("Tiempo sentado máximo permitido:")
        lbl_sit_title.setProperty("class", "field-label")
        col_sit.addWidget(lbl_sit_title)

        row_sit = QHBoxLayout()
        row_sit.setSpacing(10)
        self.slider_sitting = QSlider(Qt.Orientation.Horizontal)
        self.slider_sitting.setRange(10, 180)
        self.slider_sitting.setValue(self.settings.max_sitting_minutes)
        self.slider_sitting.setCursor(Qt.CursorShape.PointingHandCursor)
        row_sit.addWidget(self.slider_sitting)

        self.lbl_sit_val = QLabel(f"{self.settings.max_sitting_minutes} min")
        self.lbl_sit_val.setProperty("class", "slider-feedback")
        self.lbl_sit_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_sit.addWidget(self.lbl_sit_val)
        col_sit.addLayout(row_sit)
        fatigue_layout.addLayout(col_sit)

        # Control 2: Mala Postura Continua (Slider + Label Dinámico)
        col_bad = QVBoxLayout()
        col_bad.setSpacing(4)
        lbl_bad_title = QLabel("Tolerancia continua de mala postura:")
        lbl_bad_title.setProperty("class", "field-label")
        col_bad.addWidget(lbl_bad_title)

        row_bad = QHBoxLayout()
        row_bad.setSpacing(10)
        self.slider_bad = QSlider(Qt.Orientation.Horizontal)
        self.slider_bad.setRange(2, 60)
        self.slider_bad.setValue(self.settings.max_bad_posture_minutes)
        self.slider_bad.setCursor(Qt.CursorShape.PointingHandCursor)
        row_bad.addWidget(self.slider_bad)

        self.lbl_bad_val = QLabel(f"{self.settings.max_bad_posture_minutes} min")
        self.lbl_bad_val.setProperty("class", "slider-feedback")
        self.lbl_bad_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_bad.addWidget(self.lbl_bad_val)
        col_bad.addLayout(row_bad)
        fatigue_layout.addLayout(col_bad)

        # Conectar eventos en tiempo real (Directiva 5)
        self.slider_sitting.valueChanged.connect(self._on_sitting_changed)
        self.slider_bad.valueChanged.connect(self._on_bad_posture_changed)

        main_layout.addWidget(card_fatigue)

        # -------------------------------------------------------------
        # Tarjeta 2: Ejercicio de Desbloqueo Activo
        # -------------------------------------------------------------
        card_exercise = QFrame()
        card_exercise.setProperty("class", "card")
        self._apply_shadow(card_exercise)
        ex_layout = QVBoxLayout(card_exercise)
        ex_layout.setContentsMargins(14, 10, 14, 10)
        ex_layout.setSpacing(6)

        tag_2 = QLabel("2. OBJETIVO DE DESBLOQUEO ACTIVO")
        tag_2.setProperty("class", "section-tag")
        ex_layout.addWidget(tag_2)

        # Fila 1: Selector de Ejercicio
        col_combo = QVBoxLayout()
        col_combo.setSpacing(4)
        lbl_ex_type = QLabel("Modalidad de ejercicio guiado:")
        lbl_ex_type.setProperty("class", "field-label")
        col_combo.addWidget(lbl_ex_type)

        self.combo_exercise = QComboBox()
        self.combo_exercise.addItem("Brazos sobre la cabeza (Estiramiento Overhead)", "overhead_stretch")
        self.combo_exercise.addItem("Sentadillas profundas (Deep Squats)", "squats")
        idx = 0 if self.settings.exercise_type == "overhead_stretch" else 1
        self.combo_exercise.setCurrentIndex(idx)
        self.combo_exercise.setCursor(Qt.CursorShape.PointingHandCursor)
        col_combo.addWidget(self.combo_exercise)
        ex_layout.addLayout(col_combo)

        # Fila 2: Duración y Repeticiones (Con QSpinBox estilizados con flechas ▲ y ▼)
        row_metrics = QHBoxLayout()
        row_metrics.setSpacing(10)

        # Columna Duración
        col_dur = QVBoxLayout()
        col_dur.setSpacing(4)
        lbl_dur = QLabel("Duración objetivo:")
        lbl_dur.setProperty("class", "field-label")
        col_dur.addWidget(lbl_dur)

        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(15, 300)
        self.spin_duration.setSuffix(" seg")
        self.spin_duration.setValue(self.settings.exercise_duration_seconds)
        self.spin_duration.setCursor(Qt.CursorShape.PointingHandCursor)
        col_dur.addWidget(self.spin_duration)
        row_metrics.addLayout(col_dur)

        # Columna Repeticiones
        col_reps = QVBoxLayout()
        col_reps.setSpacing(4)
        lbl_reps = QLabel("Repeticiones requeridas:")
        lbl_reps.setProperty("class", "field-label")
        col_reps.addWidget(lbl_reps)

        self.spin_reps = QSpinBox()
        self.spin_reps.setRange(3, 50)
        self.spin_reps.setSuffix(" reps")
        self.spin_reps.setValue(self.settings.exercise_target_reps)
        self.spin_reps.setCursor(Qt.CursorShape.PointingHandCursor)
        col_reps.addWidget(self.spin_reps)
        row_metrics.addLayout(col_reps)

        ex_layout.addLayout(row_metrics)
        main_layout.addWidget(card_exercise)

        # -------------------------------------------------------------
        # Tarjeta 3: Dispositivo y Arranque
        # -------------------------------------------------------------
        card_sys = QFrame()
        card_sys.setProperty("class", "card")
        self._apply_shadow(card_sys)
        sys_layout = QVBoxLayout(card_sys)
        sys_layout.setContentsMargins(14, 10, 14, 10)
        sys_layout.setSpacing(6)

        tag_3 = QLabel("3. DISPOSITIVO Y SISTEMA OPERATIVO")
        tag_3.setProperty("class", "section-tag")
        sys_layout.addWidget(tag_3)

        # Fila Cámara (Detección 100% Automática)
        row_cam = QHBoxLayout()
        row_cam.setSpacing(10)
        lbl_cam = QLabel("Cámara web activa:")
        lbl_cam.setProperty("class", "field-label")
        row_cam.addWidget(lbl_cam)
        row_cam.addStretch()

        self.combo_camera = AutoDetectCameraComboBox(on_before_popup=self._populate_cameras)
        self.combo_camera.setMinimumWidth(320)
        self.combo_camera.setCursor(Qt.CursorShape.PointingHandCursor)
        row_cam.addWidget(self.combo_camera)

        sys_layout.addLayout(row_cam)

        self.lbl_cam_status = QLabel("")
        self.lbl_cam_status.setWordWrap(True)
        self.lbl_cam_status.setStyleSheet("color: #00F0FF; font-size: 11px; font-weight: 600; margin-top: 2px; margin-bottom: 6px;")
        sys_layout.addWidget(self.lbl_cam_status)

        # Carga inicial automática de dispositivos detectados
        self._populate_cameras(self.settings.camera_index)

        # Checkbox Iniciar con Windows
        self.chk_windows = QCheckBox("Iniciar SmartBreak automáticamente con Windows")
        self.chk_windows.setChecked(self.settings.start_with_windows)
        self.chk_windows.setCursor(Qt.CursorShape.PointingHandCursor)
        sys_layout.addWidget(self.chk_windows)

        main_layout.addWidget(card_sys)

        # -------------------------------------------------------------
        # Botonera de Acción
        # -------------------------------------------------------------
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setProperty("class", "cancel-btn")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("⚡ GUARDAR PARÁMETROS")
        btn_save.setProperty("class", "primary-btn")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(btn_save)

        main_layout.addLayout(btn_layout)

    def _on_sitting_changed(self, value: int) -> None:
        """Actualiza el label numérico en tiempo real."""
        self.lbl_sit_val.setText(f"{value} min")

    def _on_bad_posture_changed(self, value: int) -> None:
        """Actualiza el label numérico en tiempo real."""
        self.lbl_bad_val.setText(f"{value} min")

    def _populate_cameras(self, target_index: int | None = None) -> None:
        """Escanea el sistema y carga automáticamente los nombres reales de las cámaras disponibles."""
        if target_index is None:
            target_index = self.combo_camera.currentData() if self.combo_camera.count() > 0 else self.settings.camera_index

        self.combo_camera.blockSignals(True)
        self.combo_camera.clear()
        detected = get_available_cameras()
        found = False

        for idx, name in detected:
            self.combo_camera.addItem(name, idx)
            if idx == target_index:
                found = True

        if not found and target_index is not None:
            self.combo_camera.addItem(f"Cámara {target_index} (Personalizada)", target_index)

        match_idx = self.combo_camera.findData(target_index)
        if match_idx >= 0:
            self.combo_camera.setCurrentIndex(match_idx)

        self.combo_camera.blockSignals(False)

        total = len(detected)
        self.lbl_cam_status.setText(f"● {total} cámara(s) detectada(s) automáticamente en Windows.")

    def showEvent(self, event) -> None:
        """Al abrir la ventana, refresca automáticamente las cámaras conectadas."""
        super().showEvent(event)
        self._populate_cameras()

    def _save_and_close(self) -> None:
        """Aplica la configuración y notifica."""
        self.settings.max_sitting_minutes = self.slider_sitting.value()
        self.settings.max_bad_posture_minutes = self.slider_bad.value()
        self.settings.exercise_type = self.combo_exercise.currentData()
        self.settings.exercise_duration_seconds = self.spin_duration.value()
        self.settings.exercise_target_reps = self.spin_reps.value()
        self.settings.camera_index = self.combo_camera.currentData()
        self.settings.start_with_windows = self.chk_windows.isChecked()
        set_autostart(self.settings.start_with_windows)

        self.settings.save()
        self.settings_updated.emit(self.settings)
        self.accept()

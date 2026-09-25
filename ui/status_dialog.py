"""
Diálogo Deportivo de Estado Ergonómico y Telemetría en Vivo para SmartBreak.
Cumple estrictamente con las directivas de frontend:
- Cero alturas fijas en etiquetas de texto (QLabel).
- Eliminación de skeleton loaders y contenedores vacíos.
- Telemetría en tiempo real con QTimer (actualización segundo a segundo).
- Tarjeta informativa completa con ejercicio configurado y consejo ergonómico real.
- Formato estricto de título: 'Estado de Rendimiento - SmartBreak'.
"""

from __future__ import annotations
from typing import Dict, Any, Callable, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QProgressBar, QPushButton, QSizePolicy
)


class StatusDialog(QDialog):
    """Ventana deportiva con telemetría biomecánica en tiempo real y cero placeholders."""

    def __init__(
        self, 
        summary: Dict[str, Any], 
        exercise_type: str = "overhead_stretch", 
        parent=None,
        summary_provider: Optional[Callable[[], Dict[str, Any]]] = None,
        camera_index: int = 0,
        camera_name: str = ""
    ):
        super().__init__(parent)
        self.summary = summary
        self.exercise_type = exercise_type
        self.summary_provider = summary_provider
        self.camera_index = camera_index
        self.camera_name = camera_name or f"Cámara #{camera_index}"
        
        # Formato de título único estricto: '{Nombre Ventana} - {Nombre App}'
        self.setWindowTitle("Estado de Rendimiento - SmartBreak")
        self.setMinimumSize(540, 560)
        self.resize(540, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._init_ui()

        # Actualización en vivo segundo a segundo si se proporciona un proveedor de datos
        if self.summary_provider is not None:
            self._timer = QTimer(self)
            self._timer.setInterval(1000)
            self._timer.timeout.connect(self._refresh_telemetry)
            self._timer.start()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #080A0F;
                color: #FFFFFF;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QFrame.card {
                background-color: #111522;
                border: 2px solid #1E2638;
                border-radius: 12px;
            }
            QLabel.brand-badge {
                color: #00F0FF;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 2px;
            }
            QLabel.title {
                font-size: 20px;
                font-weight: 900;
                color: #FFFFFF;
            }
            QLabel.metric-header {
                font-size: 11px;
                font-weight: 800;
                color: #718096;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            QLabel.metric-num {
                font-size: 15px;
                font-weight: 900;
                color: #CCFF00;
            }
            QProgressBar {
                background-color: #1A2030;
                border: 1px solid #2D3748;
                border-radius: 6px;
                text-align: center;
                height: 16px;
                font-size: 10px;
                font-weight: 800;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F0FF, stop:1 #CCFF00);
                border-radius: 5px;
            }
            QPushButton.action-btn {
                background-color: #CCFF00;
                color: #080A0F;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 1.5px;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
            }
            QPushButton.action-btn:hover {
                background-color: #E0FF4F;
            }
            QPushButton.action-btn:pressed {
                background-color: #B5E600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        # -------------------------------------------------------------
        # 1. Encabezado con Texto Elástico
        # -------------------------------------------------------------
        head_box = QVBoxLayout()
        head_box.setSpacing(2)
        
        badge = QLabel("⚡ TELEMETRÍA SMARTBREAK")
        badge.setProperty("class", "brand-badge")
        head_box.addWidget(badge)

        title = QLabel("ESTADO BIOMECÁNICO ACTUAL")
        title.setProperty("class", "title")
        head_box.addWidget(title)
        layout.addLayout(head_box)

        # -------------------------------------------------------------
        # 2. Sensores Superiores: Presencia y Postura
        # -------------------------------------------------------------
        status_row = QHBoxLayout()
        status_row.setSpacing(12)

        # Tarjeta Presencia
        card_presence = QFrame()
        card_presence.setProperty("class", "card")
        p_layout = QVBoxLayout(card_presence)
        p_layout.setContentsMargins(14, 10, 14, 10)
        p_layout.setSpacing(3)
        
        lbl_p = QLabel("SENSOR DE PRESENCIA")
        lbl_p.setProperty("class", "metric-header")
        p_layout.addWidget(lbl_p)

        is_pres = self.summary.get("is_present", False)
        self.val_pres = QLabel("● EN ESCRITORIO" if is_pres else "○ AUSENTE")
        self.val_pres.setStyleSheet(
            "color: #CCFF00; font-size: 13px; font-weight: 900;" if is_pres 
            else "color: #FF5E7E; font-size: 13px; font-weight: 900;"
        )
        p_layout.addWidget(self.val_pres)

        self.lbl_camera = QLabel(f"📷 {self.camera_name}")
        self.lbl_camera.setStyleSheet("color: #718096; font-size: 10px; font-weight: 600;")
        p_layout.addWidget(self.lbl_camera)
        status_row.addWidget(card_presence)

        # Tarjeta Postura
        card_posture = QFrame()
        card_posture.setProperty("class", "card")
        post_layout = QVBoxLayout(card_posture)
        post_layout.setContentsMargins(14, 10, 14, 10)
        post_layout.setSpacing(3)
        
        lbl_post = QLabel("CALIDAD POSTURAL")
        lbl_post.setProperty("class", "metric-header")
        post_layout.addWidget(lbl_post)

        is_bad = self.summary.get("is_bad_posture", False)
        if not is_pres:
            post_text = "— EN ESPERA"
            post_style = "color: #718096; font-size: 13px; font-weight: 900;"
        elif is_bad:
            post_text = "⚠️ MALA POSTURA"
            post_style = "color: #FF5E7E; font-size: 13px; font-weight: 900;"
        else:
            post_text = "✓ ERGONÓMICA"
            post_style = "color: #00F0FF; font-size: 13px; font-weight: 900;"

        self.val_post = QLabel(post_text)
        self.val_post.setStyleSheet(post_style)
        post_layout.addWidget(self.val_post)

        lbl_post_hint = QLabel("Alineación cervical y torso")
        lbl_post_hint.setStyleSheet("color: #718096; font-size: 10px; font-weight: 600;")
        post_layout.addWidget(lbl_post_hint)
        status_row.addWidget(card_posture)

        layout.addLayout(status_row)

        # -------------------------------------------------------------
        # 3. Nota explicativa sobre el Sensor de Presencia
        # -------------------------------------------------------------
        lbl_info = QLabel("💡 El sensor pausa automáticamente los contadores si no estás en el escritorio.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #64748B; font-size: 10.5px; font-weight: 600; padding: 0 4px;")
        layout.addWidget(lbl_info)

        # -------------------------------------------------------------
        # 4. Tarjeta de Carga Acumulada: Tiempo Sentado
        # -------------------------------------------------------------
        card_sit = QFrame()
        card_sit.setProperty("class", "card")
        sit_layout = QVBoxLayout(card_sit)
        sit_layout.setContentsMargins(16, 10, 16, 10)
        sit_layout.setSpacing(6)

        sit_head = QHBoxLayout()
        sit_lbl = QLabel("TIEMPO SENTADO ACUMULADO")
        sit_lbl.setProperty("class", "metric-header")
        sit_head.addWidget(sit_lbl)
        sit_head.addStretch()

        sit_s = int(self.summary.get("sitting_seconds", self.summary.get("sitting_minutes", 0.0) * 60))
        max_sit_m = self.summary.get("max_sitting_minutes", 50)
        self.sit_val = QLabel(f"{sit_s // 60:02d}m {sit_s % 60:02d}s / {int(max_sit_m)} min")
        self.sit_val.setProperty("class", "metric-num")
        sit_head.addWidget(self.sit_val)
        sit_layout.addLayout(sit_head)

        self.bar_sit = QProgressBar()
        self.bar_sit.setRange(0, 100)
        self.bar_sit.setValue(int(self.summary.get("percent_sitting", 0.0)))
        sit_layout.addWidget(self.bar_sit)
        layout.addWidget(card_sit)

        # -------------------------------------------------------------
        # 5. Tarjeta de Mala Postura Continua
        # -------------------------------------------------------------
        card_bad = QFrame()
        card_bad.setProperty("class", "card")
        bad_layout = QVBoxLayout(card_bad)
        bad_layout.setContentsMargins(16, 10, 16, 10)
        bad_layout.setSpacing(6)

        bad_head = QHBoxLayout()
        bad_lbl = QLabel("MALA POSTURA CONTINUA")
        bad_lbl.setProperty("class", "metric-header")
        bad_head.addWidget(bad_lbl)
        bad_head.addStretch()

        bad_s = int(self.summary.get("bad_posture_seconds", self.summary.get("bad_posture_minutes", 0.0) * 60))
        max_bad_m = self.summary.get("max_bad_posture_minutes", 15)
        self.bad_val = QLabel(f"{bad_s // 60:02d}m {bad_s % 60:02d}s / {int(max_bad_m)} min")
        self.bad_val.setStyleSheet("color: #FF5E7E; font-size: 15px; font-weight: 900;")
        bad_head.addWidget(self.bad_val)
        bad_layout.addLayout(bad_head)

        self.bar_bad = QProgressBar()
        self.bar_bad.setRange(0, 100)
        self.bar_bad.setValue(int(self.summary.get("percent_bad_posture", 0.0)))
        bad_layout.addWidget(self.bar_bad)
        layout.addWidget(card_bad)

        # -------------------------------------------------------------
        # 6. Tarjeta de Pausa Obligatoria & Consejo Ergonómico
        # -------------------------------------------------------------
        card_next = QFrame()
        card_next.setProperty("class", "card")
        card_next.setStyleSheet("""
            background-color: #141A28;
            border: 2px solid #2B3852;
            border-radius: 12px;
        """)
        next_layout = QVBoxLayout(card_next)
        next_layout.setContentsMargins(16, 10, 16, 10)
        next_layout.setSpacing(6)

        info_row = QHBoxLayout()
        
        col_time = QVBoxLayout()
        col_time.setSpacing(2)
        lbl_p_time = QLabel("PRÓXIMA PAUSA EN:")
        lbl_p_time.setProperty("class", "metric-header")
        col_time.addWidget(lbl_p_time)
        
        rem_m = self.summary.get("minutes_until_break", 0.0)
        rem_s = int(rem_m * 60)
        self.val_p_time = QLabel(f"{rem_s // 60:02d}m {rem_s % 60:02d}s")
        self.val_p_time.setStyleSheet("font-size: 18px; font-weight: 900; color: #CCFF00;")
        col_time.addWidget(self.val_p_time)
        info_row.addLayout(col_time)
        
        info_row.addStretch()

        col_ex = QVBoxLayout()
        col_ex.setSpacing(2)
        lbl_p_ex = QLabel("EJERCICIO PROGRAMADO:")
        lbl_p_ex.setProperty("class", "metric-header")
        col_ex.addWidget(lbl_p_ex)
        
        ex_name = "Estiramiento Overhead" if self.exercise_type == "overhead_stretch" else "Sentadillas Profundas"
        self.val_p_ex = QLabel(f"⚡ {ex_name}")
        self.val_p_ex.setStyleSheet("font-size: 14px; font-weight: 800; color: #00F0FF;")
        col_ex.addWidget(self.val_p_ex)
        info_row.addLayout(col_ex)

        next_layout.addLayout(info_row)

        tip_text = QLabel("💡 Consejo: Mantén la pantalla a la altura de los ojos para liberar tensión en C5-C7.")
        tip_text.setWordWrap(True)
        tip_text.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600; line-height: 1.3;")
        next_layout.addWidget(tip_text)

        layout.addWidget(card_next)

        # -------------------------------------------------------------
        # 7. Botón de Acción Inferior
        # -------------------------------------------------------------
        btn_close = QPushButton("⚡ ENTENDIDO")
        btn_close.setProperty("class", "action-btn")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _refresh_telemetry(self) -> None:
        """Actualiza todos los indicadores numéricos y estados en tiempo real."""
        if not self.summary_provider:
            return
        try:
            summary = self.summary_provider()
            self._update_metrics(summary)
        except Exception as e:
            print(f"[StatusDialog] Error en refresco de telemetría: {e}")

    def _update_metrics(self, summary: Dict[str, Any]) -> None:
        """Aplica los datos actualizados a los widgets existentes."""
        self.summary = summary
        is_pres = summary.get("is_present", False)
        
        # Sensor de presencia
        if is_pres:
            self.val_pres.setText("● EN ESCRITORIO")
            self.val_pres.setStyleSheet("color: #CCFF00; font-size: 13px; font-weight: 900;")
        else:
            self.val_pres.setText("○ AUSENTE")
            self.val_pres.setStyleSheet("color: #FF5E7E; font-size: 13px; font-weight: 900;")

        # Calidad postural
        is_bad = summary.get("is_bad_posture", False)
        if not is_pres:
            self.val_post.setText("— EN ESPERA")
            self.val_post.setStyleSheet("color: #718096; font-size: 13px; font-weight: 900;")
        elif is_bad:
            self.val_post.setText("⚠️ MALA POSTURA")
            self.val_post.setStyleSheet("color: #FF5E7E; font-size: 13px; font-weight: 900;")
        else:
            self.val_post.setText("✓ ERGONÓMICA")
            self.val_post.setStyleSheet("color: #00F0FF; font-size: 13px; font-weight: 900;")

        # Tiempo sentado
        sit_s = int(summary.get("sitting_seconds", summary.get("sitting_minutes", 0.0) * 60))
        max_sit_m = summary.get("max_sitting_minutes", 50)
        self.sit_val.setText(f"{sit_s // 60:02d}m {sit_s % 60:02d}s / {int(max_sit_m)} min")
        self.bar_sit.setValue(int(summary.get("percent_sitting", 0.0)))

        # Mala postura
        bad_s = int(summary.get("bad_posture_seconds", summary.get("bad_posture_minutes", 0.0) * 60))
        max_bad_m = summary.get("max_bad_posture_minutes", 15)
        self.bad_val.setText(f"{bad_s // 60:02d}m {bad_s % 60:02d}s / {int(max_bad_m)} min")
        self.bar_bad.setValue(int(summary.get("percent_bad_posture", 0.0)))

        # Próxima pausa
        rem_m = summary.get("minutes_until_break", 0.0)
        rem_s = int(rem_m * 60)
        self.val_p_time.setText(f"{rem_s // 60:02d}m {rem_s % 60:02d}s")

"""
Lienzo de Renderizado de Video y HUD Deportivo de Alto Rendimiento para SmartBreak.
Estilo athletic fitness-tech (Nike Training / Apple Fitness HUD) con esquinas tácticas,
telemetría biomecánica en tiempo real y banners de máxima legibilidad y contraste.
"""

from __future__ import annotations
import cv2
import numpy as np
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtWidgets import QWidget


class VideoCanvas(QWidget):
    """
    Widget con estética deportiva y HUD biomecánico de alta visibilidad.
    Renderiza el feed de cámara en tiempo real con brackets tácticos y telemetría.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.current_pixmap: QPixmap | None = None
        
        # Telemetría deportiva
        self.feedback_message: str = "Buscando postura..."
        self.progress_percent: float = 0.0
        self.is_standing: bool = False
        self.knee_angle: float = 0.0
        self.requires_standing: bool = False
        self.current_fps: int = 30

    def update_frame(self, frame_bgr: np.ndarray, 
                     feedback: str = "", 
                     progress: float = 0.0, 
                     is_standing: bool = False, 
                     knee_angle: float = 0.0,
                     requires_standing: bool = False) -> None:
        """
        Recibe el frame procesado por OpenCV y actualiza el renderizado del lienzo.
        """
        if frame_bgr is None:
            return

        self.feedback_message = feedback
        self.progress_percent = progress
        self.is_standing = is_standing
        self.knee_angle = knee_angle
        self.requires_standing = requires_standing

        # Convertir frame BGR de OpenCV a QImage con efecto espejo
        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        flipped = cv2.flip(frame_bgr, 1)
        rgb_frame = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)
        
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        self.current_pixmap = QPixmap.fromImage(q_img)
        self.update()

    def paintEvent(self, event) -> None:
        """Renderiza el fotograma de cámara y el HUD deportivo de alto rendimiento."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor(8, 10, 16))  # Fondo negro carbono profundo

        if self.current_pixmap and not self.current_pixmap.isNull():
            # Calcular geometría manteniendo relación de aspecto sin alocar nuevo QPixmap en cada frame
            pix_size = self.current_pixmap.size()
            scaled_size = pix_size.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x_offset = (rect.width() - scaled_size.width()) // 2
            y_offset = (rect.height() - scaled_size.height()) // 2
            target_rect = QRect(x_offset, y_offset, scaled_size.width(), scaled_size.height())

            # Dibujar feed de video directamente escalado
            painter.drawPixmap(target_rect, self.current_pixmap)
            
            # Marco exterior deportivo con acento Neón Volt, Cyan o Rojo Alerta
            if self.is_standing:
                accent_color = QColor(204, 255, 0)
            elif not self.requires_standing:
                accent_color = QColor(0, 240, 255)
            else:
                accent_color = QColor(255, 45, 85)

            painter.setPen(QPen(accent_color, 3))
            painter.drawRoundedRect(target_rect, 14, 14)

            # 1. Dibujar brackets tácticos de fitness en las 4 esquinas
            self._draw_tactical_corners(painter, target_rect, accent_color)

            # 2. Barra de telemetría superior
            self._draw_top_telemetry(painter, target_rect)

            # 3. Banner deportivo inferior de feedback y progreso
            self._draw_sports_hud_banner(painter, target_rect, accent_color)

        else:
            # Estado sin feed disponible
            painter.setPen(QColor(160, 174, 192))
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "⚡ SINCRONIZANDO SENSOR BIOMÉTRICO...")

        painter.end()

    def _draw_tactical_corners(self, painter: QPainter, target_rect: QRect, color: QColor) -> None:
        """Dibuja marcas tácticas en las esquinas al estilo monitor deportivo."""
        pen = QPen(color, 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        arm = 30
        pad = 8
        l, r, t, b = target_rect.left() + pad, target_rect.right() - pad, target_rect.top() + pad, target_rect.bottom() - pad

        # Esquina Superior Izquierda
        painter.drawLine(l, t, l + arm, t)
        painter.drawLine(l, t, l, t + arm)
        # Esquina Superior Derecha
        painter.drawLine(r, t, r - arm, t)
        painter.drawLine(r, t, r, t + arm)
        # Esquina Inferior Izquierda
        painter.drawLine(l, b, l + arm, b)
        painter.drawLine(l, b, l, b - arm)
        # Esquina Inferior Derecha
        painter.drawLine(r, b, r - arm, b)
        painter.drawLine(r, b, r, b - arm)

    def _draw_top_telemetry(self, painter: QPainter, target_rect: QRect) -> None:
        """Barra superior con métricas biomecánicas en vivo."""
        top_bar_rect = QRect(target_rect.left() + 20, target_rect.top() + 18, target_rect.width() - 40, 36)
        
        # Fondo oscuro traslúcido
        painter.setBrush(QBrush(QColor(10, 12, 18, 220)))
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
        painter.drawRoundedRect(top_bar_rect, 8, 8)

        # Badge: LIVE / EN VIVO
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.ExtraBold))
        painter.setPen(QColor(204, 255, 0))  # Volt Neón
        painter.drawText(
            QRect(top_bar_rect.left() + 14, top_bar_rect.top(), 160, 36),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            "● AI POSE TRACKER"
        )

        # Centro: Ángulo articular o estado de escritorio
        if self.knee_angle > 0 and self.requires_standing:
            angle_text = f"ÁNGULO DE PIERNA: {self.knee_angle:.1f}°"
        elif not self.requires_standing:
            angle_text = "EJERCICIO DE ESCRITORIO • ACTIVO"
        else:
            angle_text = "CALIBRANDO CUERPO..."

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(
            top_bar_rect,
            Qt.AlignmentFlag.AlignCenter,
            angle_text
        )

        # Derecha: Estado de postura
        if self.is_standing or not self.requires_standing:
            status_text = "BIOMECÁNICA ALINEADA"
            status_color = QColor(0, 240, 255)
        else:
            status_text = "REQUIERE ELEVACIÓN"
            status_color = QColor(255, 45, 85)

        painter.setPen(status_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.ExtraBold))
        painter.drawText(
            QRect(top_bar_rect.right() - 210, top_bar_rect.top(), 195, 36),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            status_text
        )

    def _draw_sports_hud_banner(self, painter: QPainter, target_rect: QRect, accent_color: QColor) -> None:
        """Dibuja el banner inferior deportivo con feedback de alta visibilidad."""
        banner_height = 80
        banner_rect = QRect(
            target_rect.left() + 20,
            target_rect.bottom() - banner_height - 20,
            target_rect.width() - 40,
            banner_height
        )

        # Fondo glassmorphic ultra oscuro de alto contraste
        painter.setBrush(QBrush(QColor(12, 16, 26, 235)))
        painter.setPen(QPen(accent_color, 1.5))
        painter.drawRoundedRect(banner_rect, 14, 14)

        # Pill Badge a la izquierda: ESTADO
        pill_rect = QRect(banner_rect.left() + 16, banner_rect.top() + 12, 140, 26)
        if self.is_standing:
            pill_bg = QColor(204, 255, 0, 40)
            pill_border = QColor(204, 255, 0)
            pill_text = "⚡ DE PIE"
        elif not self.requires_standing:
            pill_bg = QColor(0, 240, 255, 40)
            pill_border = QColor(0, 240, 255)
            pill_text = "🪑 ESCRITORIO"
        else:
            pill_bg = QColor(255, 45, 85, 40)
            pill_border = QColor(255, 45, 85)
            pill_text = "⚠️ SENTADO"

        painter.setBrush(QBrush(pill_bg))
        painter.setPen(QPen(pill_border, 1.5))
        painter.drawRoundedRect(pill_rect, 13, 13)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.ExtraBold))
        painter.setPen(pill_border)
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, pill_text)

        # Mensaje de feedback en texto grande y nítido
        msg_rect = QRect(
            pill_rect.right() + 16, 
            banner_rect.top() + 8, 
            banner_rect.width() - pill_rect.width() - 45, 
            32
        )
        painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(msg_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.feedback_message)

        # Barra de progreso deportiva
        bar_bg_rect = QRectF(banner_rect.left() + 16, banner_rect.top() + 48, banner_rect.width() - 90, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(26, 32, 48))
        painter.drawRoundedRect(bar_bg_rect, 8, 8)

        # Relleno con degradado deportivo Neón Volt a Cyan Eléctrico
        fill_width = (bar_bg_rect.width() * min(100.0, max(0.0, self.progress_percent))) / 100.0
        if fill_width > 0:
            fill_rect = QRectF(bar_bg_rect.left(), bar_bg_rect.top(), fill_width, bar_bg_rect.height())
            grad = QLinearGradient(fill_rect.left(), fill_rect.top(), fill_rect.right(), fill_rect.top())
            grad.setColorAt(0.0, QColor(0, 240, 255))   # Cyan Eléctrico
            grad.setColorAt(1.0, QColor(204, 255, 0))   # Volt Neón
            painter.setBrush(grad)
            painter.drawRoundedRect(fill_rect, 8, 8)

        # Texto del porcentaje numérico
        pct_text = f"{int(self.progress_percent)}%"
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.ExtraBold))
        painter.setPen(QColor(204, 255, 0))
        pct_rect = QRect(banner_rect.right() - 65, banner_rect.top() + 44, 55, 22)
        painter.drawText(pct_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, pct_text)

"""
Módulo de Gestión de la Bandeja del Sistema (System Tray) para Windows con pystray.
Ejecuta el menú contextual y notificaciones en un hilo secundario coordinado con PyQt6.
"""

from __future__ import annotations
import threading
from pathlib import Path
from typing import Callable, Optional
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except Exception as e:
    print(f"[TrayManager] Advertencia: pystray no disponible: {e}")
    pystray = None
    PYSTRAY_AVAILABLE = False


def create_default_icon_image(size: int = 64) -> Image.Image:
    """Genera dinámicamente un icono ergonómico de alta fidelidad si no existe en disco."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Círculo de fondo verde azulado
    padding = 4
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(0, 230, 150, 255),
        outline=(255, 255, 255, 200),
        width=2
    )
    
    # Letra 'S' o símbolo estilizado de pausa activa (dos barras + figura humana)
    bar_w = 6
    bar_h = 24
    top_y = (size - bar_h) // 2
    
    # Barra izquierda y derecha
    draw.rectangle([size // 2 - 10, top_y, size // 2 - 10 + bar_w, top_y + bar_h], fill=(13, 15, 23, 255))
    draw.rectangle([size // 2 + 4, top_y, size // 2 + 4 + bar_w, top_y + bar_h], fill=(13, 15, 23, 255))
    
    return img


class TrayManager:
    """
    Administrador de la bandeja del sistema usando pystray.
    Desacopla la interacción con el usuario del hilo principal de PyQt6.
    """

    def __init__(self, 
                 icon_path: Optional[str] = None,
                 on_show_status: Optional[Callable[[], None]] = None,
                 on_force_break: Optional[Callable[[], None]] = None,
                 on_open_config: Optional[Callable[[], None]] = None,
                 on_exit_app: Optional[Callable[[], None]] = None):

        self.icon_path = icon_path
        self.on_show_status = on_show_status
        self.on_force_break = on_force_break
        self.on_open_config = on_open_config
        self.on_exit_app = on_exit_app

        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _load_image(self) -> Image.Image:
        """Carga la imagen del icono desde disco o la sintetiza."""
        if self.icon_path and Path(self.icon_path).exists():
            try:
                return Image.open(self.icon_path)
            except Exception:
                pass
        return create_default_icon_image()

    def start(self) -> None:
        """Inicia el icono en la bandeja dentro de un hilo daemon de segundo plano."""
        if not PYSTRAY_AVAILABLE:
            print("[TrayManager] Error: No se puede iniciar bandeja sin pystray.")
            return

        icon_image = self._load_image()

        # Construcción del menú contextual requerido:
        # "Estado actual", "Forzar pausa activa", "Configurar intervalos", "Salir"
        menu = (
            item("📊 Estado actual", lambda icon, item: self._safe_call(self.on_show_status)),
            item("⚡ Forzar pausa activa", lambda icon, item: self._safe_call(self.on_force_break)),
            item("⚙️ Configurar intervalos", lambda icon, item: self._safe_call(self.on_open_config)),
            pystray.Menu.SEPARATOR,
            item("❌ Salir", lambda icon, item: self._handle_exit())
        )

        self.icon = pystray.Icon(
            name="SmartBreak",
            icon=icon_image,
            title="SmartBreak - Monitor Ergonómico Activo",
            menu=pystray.Menu(*menu)
        )

        self._thread = threading.Thread(target=self.icon.run, daemon=True, name="TrayThread")
        self._thread.start()

    def _safe_call(self, callback: Optional[Callable[[], None]]) -> None:
        """Invoca un callback capturando excepciones en el hilo."""
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"[TrayManager] Error en callback de menú: {e}")

    def _handle_exit(self) -> None:
        """Detiene el icono y notifica al orquestador para terminar la aplicación."""
        if self.icon:
            self.icon.stop()
        if self.on_exit_app:
            self.on_exit_app()

    def notify(self, title: str, message: str) -> None:
        """Envía una notificación emergente a la bandeja de Windows."""
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                print(f"[TrayManager] No se pudo enviar notificación de bandeja: {e}")

    def update_tooltip(self, text: str) -> None:
        """Actualiza el texto flotante del icono en la bandeja."""
        if self.icon:
            self.icon.title = text

    def stop(self) -> None:
        """Detiene el icono de la bandeja."""
        if self.icon:
            self.icon.stop()
            self.icon = None

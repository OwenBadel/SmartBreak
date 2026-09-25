"""
Módulo de Configuración Central y Persistencia para SmartBreak.
Gestiona umbrales ergonómicos, tiempos de descanso, tolerancias y persistencia JSON.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Any, Dict


@dataclass
class Settings:
    """Configuración general de SmartBreak."""

    # Tiempos de fatiga (en minutos)
    max_sitting_minutes: int = 50           # Pausa obligatoria tras 50 minutos sentado
    max_bad_posture_minutes: int = 15      # Pausa obligatoria tras 15 minutos continuos de mala postura
    
    # Requisitos de ejercicio para desbloqueo
    exercise_type: str = "overhead_stretch"  # "overhead_stretch" (brazos arriba) o "squats" (sentadillas)
    exercise_duration_seconds: int = 60     # Segundos requeridos si el ejercicio es por tiempo
    exercise_target_reps: int = 10          # Repeticiones requeridas si el ejercicio es por conteo
    
    # Muestreo y cámara
    passive_sample_interval_sec: float = 0.8  # Muestreo a bajo consumo (aprox 1.25 FPS)
    active_target_fps: int = 30               # FPS en pantalla completa de ejercicio
    camera_index: int = 0                     # Índice de la cámara OpenCV por defecto
    
    # Umbrales trigonométricos de postura
    neck_angle_threshold_deg: float = 35.0    # Grados de inclinación cervical (cuello adelantado)
    torso_angle_threshold_deg: float = 22.0   # Grados de inclinación torácica (columna encorvada)
    standing_leg_angle_threshold: float = 165.0 # Ángulo cadera-rodilla-tobillo para considerar al usuario de pie
    
    # Opciones de interfaz y sistema
    start_with_windows: bool = True
    notifications_enabled: bool = True
    debug_mode: bool = False
    
    # Rutas
    config_dir: str = field(default_factory=lambda: str(Path.home() / ".smartbreak"))
    
    @property
    def config_file_path(self) -> Path:
        return Path(self.config_dir) / "config.json"

    def save(self) -> None:
        """Guarda la configuración actual en el archivo JSON local del usuario."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error al guardar configuración: {e}")

    @classmethod
    def load(cls) -> Settings:
        """Carga la configuración desde JSON o retorna valores predeterminados."""
        instance = cls()
        if instance.config_file_path.exists():
            try:
                with open(instance.config_file_path, "r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                    for key, val in data.items():
                        if hasattr(instance, key):
                            setattr(instance, key, val)
            except Exception as e:
                print(f"[Config] Error al leer configuración existente ({e}), usando defaults.")
        else:
            instance.save()
        return instance

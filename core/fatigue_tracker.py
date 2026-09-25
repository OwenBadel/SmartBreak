"""
Módulo Acumulador de Fatiga y Monitor Ergonómico Temporal.
Controla el tiempo acumulado de sedentarismo y la duración continua de mala postura.
"""

from __future__ import annotations
import time
from typing import Tuple, Dict, Any


class FatigueTracker:
    """
    Rastrea el tiempo de presencia, el sedentarismo y los episodios de mala postura.
    Dispara la señal de descanso obligatorio al alcanzar los límites configurados.
    """

    def __init__(self, max_sitting_minutes: int = 50, max_bad_posture_minutes: int = 15):
        self.max_sitting_seconds: float = float(max_sitting_minutes * 60)
        self.max_bad_posture_seconds: float = float(max_bad_posture_minutes * 60)

        # Contadores de estado
        self.sitting_seconds: float = 0.0
        self.bad_posture_seconds: float = 0.0
        self.good_posture_streak_seconds: float = 0.0
        self.absence_seconds: float = 0.0
        
        # Banderas
        self.is_present: bool = False
        self.is_bad_posture: bool = False
        self.break_triggered: bool = False
        self.trigger_reason: str = ""
        
        # Marcas de tiempo
        self.last_update_ts: float = time.time()
        self.session_start_ts: float = time.time()

    def update(self, delta_time: float, presence: bool, bad_posture: bool) -> Tuple[bool, str]:
        """
        Actualiza los contadores según el estado del último frame.
        Retorna (debe_bloquear, razon).
        """
        self.is_present = presence
        self.is_bad_posture = bad_posture

        # Si el usuario no está en el escritorio, acumulamos ausencia y aliviamos fatiga
        if not presence:
            self.absence_seconds += delta_time
            self.good_posture_streak_seconds = 0.0

            # Si el usuario se alejó más de 15 minutos (900 seg), descanso completo
            if self.absence_seconds >= 900.0:
                self.sitting_seconds = 0.0
                self.bad_posture_seconds = 0.0
            # Si se alejó más de 3 minutos (180 seg), aplicamos decaimiento progresivo
            elif self.absence_seconds > 180.0:
                self.sitting_seconds = max(0.0, self.sitting_seconds - (delta_time * 0.5))
                self.bad_posture_seconds = max(0.0, self.bad_posture_seconds - (delta_time * 0.5))

            return False, ""

        # El usuario está presente frente a la pantalla
        self.absence_seconds = 0.0
        self.sitting_seconds += delta_time

        # Monitoreo de mala postura continuada
        if bad_posture:
            self.bad_posture_seconds += delta_time
            self.good_posture_streak_seconds = 0.0
        else:
            # Buena postura sostenida
            self.good_posture_streak_seconds += delta_time
            # Si mantiene buena postura por más de 20 segundos, aliviamos progresivamente el contador de mala postura
            if self.good_posture_streak_seconds > 20.0:
                self.bad_posture_seconds = max(0.0, self.bad_posture_seconds - (delta_time * 1.5))

        # Verificación de condiciones de activación de pausa obligatoria
        if self.sitting_seconds >= self.max_sitting_seconds:
            self.break_triggered = True
            self.trigger_reason = f"Límite de tiempo sentado alcanzado ({int(self.sitting_seconds // 60)} min)"
            return True, self.trigger_reason

        if self.bad_posture_seconds >= self.max_bad_posture_seconds:
            self.break_triggered = True
            self.trigger_reason = f"Mala postura sostenida por {int(self.bad_posture_seconds // 60)} min"
            return True, self.trigger_reason

        return False, ""

    def reset_after_break(self) -> None:
        """Reinicia los contadores tras completar exitosamente la pausa activa."""
        self.sitting_seconds = 0.0
        self.bad_posture_seconds = 0.0
        self.good_posture_streak_seconds = 0.0
        self.absence_seconds = 0.0
        self.break_triggered = False
        self.trigger_reason = ""
        self.session_start_ts = time.time()

    def get_status_summary(self) -> Dict[str, Any]:
        """Genera un resumen para la interfaz de usuario y el menú de la bandeja."""
        sitting_min = self.sitting_seconds / 60.0
        bad_min = self.bad_posture_seconds / 60.0
        max_sit_min = self.max_sitting_seconds / 60.0
        max_bad_min = self.max_bad_posture_seconds / 60.0

        percent_sitting = min(100.0, (self.sitting_seconds / max(1.0, self.max_sitting_seconds)) * 100.0)
        percent_bad_posture = min(100.0, (self.bad_posture_seconds / max(1.0, self.max_bad_posture_seconds)) * 100.0)

        return {
            "is_present": self.is_present,
            "is_bad_posture": self.is_bad_posture,
            "sitting_minutes": sitting_min,
            "max_sitting_minutes": max_sit_min,
            "percent_sitting": percent_sitting,
            "bad_posture_minutes": bad_min,
            "max_bad_posture_minutes": max_bad_min,
            "percent_bad_posture": percent_bad_posture,
            "sitting_seconds": self.sitting_seconds,
            "bad_posture_seconds": self.bad_posture_seconds,
            "break_triggered": self.break_triggered,
            "trigger_reason": self.trigger_reason,
            "minutes_until_break": max(0.0, min(max_sit_min - sitting_min, max_bad_min - bad_min))
        }

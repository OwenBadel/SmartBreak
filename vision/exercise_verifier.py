"""
Módulo de Verificación de Ejercicios y Bipedestación para Desbloqueo.
Implementa una máquina de estados para detectar que el usuario se pone de pie
y valida la realización de ejercicios físicos (estiramiento de brazos o sentadillas).
"""

from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Any
from .posture_analyzer import PostureAnalyzer


@dataclass
class ExerciseStatus:
    """Estado en tiempo real del ejercicio de desbloqueo."""
    is_standing: bool
    knee_angle: float
    current_exercise: str
    completed_reps: int
    target_reps: int
    elapsed_seconds: float
    target_seconds: float
    progress_percent: float
    is_unlocked: bool
    feedback_message: str


class ExerciseVerifier:
    """
    Verificador de ejercicios ergonómicos para la pantalla de bloqueo.
    """

    def __init__(self, 
                 exercise_type: str = "overhead_stretch",
                 target_seconds: int = 60,
                 target_reps: int = 10,
                 standing_knee_threshold: float = 165.0):
        
        self.exercise_type = exercise_type  # "overhead_stretch" o "squats"
        self.target_seconds = float(target_seconds)
        self.target_reps = target_reps
        self.standing_knee_threshold = standing_knee_threshold

        # Variables de estado
        self.completed_reps: int = 0
        self.elapsed_seconds: float = 0.0
        self.is_unlocked: bool = False
        
        # Máquina de estados para sentadillas ("UP", "DOWN")
        self.squat_state: str = "UP"
        
        # Máquina de estados para brazos arriba
        self.arm_raise_state: str = "DOWN"
        
        # Umbrales
        self.squat_down_angle: float = 110.0
        self.squat_up_angle: float = 150.0

        # Seguimiento cinemático para encuadres de medio cuerpo (cuando las piernas no son visibles)
        self.shoulder_baseline_y: Optional[float] = None
        self.standing_stability_frames: int = 0

    def reset(self) -> None:
        """Reinicia la máquina de estados del ejercicio."""
        self.completed_reps = 0
        self.elapsed_seconds = 0.0
        self.is_unlocked = False
        self.squat_state = "UP"
        self.arm_raise_state = "DOWN"
        self.shoulder_baseline_y = None
        self.standing_stability_frames = 0

    def update(self, pose_results: Any, image_shape: Tuple[int, int, int], delta_time: float) -> ExerciseStatus:
        """
        Evalúa el frame actual y avanza el progreso del ejercicio.
        """
        h, w = image_shape[:2]

        if pose_results is None:
            return self._build_status(
                is_standing=False,
                knee_angle=0.0,
                feedback="Ponte frente a la cámara para iniciar el desbloqueo"
            )

        # Unificación de acceso a landmarks (Tasks API, Solutions API o PoseDetectionResult)
        if hasattr(pose_results, "landmarks"):
            landmarks = pose_results.landmarks
        elif hasattr(pose_results, "pose_landmarks") and pose_results.pose_landmarks:
            landmarks = getattr(pose_results.pose_landmarks, "landmark", pose_results.pose_landmarks)
        else:
            landmarks = None

        if not landmarks or len(landmarks) == 0:
            return self._build_status(
                is_standing=False,
                knee_angle=0.0,
                feedback="Ponte frente a la cámara para iniciar el desbloqueo"
            )

        def get_pt(idx: int) -> Tuple[float, float, float]:
            if idx < len(landmarks):
                lm = landmarks[idx]
                vis = getattr(lm, 'visibility', getattr(lm, 'presence', 0.9))
                return (lm.x * w, lm.y * h, vis)
            return (0.0, 0.0, 0.0)

        # Landmarks clave
        nose = get_pt(PostureAnalyzer.NOSE)
        l_sh = get_pt(PostureAnalyzer.LEFT_SHOULDER)
        r_sh = get_pt(PostureAnalyzer.RIGHT_SHOULDER)
        l_el = get_pt(PostureAnalyzer.LEFT_ELBOW)
        r_el = get_pt(PostureAnalyzer.RIGHT_ELBOW)
        l_wr = get_pt(PostureAnalyzer.LEFT_WRIST)
        r_wr = get_pt(PostureAnalyzer.RIGHT_WRIST)
        l_hip = get_pt(PostureAnalyzer.LEFT_HIP)
        r_hip = get_pt(PostureAnalyzer.RIGHT_HIP)
        l_knee = get_pt(PostureAnalyzer.LEFT_KNEE)
        r_knee = get_pt(PostureAnalyzer.RIGHT_KNEE)
        l_ank = get_pt(PostureAnalyzer.LEFT_ANKLE)
        r_ank = get_pt(PostureAnalyzer.RIGHT_ANKLE)

        # 1. Comprobar si el usuario se ha puesto de pie (Bipedestación)
        # Se calcula el ángulo cadera-rodilla-tobillo para ambas piernas
        l_leg_angle = 0.0
        r_leg_angle = 0.0
        leg_angles = []

        if l_hip[2] > 0.4 and l_knee[2] > 0.4 and l_ank[2] > 0.4:
            l_leg_angle = PostureAnalyzer.calculate_angle_2d((l_hip[0], l_hip[1]), (l_knee[0], l_knee[1]), (l_ank[0], l_ank[1]))
            leg_angles.append(l_leg_angle)

        if r_hip[2] > 0.4 and r_knee[2] > 0.4 and r_ank[2] > 0.4:
            r_leg_angle = PostureAnalyzer.calculate_angle_2d((r_hip[0], r_hip[1]), (r_knee[0], r_knee[1]), (r_ank[0], r_ank[1]))
            leg_angles.append(r_leg_angle)

        # Si los tobillos están fuera del cuadro (webcam colocada alta o encuadre de medio cuerpo),
        # evaluamos si las piernas están extendidas o aplicamos seguimiento cinemático de torso
        has_legs = len(leg_angles) > 0
        if has_legs:
            current_knee_angle = float(np.mean(leg_angles))
            if self.exercise_type == "squats":
                is_standing = True
            else:
                is_standing = current_knee_angle >= self.standing_knee_threshold
        else:
            # Fallback cinemático cuando las piernas inferiores no se ven completamente (típico en webcams de escritorio)
            is_standing = (l_sh[2] > 0.35 and r_sh[2] > 0.35 and nose[2] > 0.35)
            sh_y = (l_sh[1] + r_sh[1]) / 2.0

            if self.exercise_type == "squats":
                # Calibrar o actualizar la línea base del hombro al estar erguido (menor Y en pantalla)
                if self.shoulder_baseline_y is None:
                    self.shoulder_baseline_y = sh_y
                elif sh_y < self.shoulder_baseline_y:
                    self.shoulder_baseline_y = sh_y

                delta_y = max(0.0, sh_y - self.shoulder_baseline_y)
                # Conversión de descenso vertical a ángulo articular proyectado (180° erguido -> 95° en sentadilla profunda)
                target_drop = max(40.0, h * 0.14)
                drop_ratio = max(0.0, min(1.0, delta_y / target_drop))
                current_knee_angle = 180.0 - (drop_ratio * 85.0)
            else:
                current_knee_angle = 180.0

        if not is_standing:
            return self._build_status(
                is_standing=False,
                knee_angle=current_knee_angle,
                feedback="⚠️ ¡Ponte de pie! Estira las piernas (Ángulo > 165°)"
            )

        # 2. Evaluación según el ejercicio seleccionado
        if self.exercise_type == "squats":
            feedback = self._process_squats(current_knee_angle)
            if not has_legs and "válida" not in feedback and self.squat_state == "UP":
                feedback = f"🏋️ Sentadilla activa: Flexiona profundo y sube. Llevas {self.completed_reps}/{self.target_reps}"
        else:
            # Ejercicio predeterminado: Estiramiento con brazos sobre la cabeza
            feedback = self._process_overhead_stretch(nose, l_sh, r_sh, l_el, r_el, l_wr, r_wr, delta_time)

        # 3. Comprobar si se ha cumplido el objetivo de desbloqueo
        if self.exercise_type == "squats":
            if self.completed_reps >= self.target_reps:
                self.is_unlocked = True
                feedback = "🎉 ¡Excelente trabajo! 10 sentadillas completadas. Desbloqueando..."
        else:
            # Modo estiramiento: puede ser por tiempo (60s) o por repeticiones de elevación (10 reps)
            if self.elapsed_seconds >= self.target_seconds or self.completed_reps >= self.target_reps:
                self.is_unlocked = True
                feedback = "🎉 ¡Meta cumplida! Postura y circulación restablecidas. Desbloqueando..."

        return self._build_status(
            is_standing=True,
            knee_angle=current_knee_angle,
            feedback=feedback
        )

    def _process_overhead_stretch(self, nose, l_sh, r_sh, l_el, r_el, l_wr, r_wr, delta_time: float) -> str:
        """
        Evalúa el estiramiento de brazos extendidos hacia arriba.
        Ambas muñecas deben estar por encima de la nariz y con codos extendidos.
        """
        # Muñecas por encima de la nariz o nivel superior (umbral de visibilidad 0.20 tolerante para bordes)
        left_wrist_up = l_wr[2] > 0.20 and l_wr[1] < (nose[1] + 20)
        right_wrist_up = r_wr[2] > 0.20 and r_wr[1] < (nose[1] + 20)

        # Extensión de codos (Ángulo hombro-codo-muñeca > 130°)
        l_arm_angle = PostureAnalyzer.calculate_angle_2d((l_sh[0], l_sh[1]), (l_el[0], l_el[1]), (l_wr[0], l_wr[1]))
        r_arm_angle = PostureAnalyzer.calculate_angle_2d((r_sh[0], r_sh[1]), (r_el[0], r_el[1]), (r_wr[0], r_wr[1]))
        arms_straight = l_arm_angle > 130.0 and r_arm_angle > 130.0

        if left_wrist_up and right_wrist_up and arms_straight:
            # Posición correcta: acumulamos tiempo
            self.elapsed_seconds += delta_time
            
            # También detectamos repeticiones dinámicas si el usuario sube y baja
            if self.arm_raise_state == "DOWN":
                self.completed_reps += 1
                self.arm_raise_state = "UP"

            rem_sec = max(0, int(self.target_seconds - self.elapsed_seconds))
            return f"✅ ¡Posición perfecta! Mantén los brazos arriba ({rem_sec}s restantes)"
        
        elif left_wrist_up and right_wrist_up:
            return "👉 Estira los codos completamente hacia el techo"
        else:
            # Los brazos bajaron
            if self.arm_raise_state == "UP":
                self.arm_raise_state = "DOWN"
            return "🙌 Eleva ambos brazos rectos por encima de tu cabeza"

    def _process_squats(self, current_knee_angle: float) -> str:
        """
        Evalúa la máquina de estados de las sentadillas (Deep Squat).
        """
        if current_knee_angle <= self.squat_down_angle and self.squat_state == "UP":
            self.squat_state = "DOWN"
            return "🔽 ¡Buena flexión! Ahora sube manteniendo la espalda recta"

        if current_knee_angle >= self.squat_up_angle and self.squat_state == "DOWN":
            self.completed_reps += 1
            self.squat_state = "UP"
            return f"🔥 ¡Repetición válida! {self.completed_reps} de {self.target_reps}"

        if self.squat_state == "DOWN":
            return "🔼 Sube de nuevo a posición erguida"

        return f"🏋️ Haz una sentadilla (Baja hasta ~90° y sube). Llevas {self.completed_reps}/{self.target_reps}"

    def _build_status(self, is_standing: bool, knee_angle: float, feedback: str) -> ExerciseStatus:
        """Construye el objeto ExerciseStatus con el porcentaje de progreso calculado."""
        if self.exercise_type == "squats":
            progress = min(100.0, (self.completed_reps / max(1, self.target_reps)) * 100.0)
        else:
            # Progresión por tiempo o por repeticiones (el que sea mayor)
            time_prog = (self.elapsed_seconds / max(1.0, self.target_seconds)) * 100.0
            reps_prog = (self.completed_reps / max(1, self.target_reps)) * 100.0
            progress = min(100.0, max(time_prog, reps_prog))

        return ExerciseStatus(
            is_standing=is_standing,
            knee_angle=round(knee_angle, 1),
            current_exercise=self.exercise_type,
            completed_reps=self.completed_reps,
            target_reps=self.target_reps,
            elapsed_seconds=round(self.elapsed_seconds, 1),
            target_seconds=self.target_seconds,
            progress_percent=round(progress, 1),
            is_unlocked=self.is_unlocked,
            feedback_message=feedback
        )

"""
Módulo de Verificación de Ejercicios y Pausas Activas para Desbloqueo.
Implementa máquinas de estados para ejercicios ergonómicos de escritorio (sentado o de pie)
y ejercicios de cuerpo completo con alta fidelidad cinemática mediante MediaPipe Pose.
"""

from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Any
from .posture_analyzer import PostureAnalyzer
from .exercise_catalog import get_exercise_metadata, EXERCISE_CATALOG, ExerciseMetadata


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
    requires_standing: bool = False


class ExerciseVerifier:
    """
    Verificador biomecánico multi-ejercicio para la pantalla de bloqueo de SmartBreak.
    Soporta ejercicios de escritorio (primer plano/medio cuerpo) y de cuerpo completo.
    """

    def __init__(self, 
                 exercise_type: str = "shoulder_shrugs",
                 target_seconds: int = 45,
                 target_reps: int = 10,
                 standing_knee_threshold: float = 165.0):
        
        self.exercise_type = exercise_type
        self.target_seconds = float(target_seconds)
        self.target_reps = target_reps
        self.standing_knee_threshold = standing_knee_threshold

        # Variables de progreso
        self.completed_reps: int = 0
        self.elapsed_seconds: float = 0.0
        self.is_unlocked: bool = False
        
        # Máquinas de estados para cada modalidad de ejercicio
        self.shrug_state: str = "DOWN"            # "DOWN" (relajado) -> "UP" (encogido) -> "DOWN"
        self.overhead_touch_state: str = "DOWN"   # "DOWN" -> "UP" (manos juntas arriba) -> "DOWN"
        self.cactus_state: str = "OPEN"           # "OPEN" -> "CLOSED" (codos juntos) -> "OPEN" (codos separados)
        self.neck_state: str = "CENTER"           # "CENTER" -> "TILTED" -> "CENTER"
        self.neck_target_side: str = "LEFT"       # Alterna entre "LEFT" y "RIGHT"
        self.arm_raise_state: str = "DOWN"        # "DOWN" -> "UP" (para overhead_stretch)
        self.squat_state: str = "UP"              # "UP" -> "DOWN" (para sentadillas)

        # Umbrales cinemáticos
        self.squat_down_angle: float = 110.0
        self.squat_up_angle: float = 150.0
        self.shoulder_baseline_y: Optional[float] = None

    def reset(self) -> None:
        """Reinicia los contadores y las máquinas de estados de todos los ejercicios."""
        self.completed_reps = 0
        self.elapsed_seconds = 0.0
        self.is_unlocked = False
        self.shrug_state = "DOWN"
        self.overhead_touch_state = "DOWN"
        self.cactus_state = "OPEN"
        self.neck_state = "CENTER"
        self.neck_target_side = "LEFT"
        self.arm_raise_state = "DOWN"
        self.squat_state = "UP"
        self.shoulder_baseline_y = None

    def update(self, pose_results: Any, image_shape: Tuple[int, int, int], delta_time: float) -> ExerciseStatus:
        """
        Evalúa el frame actual con MediaPipe Pose y avanza el progreso del ejercicio configurado.
        """
        h, w = image_shape[:2]
        meta = get_exercise_metadata(self.exercise_type)

        if pose_results is None:
            return self._build_status(
                is_standing=False,
                knee_angle=0.0,
                feedback="Ponte frente a la cámara para iniciar el ejercicio",
                requires_standing=meta.requires_standing
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
                feedback="Ponte frente a la cámara para iniciar el ejercicio",
                requires_standing=meta.requires_standing
            )

        def get_pt(idx: int) -> Tuple[float, float, float]:
            if idx < len(landmarks):
                lm = landmarks[idx]
                vis = getattr(lm, 'visibility', getattr(lm, 'presence', 0.9))
                if vis is None:
                    vis = 0.9
                return (lm.x * w, lm.y * h, vis)
            return (0.0, 0.0, 0.0)

        # Puntos anatómicos clave
        nose = get_pt(PostureAnalyzer.NOSE)
        l_ear = get_pt(PostureAnalyzer.LEFT_EAR)
        r_ear = get_pt(PostureAnalyzer.RIGHT_EAR)
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

        # -----------------------------------------------------------------
        # 1. Evaluación de Bipedestación (Solo obligatoria si meta.requires_standing)
        # -----------------------------------------------------------------
        leg_angles = []
        if l_hip[2] > 0.35 and l_knee[2] > 0.35 and l_ank[2] > 0.35:
            leg_angles.append(PostureAnalyzer.calculate_angle_2d((l_hip[0], l_hip[1]), (l_knee[0], l_knee[1]), (l_ank[0], l_ank[1])))
        if r_hip[2] > 0.35 and r_knee[2] > 0.35 and r_ank[2] > 0.35:
            leg_angles.append(PostureAnalyzer.calculate_angle_2d((r_hip[0], r_hip[1]), (r_knee[0], r_knee[1]), (r_ank[0], r_ank[1])))

        has_legs = len(leg_angles) > 0
        if has_legs:
            current_knee_angle = float(np.mean(leg_angles))
            is_standing = current_knee_angle >= self.standing_knee_threshold
        else:
            # Fallback cinemático por elevación de hombros si la cámara está cerca
            is_standing = (l_sh[2] > 0.35 and r_sh[2] > 0.35 and nose[2] > 0.35)
            sh_y = (l_sh[1] + r_sh[1]) / 2.0

            if self.exercise_type == "squats":
                if self.shoulder_baseline_y is None:
                    self.shoulder_baseline_y = sh_y
                elif sh_y < self.shoulder_baseline_y:
                    self.shoulder_baseline_y = sh_y

                delta_y = max(0.0, sh_y - self.shoulder_baseline_y)
                target_drop = max(40.0, h * 0.14)
                drop_ratio = max(0.0, min(1.0, delta_y / target_drop))
                current_knee_angle = 180.0 - (drop_ratio * 85.0)
            else:
                current_knee_angle = 180.0

        # Si el ejercicio exige explícitamente estar de pie (ej. Sentadillas) y no lo está
        if meta.requires_standing and not is_standing:
            return self._build_status(
                is_standing=False,
                knee_angle=current_knee_angle,
                feedback="⚠️ ¡Ponte de pie! Este ejercicio requiere bipedestación (Ángulo > 165°)",
                requires_standing=True
            )

        # -----------------------------------------------------------------
        # 2. Despacho y Evaluación del Ejercicio Seleccionado
        # -----------------------------------------------------------------
        feedback = ""

        if self.exercise_type == "shoulder_shrugs":
            feedback = self._process_shoulder_shrugs(l_sh, r_sh, l_ear, r_ear)

        elif self.exercise_type == "overhead_touch":
            feedback = self._process_overhead_touch(nose, l_sh, r_sh, l_wr, r_wr)

        elif self.exercise_type == "cactus_arms":
            feedback = self._process_cactus_arms(l_sh, r_sh, l_el, r_el, l_wr, r_wr)

        elif self.exercise_type == "neck_stretch":
            feedback = self._process_neck_stretch(nose, l_sh, r_sh, l_ear, r_ear)

        elif self.exercise_type == "overhead_stretch":
            feedback = self._process_overhead_stretch(nose, l_sh, r_sh, l_el, r_el, l_wr, r_wr, delta_time)

        elif self.exercise_type == "squats":
            feedback = self._process_squats(current_knee_angle)
            if not has_legs and "válida" not in feedback and self.squat_state == "UP":
                feedback = f"🏋️ Sentadilla activa: Flexiona profundo y sube. Llevas {self.completed_reps}/{self.target_reps}"

        else:
            # Fallback a encogimiento de hombros
            feedback = self._process_shoulder_shrugs(l_sh, r_sh, l_ear, r_ear)

        # -----------------------------------------------------------------
        # 3. Comprobar si se ha cumplido el objetivo de desbloqueo
        # -----------------------------------------------------------------
        if meta.metric_type == "reps":
            if self.completed_reps >= self.target_reps:
                self.is_unlocked = True
                feedback = f"🎉 ¡Excelente trabajo! {self.completed_reps} repeticiones completadas. Desbloqueando..."
        else:
            if self.elapsed_seconds >= self.target_seconds or self.completed_reps >= self.target_reps:
                self.is_unlocked = True
                feedback = "🎉 ¡Meta cumplida! Postura y circulación restablecidas. Desbloqueando..."

        return self._build_status(
            is_standing=is_standing,
            knee_angle=current_knee_angle,
            feedback=feedback,
            requires_standing=meta.requires_standing
        )

    # ---------------------------------------------------------------------
    # Lógica Biomecánica Detallada por Ejercicio
    # ---------------------------------------------------------------------

    def _process_shoulder_shrugs(self, l_sh, r_sh, l_ear, r_ear) -> str:
        """
        Encogimiento de hombros: mide la reducción de la distancia oreja-hombro
        normalizada respecto al ancho biacromial (hombro a hombro).
        """
        w_sh = max(40.0, abs(r_sh[0] - l_sh[0]))
        # Distancia oreja-hombro (en pantalla Y crece hacia abajo: oreja menor Y, hombro mayor Y)
        dist_l = max(0.0, l_sh[1] - l_ear[1])
        dist_r = max(0.0, r_sh[1] - r_ear[1])
        avg_dist = (dist_l + dist_r) / 2.0
        ratio = avg_dist / w_sh

        # Umbrales empíricos:
        # En reposo/relajado ratio > 0.28 (típicamente 0.32 a 0.48)
        # Al encoger fuertemente los hombros hacia arriba ratio baja de 0.23
        is_shrugged = ratio < 0.23
        is_relaxed = ratio > 0.28

        if is_shrugged and self.shrug_state == "DOWN":
            self.shrug_state = "UP"
            return "✅ ¡Hombros arriba! Ahora relájalos completamente hacia abajo"

        elif is_relaxed and self.shrug_state == "UP":
            self.completed_reps += 1
            self.shrug_state = "DOWN"
            return f"🔥 ¡Repetición completada! {self.completed_reps} de {self.target_reps}"

        if self.shrug_state == "UP":
            return "🔽 Relaja los hombros soltando la tensión hacia abajo"

        return f"⚡ Sube los hombros hacia las orejas. Llevas {self.completed_reps}/{self.target_reps}"

    def _process_overhead_touch(self, nose, l_sh, r_sh, l_wr, r_wr) -> str:
        """
        Toque de manos sobre la cabeza: ambas muñecas ascienden juntas por encima de la cabeza
        y luego descienden a la altura del pecho.
        """
        w_sh = max(40.0, abs(r_sh[0] - l_sh[0]))
        dist_wr = math.hypot(l_wr[0] - r_wr[0], l_wr[1] - r_wr[1])
        wr_ratio = dist_wr / w_sh

        # Manos arriba (por encima de la nariz) y juntas
        hands_up = (l_wr[1] < (nose[1] + 20)) and (r_wr[1] < (nose[1] + 20))
        hands_together = wr_ratio < 0.40 and hands_up
        hands_down = (l_wr[1] > (nose[1] + 50)) or (r_wr[1] > (nose[1] + 50))

        if hands_together and self.overhead_touch_state == "DOWN":
            self.overhead_touch_state = "UP"
            return "✅ ¡Manos juntas arriba! Ahora bájalas al nivel del pecho"

        elif hands_down and self.overhead_touch_state == "UP":
            self.completed_reps += 1
            self.overhead_touch_state = "DOWN"
            return f"🔥 ¡Toque válido! {self.completed_reps} de {self.target_reps}"

        if self.overhead_touch_state == "UP":
            return "🔽 Desciende las manos al pecho"

        return f"🙌 Junta ambas palmas sobre tu cabeza. Llevas {self.completed_reps}/{self.target_reps}"

    def _process_cactus_arms(self, l_sh, r_sh, l_el, r_el, l_wr, r_wr) -> str:
        """
        Apertura pectoral (Brazos en Cactus): junta antebrazos frente al rostro
        y luego abre los codos hacia atrás expandiendo la caja torácica.
        """
        w_sh = max(40.0, abs(r_sh[0] - l_sh[0]))
        elbow_dist = abs(r_el[0] - l_el[0]) / w_sh

        # Codos juntos al frente vs codos abiertos lateralmente
        is_closed = elbow_dist < 0.70
        is_open = elbow_dist > 1.10

        if is_closed and self.cactus_state != "CLOSED":
            self.cactus_state = "CLOSED"
            return "👐 ¡Codos juntos! Ahora ábrelos hacia atrás expandiendo el pecho"

        elif is_open and self.cactus_state == "CLOSED":
            self.completed_reps += 1
            self.cactus_state = "OPEN"
            return f"🔥 ¡Apertura pectoral válida! {self.completed_reps} de {self.target_reps}"

        if self.cactus_state == "CLOSED":
            return "👐 Abre amplio los codos hacia los lados expandiendo el pecho"

        return f"👥 Junta los codos y antebrazos al frente. Llevas {self.completed_reps}/{self.target_reps}"

    def _process_neck_stretch(self, nose, l_sh, r_sh, l_ear, r_ear) -> str:
        """
        Estiramiento lateral de cuello: detecta inclinación de la cabeza
        hacia la oreja izquierda o derecha y retorno al centro.
        """
        dx = r_ear[0] - l_ear[0]
        dy = r_ear[1] - l_ear[1]

        if abs(dx) < 1.0:
            angle = 0.0
        else:
            angle = math.degrees(math.atan2(dy, dx))

        tilt_deg = abs(angle)
        is_tilted = tilt_deg > 17.0
        is_centered = tilt_deg < 10.0

        target_side_str = "izquierda" if self.neck_target_side == "LEFT" else "derecha"
        next_side_str = "derecha" if self.neck_target_side == "LEFT" else "izquierda"

        if is_tilted and self.neck_state == "CENTER":
            self.neck_state = "TILTED"
            return f"✅ ¡Buen estiramiento hacia la {target_side_str}! Ahora regresa la cabeza al centro"

        elif is_centered and self.neck_state == "TILTED":
            self.completed_reps += 1
            self.neck_state = "CENTER"
            self.neck_target_side = "RIGHT" if self.neck_target_side == "LEFT" else "LEFT"
            return f"🔥 ¡Repetición {self.completed_reps}/{self.target_reps}! Ahora inclina hacia la {next_side_str}"

        if self.neck_state == "TILTED":
            return "🧘 Regresa despacio la cabeza a posición erguida"

        return f"🧘 Inclina tu cabeza hacia la {target_side_str}. Llevas {self.completed_reps}/{self.target_reps}"

    def _process_overhead_stretch(self, nose, l_sh, r_sh, l_el, r_el, l_wr, r_wr, delta_time: float) -> str:
        """
        Estiramiento sostenido de brazos sobre la cabeza.
        """
        left_wrist_up = l_wr[2] > 0.20 and l_wr[1] < (nose[1] + 20)
        right_wrist_up = r_wr[2] > 0.20 and r_wr[1] < (nose[1] + 20)

        l_arm_angle = PostureAnalyzer.calculate_angle_2d((l_sh[0], l_sh[1]), (l_el[0], l_el[1]), (l_wr[0], l_wr[1]))
        r_arm_angle = PostureAnalyzer.calculate_angle_2d((r_sh[0], r_sh[1]), (r_el[0], r_el[1]), (r_wr[0], r_wr[1]))
        arms_straight = l_arm_angle > 125.0 and r_arm_angle > 125.0

        if left_wrist_up and right_wrist_up and arms_straight:
            self.elapsed_seconds += delta_time
            if self.arm_raise_state == "DOWN":
                self.completed_reps += 1
                self.arm_raise_state = "UP"

            rem_sec = max(0, int(self.target_seconds - self.elapsed_seconds))
            return f"✅ ¡Posición perfecta! Mantén los brazos arriba ({rem_sec}s restantes)"

        elif left_wrist_up and right_wrist_up:
            return "👉 Estira los codos completamente hacia el techo"
        else:
            if self.arm_raise_state == "UP":
                self.arm_raise_state = "DOWN"
            return "🙌 Eleva ambos brazos rectos por encima de tu cabeza"

    def _process_squats(self, current_knee_angle: float) -> str:
        """
        Sentadillas profundas: máquina de estados UP -> DOWN -> UP.
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

    def _build_status(self, is_standing: bool, knee_angle: float, feedback: str, requires_standing: bool = False) -> ExerciseStatus:
        """Construye el objeto ExerciseStatus con el cálculo de progreso dinámico."""
        meta = get_exercise_metadata(self.exercise_type)

        if meta.metric_type == "reps":
            progress = min(100.0, (self.completed_reps / max(1, self.target_reps)) * 100.0)
        else:
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
            feedback_message=feedback,
            requires_standing=requires_standing
        )

"""
Módulo de Análisis Trigonométrico de Postura Ergonómica.
Calcula ángulos de inclinación cervical y torácica, asimetría de hombros y presencia frente a la cámara.
Inspirado en la metodología ergonómica de Posture-Detection-Project (Zaini Baloch) y datasets biomecánicos.
"""

from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any


@dataclass
class PostureResult:
    """Resultado del análisis ergonómico de un frame."""
    presence: bool
    is_bad_posture: bool
    neck_angle: float
    torso_angle: float
    shoulder_slope_deg: float
    primary_issue: str
    confidence: float
    landmarks_dict: Dict[str, Tuple[float, float, float]]  # {nombre: (x, y, visibility)}


class PostureAnalyzer:
    """
    Analizador ergonómico por visión computacional.
    Evalúa la alineación de la columna vertebral y posición de la cabeza.
    """

    # Índices canónicos de MediaPipe Pose
    NOSE = 0
    LEFT_EYE = 2
    RIGHT_EYE = 5
    LEFT_EAR = 7
    RIGHT_EAR = 8
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self, 
                 neck_threshold_deg: float = 35.0, 
                 torso_threshold_deg: float = 22.0,
                 min_visibility: float = 0.5):
        self.neck_threshold_deg = neck_threshold_deg
        self.torso_threshold_deg = torso_threshold_deg
        self.min_visibility = min_visibility

    @staticmethod
    def calculate_angle_2d(p_a: Tuple[float, float], 
                           p_b: Tuple[float, float], 
                           p_c: Tuple[float, float]) -> float:
        """
        Calcula el ángulo en grados formado en el vértice B por los puntos A-B-C.
        """
        ba = (p_a[0] - p_b[0], p_a[1] - p_b[1])
        bc = (p_c[0] - p_b[0], p_c[1] - p_b[1])

        dot = ba[0] * bc[0] + ba[1] * bc[1]
        mag_ba = math.hypot(ba[0], ba[1])
        mag_bc = math.hypot(bc[0], bc[1])

        if mag_ba * mag_bc == 0:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
        return math.degrees(math.acos(cos_angle))

    @staticmethod
    def calculate_vector_angle_with_vertical(p_origin: Tuple[float, float], 
                                             p_target: Tuple[float, float]) -> float:
        """
        Calcula el ángulo en grados de inclinación respecto al eje vertical imaginario.
        Por convención en imágenes: Y crece hacia abajo. 
        Un punto erguido directamente encima tiene delta_x = 0 y delta_y < 0.
        """
        dx = p_target[0] - p_origin[0]
        dy = p_origin[1] - p_target[1]  # Invertir para que arriba sea positivo

        if dy == 0 and dx == 0:
            return 0.0

        # Ángulo respecto a la vertical superior (0 grados es vertical pura hacia arriba)
        angle_rad = math.atan2(abs(dx), dy)
        return math.degrees(angle_rad)

    def analyze(self, pose_results: Any, image_shape: Tuple[int, int, int]) -> PostureResult:
        """
        Evalúa el esqueleto corporal detectado y determina el nivel de ergonomía.
        """
        h, w = image_shape[:2]

        if pose_results is None:
            return PostureResult(
                presence=False,
                is_bad_posture=False,
                neck_angle=0.0,
                torso_angle=0.0,
                shoulder_slope_deg=0.0,
                primary_issue="Usuario ausente",
                confidence=0.0,
                landmarks_dict={}
            )

        # Unificación de acceso a landmarks (Tasks API, Solutions API o PoseDetectionResult)
        if hasattr(pose_results, "landmarks"):
            landmarks = pose_results.landmarks
        elif hasattr(pose_results, "pose_landmarks") and pose_results.pose_landmarks:
            landmarks = getattr(pose_results.pose_landmarks, "landmark", pose_results.pose_landmarks)
        else:
            landmarks = None

        if not landmarks or len(landmarks) == 0:
            return PostureResult(
                presence=False,
                is_bad_posture=False,
                neck_angle=0.0,
                torso_angle=0.0,
                shoulder_slope_deg=0.0,
                primary_issue="Usuario ausente",
                confidence=0.0,
                landmarks_dict={}
            )

        # Extraer landmarks relevantes en coordenadas de píxeles y profundidad normalizada
        def get_pt_3d(idx: int) -> Tuple[float, float, float, float]:
            """Retorna (x_px, y_px, z_norm, visibility)."""
            if idx < len(landmarks):
                lm = landmarks[idx]
                vis = getattr(lm, 'visibility', getattr(lm, 'presence', 0.9))
                if vis is None:
                    vis = 0.9
                z = getattr(lm, 'z', 0.0)
                if z is None:
                    z = 0.0
                return (float(lm.x * w), float(lm.y * h), float(z), float(vis))
            return (0.0, 0.0, 0.0, 0.0)

        l_ear = get_pt_3d(self.LEFT_EAR)
        r_ear = get_pt_3d(self.RIGHT_EAR)
        l_sh = get_pt_3d(self.LEFT_SHOULDER)
        r_sh = get_pt_3d(self.RIGHT_SHOULDER)
        l_hip = get_pt_3d(self.LEFT_HIP)
        r_hip = get_pt_3d(self.RIGHT_HIP)
        nose = get_pt_3d(self.NOSE)

        # 1. Comprobar presencia: al menos la nariz y un hombro deben tener visibilidad suficiente
        has_shoulders = l_sh[3] > self.min_visibility or r_sh[3] > self.min_visibility
        has_face = nose[3] > self.min_visibility or l_ear[3] > self.min_visibility or r_ear[3] > self.min_visibility

        if not (has_shoulders and has_face):
            return PostureResult(
                presence=False,
                is_bad_posture=False,
                neck_angle=0.0,
                torso_angle=0.0,
                shoulder_slope_deg=0.0,
                primary_issue="No se detecta torso completo",
                confidence=float(np.mean([l_sh[3], r_sh[3], nose[3]])),
                landmarks_dict={}
            )

        # 2. Determinar si la vista es lateral/perfil o frontal
        # Si un lado tiene mucha mayor visibilidad que el otro, es vista lateral
        use_left_lateral = (l_ear[3] > self.min_visibility and r_ear[3] < 0.25)
        use_right_lateral = (r_ear[3] > self.min_visibility and l_ear[3] < 0.25)
        is_lateral_view = use_left_lateral or use_right_lateral

        if use_left_lateral:
            ear_pt_2d = (l_ear[0], l_ear[1])
            sh_pt_2d = (l_sh[0], l_sh[1])
            hip_pt_2d = (l_hip[0], l_hip[1]) if l_hip[3] > self.min_visibility else None
            z_ear = l_ear[2]
            z_sh = l_sh[2]
        elif use_right_lateral:
            ear_pt_2d = (r_ear[0], r_ear[1])
            sh_pt_2d = (r_sh[0], r_sh[1])
            hip_pt_2d = (r_hip[0], r_hip[1]) if r_hip[3] > self.min_visibility else None
            z_ear = r_ear[2]
            z_sh = r_sh[2]
        else:
            # Vista frontal (típica en monitores y portátiles)
            ear_pt_2d = ((l_ear[0] + r_ear[0]) / 2.0, (l_ear[1] + r_ear[1]) / 2.0)
            sh_pt_2d = ((l_sh[0] + r_sh[0]) / 2.0, (l_sh[1] + r_sh[1]) / 2.0)
            if l_hip[3] > self.min_visibility and r_hip[3] > self.min_visibility:
                hip_pt_2d = ((l_hip[0] + r_hip[0]) / 2.0, (l_hip[1] + r_hip[1]) / 2.0)
            else:
                hip_pt_2d = None
            z_ear = (l_ear[2] + r_ear[2]) / 2.0
            z_sh = (l_sh[2] + r_sh[2]) / 2.0

        # Ancho biacromial en píxeles (distancia de hombro a hombro)
        shoulder_width = max(1.0, math.hypot(r_sh[0] - l_sh[0], r_sh[1] - l_sh[1]))

        # 3. Cálculo de Inclinación de Cuello (Neck Inclination Angle)
        # Componente 2D estándar (útil en vista lateral o inclinación lateral de cabeza)
        neck_angle_2d = self.calculate_vector_angle_with_vertical(sh_pt_2d, ear_pt_2d)

        # Componente 3D para cámaras frontales (cuello adelantado a lo largo del eje Z y compresión vertical)
        neck_angle_frontal = 0.0
        if not is_lateral_view and shoulder_width > 20:
            # A) Profundidad relativa Z: En MediaPipe, z disminuye conforme el punto se acerca a la cámara.
            # Cuando la cabeza se adelanta hacia la pantalla, z_sh - z_ear es positivo.
            delta_z = z_sh - z_ear
            vertical_neck_h = max(1.0, sh_pt_2d[1] - ear_pt_2d[1])
            normalized_h = vertical_neck_h / shoulder_width

            if delta_z > 0.06:
                # Estimación trigonométrica del vector sagital cabeza-hombro
                depth_angle = math.degrees(math.atan2(delta_z, max(0.1, normalized_h))) * 1.5
                neck_angle_frontal = max(neck_angle_frontal, depth_angle)

            # B) Ratio de compresión vertical del cuello:
            # En postura correcta, normalized_h está entre 0.32 y 0.50.
            # Al encorvarse y adelantar el cuello, la distancia vertical aparente cae drásticamente (< 0.24)
            if normalized_h < 0.26:
                compression_factor = max(0.0, min(1.0, (0.26 - normalized_h) / 0.16))
                ratio_angle = 35.0 + (compression_factor * 25.0)  # Escala proporcional de alerta
                neck_angle_frontal = max(neck_angle_frontal, ratio_angle)

        neck_angle = max(neck_angle_2d, neck_angle_frontal)

        # 4. Cálculo de Inclinación de Torso (Torso Inclination Angle)
        torso_angle_2d = 0.0
        torso_angle_frontal = 0.0
        if hip_pt_2d is not None:
            torso_angle_2d = self.calculate_vector_angle_with_vertical(hip_pt_2d, sh_pt_2d)
            if not is_lateral_view and shoulder_width > 20:
                z_hip = (l_hip[2] + r_hip[2]) / 2.0
                delta_z_torso = z_hip - z_sh
                vertical_torso_h = max(1.0, hip_pt_2d[1] - sh_pt_2d[1])
                if delta_z_torso > 0.08:
                    torso_angle_frontal = math.degrees(math.atan2(delta_z_torso, vertical_torso_h / shoulder_width)) * 1.3
        
        torso_angle = max(torso_angle_2d, torso_angle_frontal)

        # 5. Cálculo de Inclinación / Desnivel de Hombros (Shoulder Slope)
        if l_sh[3] > self.min_visibility and r_sh[3] > self.min_visibility:
            delta_y = abs(l_sh[1] - r_sh[1])
            delta_x = max(1.0, abs(l_sh[0] - r_sh[0]))
            shoulder_slope_deg = math.degrees(math.atan2(delta_y, delta_x))
        else:
            shoulder_slope_deg = 0.0

        # 6. Clasificación Ergonómica y Diagnóstico
        issues = []
        is_bad = False

        if neck_angle >= self.neck_threshold_deg:
            issues.append(f"Cuello adelantado ({neck_angle:.1f}°)")
            is_bad = True

        if torso_angle >= self.torso_threshold_deg:
            issues.append(f"Columna encorvada ({torso_angle:.1f}°)")
            is_bad = True

        if shoulder_slope_deg > 14.0:
            issues.append(f"Hombros desnivelados ({shoulder_slope_deg:.1f}°)")
            is_bad = True

        primary_issue = " | ".join(issues) if issues else "Postura Ergonómica Correcta"
        avg_confidence = float(np.mean([l_sh[3], r_sh[3], l_ear[3], r_ear[3]]))

        # Compilar mapa de landmarks
        landmarks_dict = {
            "nose": (nose[0], nose[1], nose[3]),
            "left_ear": (l_ear[0], l_ear[1], l_ear[3]),
            "right_ear": (r_ear[0], r_ear[1], r_ear[3]),
            "left_shoulder": (l_sh[0], l_sh[1], l_sh[3]),
            "right_shoulder": (r_sh[0], r_sh[1], r_sh[3]),
        }
        if hip_pt_2d:
            landmarks_dict["left_hip"] = (l_hip[0], l_hip[1], l_hip[3])
            landmarks_dict["right_hip"] = (r_hip[0], r_hip[1], r_hip[3])

        return PostureResult(
            presence=True,
            is_bad_posture=is_bad,
            neck_angle=round(neck_angle, 1),
            torso_angle=round(torso_angle, 1),
            shoulder_slope_deg=round(shoulder_slope_deg, 1),
            primary_issue=primary_issue,
            confidence=round(avg_confidence, 2),
            landmarks_dict=landmarks_dict
        )

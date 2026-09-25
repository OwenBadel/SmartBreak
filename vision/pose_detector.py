"""
Módulo Detector de Postura mediante MediaPipe Pose.
Compatible tanto con la nueva Tasks API de MediaPipe 0.10+ (Python 3.12)
como con la API clásica de Solutions (Python 3.8-3.11).
Incluye renderizado de esqueleto con OpenCV de alto rendimiento y estética neón.
"""

from __future__ import annotations
import os
import sys
import ssl
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any
import cv2
import numpy as np


@dataclass
class NormalizedPoint:
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0


@dataclass
class PoseDetectionResult:
    landmarks: Optional[List[NormalizedPoint]]
    raw_result: Any = None


# Conexiones biomecánicas de MediaPipe Pose (33 landmarks)
POSE_CONNECTIONS = [
    # Cara
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    # Torso superior
    (11, 12), (11, 13), (13, 15),
    (12, 14), (14, 16),
    # Torso y cadera
    (11, 23), (12, 24), (23, 24),
    # Pierna izquierda
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    # Pierna derecha
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
]


class PoseDetector:
    """
    Detector de pose corporal desacoplado.
    Soporta Tasks API y Legacy Solutions API.
    """

    def __init__(self, 
                 static_mode: bool = False, 
                 model_complexity: int = 1, 
                 min_detection_confidence: float = 0.5, 
                 min_tracking_confidence: float = 0.5):
        
        self.static_mode = static_mode
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        self.backend = "none"
        self._landmarker = None
        self._legacy_pose = None
        
        self._init_backend()

    def _ensure_model_file(self) -> str:
        """Asegura que el archivo del modelo pose_landmarker_lite.task esté disponible."""
        # 1. Verificar si está empaquetado en PyInstaller (_MEIPASS o _internal)
        possible_dirs = []
        if hasattr(sys, "_MEIPASS"):
            possible_dirs.append(Path(sys._MEIPASS) / "models")
        
        exe_dir = Path(sys.executable).parent
        possible_dirs.append(exe_dir / "_internal" / "models")
        possible_dirs.append(exe_dir / "models")
        possible_dirs.append(Path(__file__).resolve().parent.parent / "models")

        for pdir in possible_dirs:
            candidate = pdir / "pose_landmarker_lite.task"
            if candidate.exists() and candidate.stat().st_size > 1000:
                return str(candidate)

        # Si no existe, usar la carpeta local de models y descargar
        models_dir = Path(__file__).resolve().parent.parent / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        model_path = models_dir / "pose_landmarker_lite.task"

        if not model_path.exists() or model_path.stat().st_size < 1000:
            print("[PoseDetector] Descargando modelo MediaPipe PoseLandmarker Lite...")
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
            try:
                # Verificación SSL segura por defecto
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(url, context=ctx) as resp, open(str(model_path), "wb") as out_file:
                    out_file.write(resp.read())
                print(f"[PoseDetector] Modelo descargado y verificado con éxito en {model_path}")
            except Exception as e:
                print(f"[PoseDetector] Descarga con SSL estándar falló ({e}). Reintentando con urllib seguro...")
                try:
                    urllib.request.urlretrieve(url, str(model_path))
                except Exception as e2:
                    print(f"[PoseDetector] Error crítico al descargar modelo: {e2}")

        return str(model_path)

    def _init_backend(self) -> None:
        """Inicializa Tasks API (preferente) o Legacy Solutions API."""
        log_file = Path("mp_debug.txt")
        try:
            with open(log_file, "a") as f:
                f.write("Iniciando backend...\n")
            
            import mediapipe as mp
            with open(log_file, "a") as f:
                f.write(f"Mediapipe importado. dir(mp): {dir(mp)}\n")
            
            # Opción A: Tasks API (MediaPipe 0.10+ en Python 3.12+)
            if hasattr(mp, "tasks"):
                with open(log_file, "a") as f:
                    f.write("mp.tasks encontrado, intentando Tasks API...\n")
                from mediapipe.tasks.python import BaseOptions
                from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode
                
                model_file = self._ensure_model_file()
                if os.path.exists(model_file):
                    options = PoseLandmarkerOptions(
                        base_options=BaseOptions(model_asset_path=model_file),
                        running_mode=RunningMode.IMAGE,
                        min_pose_detection_confidence=self.min_detection_confidence,
                        min_pose_presence_confidence=self.min_detection_confidence,
                        min_tracking_confidence=self.min_tracking_confidence,
                        output_segmentation_masks=False
                    )
                    self._landmarker = PoseLandmarker.create_from_options(options)
                    self.backend = "tasks"
                    with open(log_file, "a") as f:
                        f.write("Tasks API inicializado con éxito.\n")
                    return
                else:
                    with open(log_file, "a") as f:
                        f.write(f"Archivo de modelo no encontrado: {model_file}\n")

            # Opción B: Legacy Solutions API
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
                with open(log_file, "a") as f:
                    f.write("mp.solutions encontrado, intentando Legacy API...\n")
                self._legacy_pose = mp.solutions.pose.Pose(
                    static_image_mode=self.static_mode,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence
                )
                self.backend = "solutions"
                with open(log_file, "a") as f:
                    f.write("Legacy Solutions API inicializado con éxito.\n")
                return
            else:
                with open(log_file, "a") as f:
                    f.write("Fallo: mp no tiene .tasks ni .solutions.pose\n")
        except Exception as e:
            with open(log_file, "a") as f:
                import traceback
                f.write(f"Exception in _init_backend: {e}\n{traceback.format_exc()}\n")
            self.backend = "none"

    def process_frame(self, frame_bgr: np.ndarray) -> Tuple[Optional[PoseDetectionResult], Optional[np.ndarray]]:
        """
        Procesa un frame BGR con MediaPipe.
        Retorna (PoseDetectionResult, frame_rgb).
        """
        if frame_bgr is None or self.backend == "none":
            return None, None

        frame_rgb = np.ascontiguousarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))

        try:
            # Inferencia con Tasks API
            if self.backend == "tasks" and self._landmarker is not None:
                import mediapipe as mp
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                result = self._landmarker.detect(mp_image)

                if result and result.pose_landmarks and len(result.pose_landmarks) > 0:
                    raw_lms = result.pose_landmarks[0]
                    points = []
                    for lm in raw_lms:
                        z_val = getattr(lm, 'z', 0.0)
                        vis_val = getattr(lm, 'visibility', None)
                        if vis_val is None:
                            vis_val = getattr(lm, 'presence', 0.9)
                        points.append(
                            NormalizedPoint(
                                x=float(lm.x),
                                y=float(lm.y),
                                z=float(z_val) if z_val is not None else 0.0,
                                visibility=float(vis_val) if vis_val is not None else 0.9
                            )
                        )
                    return PoseDetectionResult(landmarks=points, raw_result=result), frame_rgb

                # Recuperación para videos/cámaras con franjas negras (pillarbox o letterbox como en OBS)
                h, w = frame_bgr.shape[:2]
                gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                mask = gray > 15
                col_sums = mask.sum(axis=0)
                row_sums = mask.sum(axis=1)
                active_cols = np.where(col_sums > (h * 0.05))[0]
                active_rows = np.where(row_sums > (w * 0.05))[0]

                if len(active_cols) > 0 and len(active_rows) > 0:
                    x1, x2 = int(active_cols.min()), int(active_cols.max())
                    y1, y2 = int(active_rows.min()), int(active_rows.max())
                    # Si hay márgenes negros apreciables (> 8% del encuadre)
                    if x1 > w * 0.08 or (w - 1 - x2) > w * 0.08 or y1 > h * 0.08 or (h - 1 - y2) > h * 0.08:
                        crop_rgb = np.ascontiguousarray(frame_rgb[y1:y2+1, x1:x2+1])
                        crop_h, crop_w = crop_rgb.shape[:2]
                        crop_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=crop_rgb)
                        crop_res = self._landmarker.detect(crop_mp)
                        if crop_res and crop_res.pose_landmarks and len(crop_res.pose_landmarks) > 0:
                            raw_lms = crop_res.pose_landmarks[0]
                            remapped = []
                            for lm in raw_lms:
                                z_val = getattr(lm, 'z', 0.0)
                                vis_val = getattr(lm, 'visibility', None)
                                if vis_val is None:
                                    vis_val = getattr(lm, 'presence', 0.9)
                                remapped.append(
                                    NormalizedPoint(
                                        x=(x1 + lm.x * crop_w) / w,
                                        y=(y1 + lm.y * crop_h) / h,
                                        z=float(z_val) if z_val is not None else 0.0,
                                        visibility=float(vis_val) if vis_val is not None else 0.9
                                    )
                                )
                            return PoseDetectionResult(landmarks=remapped, raw_result=crop_res), frame_rgb

                return PoseDetectionResult(landmarks=None, raw_result=result), frame_rgb

            # Inferencia con Solutions API
            elif self.backend == "solutions" and self._legacy_pose is not None:
                frame_rgb.flags.writeable = False
                result = self._legacy_pose.process(frame_rgb)
                frame_rgb.flags.writeable = True

                if result and result.pose_landmarks:
                    raw_lms = result.pose_landmarks.landmark
                    points = [
                        NormalizedPoint(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility)
                        for lm in raw_lms
                    ]
                    return PoseDetectionResult(landmarks=points, raw_result=result), frame_rgb
                return PoseDetectionResult(landmarks=None, raw_result=result), frame_rgb

        except Exception as e:
            print(f"[PoseDetector] Error durante inferencia: {e}")
            return PoseDetectionResult(landmarks=None), frame_rgb

        return None, frame_rgb

    def draw_landmarks(self, frame_bgr: np.ndarray, 
                       results: Optional[PoseDetectionResult], 
                       custom_color: Tuple[int, int, int] = (0, 230, 150)) -> np.ndarray:
        """
        Dibuja los landmarks anatómicos y conexiones del esqueleto sobre el frame BGR
        usando un estilo visual moderno de alto contraste y antialiasing.
        """
        if results is None or not results.landmarks or frame_bgr is None:
            return frame_bgr

        annotated = frame_bgr.copy()
        h, w = annotated.shape[:2]
        lms = results.landmarks

        # 1. Dibujar líneas de conexión del esqueleto
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(lms) and end_idx < len(lms):
                p1 = lms[start_idx]
                p2 = lms[end_idx]

                if p1.visibility > 0.35 and p2.visibility > 0.35:
                    pt1 = (int(p1.x * w), int(p1.y * h))
                    pt2 = (int(p2.x * w), int(p2.y * h))
                    # Línea de brillo exterior
                    cv2.line(annotated, pt1, pt2, (25, 25, 25), 4, lineType=cv2.LINE_AA)
                    # Línea interior temática
                    cv2.line(annotated, pt1, pt2, custom_color, 2, lineType=cv2.LINE_AA)

        # 2. Dibujar nodos / articulaciones
        for idx, lm in enumerate(lms):
            if lm.visibility > 0.35:
                cx, cy = int(lm.x * w), int(lm.y * h)
                # Puntos faciales más sutiles, articulaciones principales más notorias
                is_joint = idx in (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
                radius = 5 if is_joint else 3
                
                # Halo exterior oscuro
                cv2.circle(annotated, (cx, cy), radius + 2, (15, 15, 20), -1, lineType=cv2.LINE_AA)
                # Punto interior brillante
                cv2.circle(annotated, (cx, cy), radius, (255, 255, 255), -1, lineType=cv2.LINE_AA)

        return annotated

    def close(self) -> None:
        """Libera recursos del detector."""
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None
        if self._legacy_pose:
            self._legacy_pose.close()
            self._legacy_pose = None

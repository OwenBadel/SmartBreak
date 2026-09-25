"""
Módulo Worker de Visión Desacoplado para SmartBreak.
Ejecuta la captura de cámara OpenCV y la inferencia de MediaPipe Pose en un hilo secundario
dedicado, garantizando que el hilo principal de la interfaz PyQt6 se mantenga 100% fluido.
"""

from __future__ import annotations
import time
import threading
from typing import Optional, Tuple, Any, List
import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal

try:
    from config.settings import Settings
    from core.fatigue_tracker import FatigueTracker
    from vision.pose_detector import PoseDetector
    from vision.posture_analyzer import PostureAnalyzer
    from vision.exercise_verifier import ExerciseVerifier, ExerciseStatus
    from vision.camera_manager import get_available_cameras
except ImportError:
    from ..config.settings import Settings
    from .fatigue_tracker import FatigueTracker
    from ..vision.pose_detector import PoseDetector
    from ..vision.posture_analyzer import PostureAnalyzer
    from ..vision.exercise_verifier import ExerciseVerifier, ExerciseStatus
    from ..vision.camera_manager import get_available_cameras


class VisionWorker(QThread):
    """
    Hilo de trabajo continuo para procesamiento de visión por computadora.
    Desacopla OpenCV y MediaPipe del ciclo de eventos de la GUI Qt.
    """

    # Señales para comunicación segura con el Hilo Principal Qt
    frame_ready = pyqtSignal(object, object)      # (annotated_frame_bgr: np.ndarray, status: ExerciseStatus)
    passive_status_updated = pyqtSignal(dict)     # summary: Dict[str, Any]
    trigger_break = pyqtSignal(str)              # reason: str
    camera_switched = pyqtSignal(int, str)       # (cam_index: int, cam_name: str)

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        # Componentes de visión y lógica
        self.fatigue_tracker = FatigueTracker(
            max_sitting_minutes=self.settings.max_sitting_minutes,
            max_bad_posture_minutes=self.settings.max_bad_posture_minutes
        )
        self.pose_detector = PoseDetector(static_mode=False, model_complexity=1)
        self.posture_analyzer = PostureAnalyzer(
            neck_threshold_deg=self.settings.neck_angle_threshold_deg,
            torso_threshold_deg=self.settings.torso_angle_threshold_deg
        )
        self.exercise_verifier = ExerciseVerifier(
            exercise_type=self.settings.exercise_type,
            target_seconds=self.settings.exercise_duration_seconds,
            target_reps=self.settings.exercise_target_reps,
            standing_knee_threshold=self.settings.standing_leg_angle_threshold
        )

        # Control de ciclo y concurrencia
        self._is_running: bool = False
        self._is_active_break: bool = False
        self._lock = threading.Lock()
        
        # Cámara
        self.cap: Optional[cv2.VideoCapture] = None

    def run(self) -> None:
        """Bucle principal de ejecución del hilo secundario de visión."""
        self._is_running = True
        self._open_camera()

        last_time = time.time()
        black_frame_count = 0

        while self._is_running:
            current_time = time.time()
            raw_delta = current_time - last_time
            last_time = current_time

            # -------------------------------------------------------------
            # Blindaje contra Reposo/Suspensión de Windows (BUG-05)
            # -------------------------------------------------------------
            if raw_delta > 15.0:
                print(f"[VisionWorker] Salto temporal detectado ({raw_delta:.1f}s, posible suspensión de Windows). Protegiendo contadores...")
                with self._lock:
                    self.fatigue_tracker.reset_after_break()
                delta = 0.0
            else:
                delta = min(raw_delta, 2.0)

            with self._lock:
                is_active = self._is_active_break

            # -------------------------------------------------------------
            # Captura de Fotograma
            # -------------------------------------------------------------
            frame = None
            if self._ensure_camera_open():
                ret, frame = self.cap.read()
                if not ret:
                    frame = None

            if frame is None:
                # Si la cámara no responde temporalmente
                time.sleep(0.1)
                continue

            # Detección de cuadros negros persistentes (ej. switch de cámara virtual a física)
            if frame.mean() < 1.0:
                black_frame_count += 1
                if black_frame_count >= 3:
                    self._autofind_alternative_camera()
                    black_frame_count = 0
            else:
                black_frame_count = 0

            # -------------------------------------------------------------
            # Modo 1: Pausa Activa Obligatoria (30 FPS en hilo worker)
            # -------------------------------------------------------------
            if is_active:
                target_interval = 1.0 / max(15, self.settings.active_target_fps)
                t_start = time.time()

                try:
                    with self._lock:
                        results, _ = self.pose_detector.process_frame(frame)
                        status = self.exercise_verifier.update(results, frame.shape, delta)
                        color = (0, 230, 150) if status.is_standing else (0, 100, 255)
                        annotated_frame = self.pose_detector.draw_landmarks(frame, results, custom_color=color)

                    # Emitir señal al hilo principal de Qt de manera asíncrona y segura
                    self.frame_ready.emit(annotated_frame, status)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"[VisionWorker] Error procesando frame activo: {e}")

                # Control preciso del ritmo a 30 FPS
                elapsed = time.time() - t_start
                sleep_time = max(0.005, target_interval - elapsed)
                time.sleep(sleep_time)

            # -------------------------------------------------------------
            # Modo 2: Monitoreo Pasivo en Segundo Plano (1 a 2 FPS)
            # -------------------------------------------------------------
            else:
                try:
                    with self._lock:
                        results, _ = self.pose_detector.process_frame(frame)
                        posture_result = self.posture_analyzer.analyze(results, frame.shape)
                        should_break, reason = self.fatigue_tracker.update(
                            delta_time=delta,
                            presence=posture_result.presence,
                            bad_posture=posture_result.is_bad_posture
                        )
                        summary = self.fatigue_tracker.get_status_summary()

                    # Notificar estado al System Tray
                    self.passive_status_updated.emit(summary)

                    # Si se alcanzan umbrales de fatiga, disparar bloqueo
                    if should_break:
                        print(f"[VisionWorker] ¡Umbral de fatiga alcanzado! Razón: {reason}")
                        self.trigger_break.emit(reason)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"[VisionWorker] Error procesando frame pasivo: {e}")

                # Dormir para mantener muestreo pasivo de bajo consumo (1-2 FPS)
                sleep_sec = max(0.4, self.settings.passive_sample_interval_sec)
                time.sleep(sleep_sec)

        # Limpieza final al detener el hilo
        self._release_camera()
        self.pose_detector.close()

    def set_active_break_mode(self, is_active: bool) -> None:
        """Conmuta entre modo pasivo de bajo consumo y modo activo a 30 FPS."""
        with self._lock:
            self._is_active_break = is_active
            if is_active:
                self.exercise_verifier.reset()
                self.exercise_verifier.exercise_type = self.settings.exercise_type
                self.exercise_verifier.target_seconds = self.settings.exercise_duration_seconds
                self.exercise_verifier.target_reps = self.settings.exercise_target_reps

    def update_settings(self, new_settings: Settings) -> None:
        """Actualiza parámetros ergonómicos y cámara de forma segura."""
        with self._lock:
            old_cam = self.settings.camera_index
            self.settings = new_settings
            self.fatigue_tracker.max_sitting_seconds = float(new_settings.max_sitting_minutes * 60)
            self.fatigue_tracker.max_bad_posture_seconds = float(new_settings.max_bad_posture_minutes * 60)
            self.posture_analyzer.neck_threshold_deg = new_settings.neck_angle_threshold_deg
            self.posture_analyzer.torso_threshold_deg = new_settings.torso_angle_threshold_deg
            self.exercise_verifier.exercise_type = new_settings.exercise_type
            self.exercise_verifier.target_seconds = new_settings.exercise_duration_seconds
            self.exercise_verifier.target_reps = new_settings.exercise_target_reps
            self.exercise_verifier.standing_knee_threshold = new_settings.standing_leg_angle_threshold

            if old_cam != new_settings.camera_index:
                self._release_camera()
                self._open_camera()

    def reset_fatigue(self) -> None:
        """Reinicia los contadores de fatiga tras pausa completada."""
        with self._lock:
            self.fatigue_tracker.reset_after_break()

    def stop(self) -> None:
        """Detiene la ejecución del worker y espera la terminación limpia."""
        self._is_running = False
        self.wait(2000)

    # -------------------------------------------------------------
    # Gestión Interna de Cámara OpenCV
    # -------------------------------------------------------------

    def _open_camera(self) -> bool:
        """Inicializa la captura con DirectShow o default."""
        try:
            self.cap = cv2.VideoCapture(self.settings.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.settings.camera_index)
            return self.cap is not None and self.cap.isOpened()
        except Exception as e:
            print(f"[VisionWorker] Error abriendo cámara #{self.settings.camera_index}: {e}")
            return False

    def _ensure_camera_open(self) -> bool:
        if self.cap is None or not self.cap.isOpened():
            return self._open_camera()
        return True

    def _release_camera(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _autofind_alternative_camera(self) -> None:
        """Conmuta a una cámara alternativa con señal activa si la actual emite negro."""
        try:
            cams = get_available_cameras()
            if len(cams) <= 1:
                return
            for c_idx, c_name in cams:
                if c_idx == self.settings.camera_index:
                    continue
                test_cap = cv2.VideoCapture(c_idx, cv2.CAP_DSHOW)
                if not test_cap.isOpened():
                    test_cap = cv2.VideoCapture(c_idx)
                if test_cap.isOpened():
                    t_ret, t_frame = test_cap.read()
                    test_cap.release()
                    if t_ret and t_frame is not None and t_frame.mean() > 5.0:
                        print(f"[VisionWorker] Cámara alternativa activa detectada: {c_name} (#{c_idx}). Cambiando...")
                        self._release_camera()
                        self.settings.camera_index = c_idx
                        self.settings.save()
                        self._open_camera()
                        self.camera_switched.emit(c_idx, c_name)
                        break
        except Exception as e:
            print(f"[VisionWorker] Error en búsqueda de cámara alternativa: {e}")

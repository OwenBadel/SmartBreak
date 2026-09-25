"""
Prueba de Integración del Pipeline de Visión por Computadora de SmartBreak.
Verifica que PoseDetector, PostureAnalyzer y ExerciseVerifier se comuniquen sin errores.
"""

import unittest
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.pose_detector import PoseDetector, NormalizedPoint, PoseDetectionResult
from vision.posture_analyzer import PostureAnalyzer
from vision.exercise_verifier import ExerciseVerifier


class TestVisionPipeline(unittest.TestCase):
    """Prueba de integración del flujo de visión computacional."""

    def test_detector_blank_frame(self):
        """Verifica que el detector maneje adecuadamente un frame vacío."""
        detector = PoseDetector(static_mode=True)
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result, rgb = detector.process_frame(blank)
        self.assertIsNotNone(rgb)
        
        # Debe retornar resultado seguro sin excepciones
        analyzer = PostureAnalyzer()
        posture = analyzer.analyze(result, blank.shape)
        self.assertFalse(posture.presence)
        self.assertEqual(posture.primary_issue, "Usuario ausente")

        verifier = ExerciseVerifier()
        status = verifier.update(result, blank.shape, delta_time=0.1)
        self.assertFalse(status.is_standing)
        self.assertFalse(status.is_unlocked)

        annotated = detector.draw_landmarks(blank, result)
        self.assertEqual(annotated.shape, blank.shape)
        detector.close()

    def test_synthetic_standing_landmarks(self):
        """Verifica la detección con un esqueleto sintético erguido."""
        # Construir 33 landmarks normalizados simulando una persona erguida
        landmarks = [NormalizedPoint(x=0.5, y=0.5, z=0.0, visibility=0.95) for _ in range(33)]
        
        # Nariz y orejas
        landmarks[0] = NormalizedPoint(x=0.5, y=0.2, visibility=0.95)  # Nariz
        landmarks[7] = NormalizedPoint(x=0.48, y=0.18, visibility=0.95) # Oreja izq
        landmarks[8] = NormalizedPoint(x=0.52, y=0.18, visibility=0.95) # Oreja der

        # Hombros nivelados
        landmarks[11] = NormalizedPoint(x=0.45, y=0.28, visibility=0.95) # Hombro izq
        landmarks[12] = NormalizedPoint(x=0.55, y=0.28, visibility=0.95) # Hombro der

        # Caderas
        landmarks[23] = NormalizedPoint(x=0.46, y=0.55, visibility=0.95) # Cadera izq
        landmarks[24] = NormalizedPoint(x=0.54, y=0.55, visibility=0.95) # Cadera der

        # Rodillas rectas
        landmarks[25] = NormalizedPoint(x=0.46, y=0.75, visibility=0.95) # Rodilla izq
        landmarks[26] = NormalizedPoint(x=0.54, y=0.75, visibility=0.95) # Rodilla der

        # Tobillos rectos
        landmarks[27] = NormalizedPoint(x=0.46, y=0.95, visibility=0.95) # Tobillo izq
        landmarks[28] = NormalizedPoint(x=0.54, y=0.95, visibility=0.95) # Tobillo der

        # Brazos extendidos hacia arriba (overhead stretch)
        landmarks[13] = NormalizedPoint(x=0.44, y=0.15, visibility=0.95) # Codo izq
        landmarks[14] = NormalizedPoint(x=0.56, y=0.15, visibility=0.95) # Codo der
        landmarks[15] = NormalizedPoint(x=0.44, y=0.05, visibility=0.95) # Muñeca izq (arriba de nariz 0.2)
        landmarks[16] = NormalizedPoint(x=0.56, y=0.05, visibility=0.95) # Muñeca der (arriba de nariz 0.2)

        synthetic_result = PoseDetectionResult(landmarks=landmarks)
        img_shape = (480, 640, 3)

        # 1. Posture Analyzer debe detectar presencia y buena postura
        analyzer = PostureAnalyzer()
        posture = analyzer.analyze(synthetic_result, img_shape)
        self.assertTrue(posture.presence)
        self.assertFalse(posture.is_bad_posture)
        self.assertIn("Correcta", posture.primary_issue)

        # 2. Exercise Verifier debe detectar de pie y posición overhead stretch
        verifier = ExerciseVerifier(exercise_type="overhead_stretch", target_seconds=5)
        status = verifier.update(synthetic_result, img_shape, delta_time=1.0)
        self.assertTrue(status.is_standing)
        self.assertGreater(status.knee_angle, 165.0)
        self.assertIn("Posición perfecta", status.feedback_message)
        self.assertAlmostEqual(status.elapsed_seconds, 1.0)

    def test_tasks_api_pose_landmarks_extraction(self):
        """Verifica que process_frame con Tasks API extraiga correctamente los 33 puntos sin UnboundLocalError."""
        from unittest.mock import MagicMock
        detector = PoseDetector(static_mode=True)
        
        # Simular resultado de Tasks API con 1 persona detectada
        mock_raw_lm = [MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9, presence=0.9) for _ in range(33)]
        mock_tasks_result = MagicMock()
        mock_tasks_result.pose_landmarks = [mock_raw_lm]
        
        # Inyectar mock en _landmarker
        detector.backend = "tasks"
        detector._landmarker = MagicMock()
        detector._landmarker.detect.return_value = mock_tasks_result
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result, rgb = detector.process_frame(frame)
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.landmarks)
        self.assertEqual(len(result.landmarks), 33)
        self.assertAlmostEqual(result.landmarks[0].x, 0.5)
        
        # Verificar que el dibujo de esqueleto sobre el frame funcione sin fallos
        annotated = detector.draw_landmarks(frame, result)
        self.assertEqual(annotated.shape, frame.shape)
        detector.close()


if __name__ == "__main__":
    unittest.main()

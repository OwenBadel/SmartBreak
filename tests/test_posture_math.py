"""
Pruebas Unitarias para el Motor Trigonométrico y Máquinas de Estado de SmartBreak.
Verifica la exactitud matemática de los ángulos articulares y los acumuladores de fatiga.
"""

import math
import unittest
from pathlib import Path
import sys

# Asegurar importación del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.posture_analyzer import PostureAnalyzer
from core.fatigue_tracker import FatigueTracker
from vision.exercise_verifier import ExerciseVerifier


class TestPostureMath(unittest.TestCase):
    """Pruebas de cálculos vectoriales y trigonométricos."""

    def test_angle_2d_right_angle(self):
        """Verifica que un ángulo recto retorne 90 grados."""
        p_a = (0.0, 1.0)
        p_b = (0.0, 0.0)  # Vértice
        p_c = (1.0, 0.0)
        angle = PostureAnalyzer.calculate_angle_2d(p_a, p_b, p_c)
        self.assertAlmostEqual(angle, 90.0, places=2)

    def test_angle_2d_straight_line(self):
        """Verifica que una línea recta retorne 180 grados (pierna extendida)."""
        p_a = (0.0, -1.0)
        p_b = (0.0, 0.0)
        p_c = (0.0, 1.0)
        angle = PostureAnalyzer.calculate_angle_2d(p_a, p_b, p_c)
        self.assertAlmostEqual(angle, 180.0, places=2)

    def test_angle_2d_acute_angle(self):
        """Verifica un ángulo agudo de 45 grados."""
        p_a = (1.0, 1.0)
        p_b = (0.0, 0.0)
        p_c = (1.0, 0.0)
        angle = PostureAnalyzer.calculate_angle_2d(p_a, p_b, p_c)
        self.assertAlmostEqual(angle, 45.0, places=2)

    def test_vector_angle_with_vertical(self):
        """Verifica el cálculo de inclinación respecto a la vertical superior."""
        origin = (100.0, 200.0)
        
        # Punto perfectamente vertical hacia arriba (cuello erguido)
        target_upright = (100.0, 100.0)
        ang_upright = PostureAnalyzer.calculate_vector_angle_with_vertical(origin, target_upright)
        self.assertAlmostEqual(ang_upright, 0.0, places=2)

        # Inclinación a 45 grados hacia la derecha (cabeza adelantada)
        target_tilted = (200.0, 100.0)
        ang_tilted = PostureAnalyzer.calculate_vector_angle_with_vertical(origin, target_tilted)
        self.assertAlmostEqual(ang_tilted, 45.0, places=2)


class TestFatigueTracker(unittest.TestCase):
    """Pruebas del acumulador de fatiga y sedentarismo."""

    def setUp(self):
        self.tracker = FatigueTracker(max_sitting_minutes=50, max_bad_posture_minutes=15)

    def test_sitting_time_accumulation(self):
        """El tiempo sentado debe incrementarse cuando hay presencia."""
        should_break, _ = self.tracker.update(delta_time=120.0, presence=True, bad_posture=False)
        self.assertFalse(should_break)
        self.assertEqual(self.tracker.sitting_seconds, 120.0)
        self.assertEqual(self.tracker.bad_posture_seconds, 0.0)

    def test_absence_does_not_accumulate(self):
        """Si el usuario se aleja del escritorio, el tiempo no debe acumularse."""
        self.tracker.update(delta_time=60.0, presence=False, bad_posture=False)
        self.assertEqual(self.tracker.sitting_seconds, 0.0)

    def test_bad_posture_break_trigger(self):
        """Disparo de pausa cuando la mala postura excede los 15 minutos (900 seg)."""
        # 14 minutos de mala postura (840 seg) -> No debe disparar
        should_break, _ = self.tracker.update(delta_time=840.0, presence=True, bad_posture=True)
        self.assertFalse(should_break)

        # 2 minutos adicionales (total 960 seg > 900 seg) -> Debe disparar
        should_break, reason = self.tracker.update(delta_time=120.0, presence=True, bad_posture=True)
        self.assertTrue(should_break)
        self.assertIn("Mala postura", reason)

    def test_sitting_break_trigger(self):
        """Disparo de pausa cuando el tiempo sentado excede los 50 minutos (3000 seg)."""
        should_break, reason = self.tracker.update(delta_time=3050.0, presence=True, bad_posture=False)
        self.assertTrue(should_break)
        self.assertIn("Límite de tiempo sentado", reason)

    def test_reset_after_break(self):
        """Verifica que el reinicio limpie adecuadamente todos los acumuladores."""
        self.tracker.update(delta_time=3100.0, presence=True, bad_posture=True)
        self.assertTrue(self.tracker.break_triggered)

        self.tracker.reset_after_break()
        self.assertEqual(self.tracker.sitting_seconds, 0.0)
        self.assertEqual(self.tracker.bad_posture_seconds, 0.0)
        self.assertFalse(self.tracker.break_triggered)

    def test_prolonged_absence_resets_sitting_time(self):
        """Verifica que una ausencia de más de 15 minutos (900s) reinicie el tiempo sentado."""
        # 40 minutos sentado acumulados
        self.tracker.update(delta_time=2400.0, presence=True, bad_posture=False)
        self.assertEqual(self.tracker.sitting_seconds, 2400.0)

        # Ausencia breve de 2 minutos (no reinicia)
        self.tracker.update(delta_time=120.0, presence=False, bad_posture=False)
        self.assertGreater(self.tracker.sitting_seconds, 2000.0)

        # Ausencia prolongada acumulando más de 15 minutos (900 seg)
        self.tracker.update(delta_time=800.0, presence=False, bad_posture=False)
        self.assertEqual(self.tracker.sitting_seconds, 0.0)
        self.assertEqual(self.tracker.bad_posture_seconds, 0.0)


class TestExerciseVerifierLogic(unittest.TestCase):
    """Pruebas de la máquina de estados de sentadillas y tiempo de ejercicio."""

    def test_squats_state_machine(self):
        """Verifica la transición UP -> DOWN -> UP para conteo de repetición."""
        verifier = ExerciseVerifier(exercise_type="squats", target_reps=3)
        self.assertEqual(verifier.completed_reps, 0)

        # Paso 1: En sentadilla profunda (< 105 grados)
        feedback1 = verifier._process_squats(current_knee_angle=95.0)
        self.assertEqual(verifier.squat_state, "DOWN")
        self.assertEqual(verifier.completed_reps, 0)
        self.assertIn("Buena flexión", feedback1)

        # Paso 2: Retorno a posición de pie (> 160 grados)
        feedback2 = verifier._process_squats(current_knee_angle=170.0)
        self.assertEqual(verifier.squat_state, "UP")
        self.assertEqual(verifier.completed_reps, 1)
        self.assertIn("Repetición válida", feedback2)

    def test_squats_kinematic_fallback_without_legs(self):
        """Verifica que las sentadillas funcionen mediante descenso de hombros cuando las piernas no están en el encuadre."""
        from vision.pose_detector import NormalizedPoint, PoseDetectionResult

        verifier = ExerciseVerifier(exercise_type="squats", target_reps=3)
        img_shape = (480, 640, 3)

        # Esqueleto con piernas fuera de cuadro (visibilidad 0.0 en rodillas y tobillos)
        def make_pose(shoulder_y: float):
            lms = [NormalizedPoint(x=0.5, y=0.5, z=0.0, visibility=0.0) for _ in range(33)]
            lms[0] = NormalizedPoint(x=0.5, y=shoulder_y - 0.1, visibility=0.9)  # Nariz
            lms[11] = NormalizedPoint(x=0.4, y=shoulder_y, visibility=0.9)       # Hombro izq
            lms[12] = NormalizedPoint(x=0.6, y=shoulder_y, visibility=0.9)       # Hombro der
            return PoseDetectionResult(landmarks=lms)

        # 1. Posición erguida de pie (hombros arriba en y=0.25)
        st1 = verifier.update(make_pose(0.25), img_shape, delta_time=0.1)
        self.assertTrue(st1.is_standing)
        self.assertEqual(st1.completed_reps, 0)

        # 2. Descenso profundo en sentadilla (hombros bajan a y=0.45)
        st2 = verifier.update(make_pose(0.45), img_shape, delta_time=0.1)
        self.assertEqual(verifier.squat_state, "DOWN")
        self.assertLess(st2.knee_angle, 120.0)

        # 3. Regreso a posición de pie erguido (hombros suben de nuevo a y=0.25)
        st3 = verifier.update(make_pose(0.25), img_shape, delta_time=0.1)
        self.assertEqual(verifier.squat_state, "UP")
        self.assertEqual(verifier.completed_reps, 1)
        self.assertIn("Repetición válida", st3.feedback_message)


class TestFrontalPostureDetection(unittest.TestCase):
    """Pruebas de detección de cuello adelantado y compresión 3D en cámara frontal."""

    def test_frontal_forward_head_detected(self):
        """Verifica que un cuello proyectado hacia adelante en Z active la alerta en vista frontal."""
        from vision.pose_detector import NormalizedPoint, PoseDetectionResult

        analyzer = PostureAnalyzer(neck_threshold_deg=35.0)
        img_shape = (480, 640, 3)

        lms = [NormalizedPoint(x=0.5, y=0.5, z=0.0, visibility=0.0) for _ in range(33)]
        lms[0] = NormalizedPoint(x=0.5, y=0.20, z=-0.22, visibility=0.95)   # Nariz adelantada
        lms[7] = NormalizedPoint(x=0.48, y=0.19, z=-0.20, visibility=0.95)  # Oreja izq adelantada
        lms[8] = NormalizedPoint(x=0.52, y=0.19, z=-0.20, visibility=0.95)  # Oreja der adelantada
        lms[11] = NormalizedPoint(x=0.35, y=0.28, z=0.0, visibility=0.95)   # Hombro izq
        lms[12] = NormalizedPoint(x=0.65, y=0.28, z=0.0, visibility=0.95)   # Hombro der

        result = PoseDetectionResult(landmarks=lms)
        posture = analyzer.analyze(result, img_shape)

        self.assertTrue(posture.presence)
        self.assertTrue(posture.is_bad_posture)
        self.assertGreaterEqual(posture.neck_angle, 35.0)
        self.assertIn("Cuello adelantado", posture.primary_issue)


if __name__ == "__main__":
    unittest.main()

"""
Pruebas Unitarias para el VisionWorker Desacoplado de SmartBreak.
Verifica el ciclo de vida del QThread, el puente de señales y la conmutación entre modos.
"""

import unittest
from PyQt6.QtWidgets import QApplication
from config.settings import Settings
from core.vision_worker import VisionWorker


app = QApplication.instance() or QApplication([])


class TestVisionWorker(unittest.TestCase):
    """Pruebas del ciclo de vida y control de concurrencia de VisionWorker."""

    def setUp(self):
        self.settings = Settings()
        self.settings.passive_sample_interval_sec = 0.1
        self.settings.max_sitting_minutes = 50
        self.worker = VisionWorker(self.settings)

    def tearDown(self):
        if self.worker.isRunning():
            self.worker.stop()

    def test_worker_initial_state(self):
        """Verifica que el worker inicialice sus componentes desacoplados."""
        self.assertFalse(self.worker.isRunning())
        self.assertFalse(self.worker._is_active_break)
        self.assertIsNotNone(self.worker.fatigue_tracker)
        self.assertIsNotNone(self.worker.pose_detector)
        self.assertIsNotNone(self.worker.posture_analyzer)
        self.assertIsNotNone(self.worker.exercise_verifier)

    def test_set_active_break_mode(self):
        """Verifica la conmutación segura al modo de pausa activa."""
        self.worker.set_active_break_mode(True)
        self.assertTrue(self.worker._is_active_break)

        self.worker.set_active_break_mode(False)
        self.assertFalse(self.worker._is_active_break)

    def test_update_settings(self):
        """Verifica que update_settings sincronice umbrales en todos los componentes."""
        new_settings = Settings(
            max_sitting_minutes=30,
            max_bad_posture_minutes=10,
            exercise_type="squats",
            exercise_target_reps=15
        )
        self.worker.update_settings(new_settings)

        self.assertEqual(self.worker.fatigue_tracker.max_sitting_seconds, 1800.0)
        self.assertEqual(self.worker.fatigue_tracker.max_bad_posture_seconds, 600.0)
        self.assertEqual(self.worker.exercise_verifier.exercise_type, "squats")
        self.assertEqual(self.worker.exercise_verifier.target_reps, 15)

    def test_reset_fatigue(self):
        """Verifica que reset_fatigue limpie el estado del acumulador."""
        self.worker.fatigue_tracker.sitting_seconds = 1500.0
        self.worker.reset_fatigue()
        self.assertEqual(self.worker.fatigue_tracker.sitting_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()

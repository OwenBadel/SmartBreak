"""
Pruebas Unitarias para el Diálogo Deportivo de Estado Ergonómico (StatusDialog).
Verifica la inicialización, la telemetría en tiempo real y el formato de textos dinámicos.
"""

import unittest
from PyQt6.QtWidgets import QApplication
from ui.status_dialog import StatusDialog


app = QApplication.instance() or QApplication([])


class TestStatusDialog(unittest.TestCase):
    """Pruebas del ciclo de vida y reactividad del StatusDialog."""

    def setUp(self):
        self.initial_summary = {
            "is_present": False,
            "is_bad_posture": False,
            "sitting_minutes": 0.0,
            "max_sitting_minutes": 50,
            "percent_sitting": 0.0,
            "bad_posture_minutes": 0.0,
            "max_bad_posture_minutes": 15,
            "percent_bad_posture": 0.0,
            "sitting_seconds": 0.0,
            "bad_posture_seconds": 0.0,
            "minutes_until_break": 15.0
        }

    def test_initial_values_absent(self):
        """Verifica que el diálogo refleje correctamente el estado ausente inicial."""
        dlg = StatusDialog(
            summary=self.initial_summary,
            exercise_type="overhead_stretch",
            camera_index=1,
            camera_name="OBS Virtual Camera"
        )
        self.assertIn("AUSENTE", dlg.val_pres.text())
        self.assertIn("00m 00s", dlg.sit_val.text())
        self.assertEqual(dlg.bar_sit.value(), 0)
        self.assertIn("OBS Virtual Camera", dlg.lbl_camera.text())
        dlg.close()

    def test_live_telemetry_refresh(self):
        """Verifica que al invocar _refresh_telemetry se actualicen los widgets en vivo."""
        current_state = dict(self.initial_summary)

        def mock_provider():
            return current_state

        dlg = StatusDialog(
            summary=self.initial_summary,
            exercise_type="overhead_stretch",
            summary_provider=mock_provider,
            camera_index=1
        )

        # Simular usuario presente y 125 segundos sentado
        current_state["is_present"] = True
        current_state["is_bad_posture"] = False
        current_state["sitting_seconds"] = 125.0
        current_state["sitting_minutes"] = 125.0 / 60.0
        current_state["percent_sitting"] = 4.1
        current_state["minutes_until_break"] = 14.0

        dlg._refresh_telemetry()

        self.assertIn("EN ESCRITORIO", dlg.val_pres.text())
        self.assertIn("02m 05s", dlg.sit_val.text())
        self.assertEqual(dlg.bar_sit.value(), 4)
        self.assertIn("ERGONÓMICA", dlg.val_post.text())
        dlg.close()


if __name__ == "__main__":
    unittest.main()

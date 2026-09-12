import io
import unittest
from contextlib import redirect_stdout

from relativistic_engine import ExperimentConfig, run_experiment


class ExperimentOutputTests(unittest.TestCase):
    def test_output_uses_one_compact_table_for_both_frames(self) -> None:
        config = ExperimentConfig(
            particle_count=20,
            preparation_time=0.1,
            compression_stages=(0.0,),
        )
        output = io.StringIO()

        with redirect_stdout(output):
            run_experiment(config)

        report = output.getvalue()
        self.assertEqual(report.count("STAGE"), 1)
        self.assertIn("0.0%  WALL", report)
        self.assertIn("PISTON", report)
        self.assertIn("IDEAL-GAS READINGS", report)
        self.assertIn("CONSERVATION", report)
        self.assertNotIn("MATCHED PISTON EVENT", report)

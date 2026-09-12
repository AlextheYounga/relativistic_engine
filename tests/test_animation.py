import json
import tempfile
import unittest
from pathlib import Path

from relativistic_engine import ExperimentConfig, write_animation_json


class AnimationExportTests(unittest.TestCase):
    def test_writes_matched_states_for_both_frames(self) -> None:
        config = ExperimentConfig(
            particle_count=8,
            preparation_time=0.1,
            piston_proper_length=2.0,
            compression_stages=(0.0, 0.1),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "simulation.json"
            write_animation_json(config, output_path, frame_count=3)
            document = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(document["metadata"]["frame_count"], 3)
        self.assertEqual(document["metadata"]["particle_count"], 8)
        self.assertEqual(document["metadata"]["temperature_unit"], "deg F")
        self.assertEqual(len(document["frames"]), 3)
        self.assertEqual(document["frames"][0]["compression_fraction"], 0.0)
        self.assertEqual(document["frames"][-1]["compression_fraction"], 0.1)

        initial_frame = document["frames"][0]
        self.assertAlmostEqual(initial_frame["wall"]["temperature"], 70.0)
        self.assertGreater(initial_frame["wall"]["model_temperature"], 0.0)
        self.assertLess(
            initial_frame["wall"]["piston_length"],
            initial_frame["piston"]["piston_length"],
        )
        self.assertEqual(initial_frame["piston"]["piston_length"], 2.0)
        self.assertEqual(initial_frame["wall"]["piston_velocity"], 0.95)
        self.assertEqual(initial_frame["piston"]["piston_velocity"], 0.0)
        self.assertEqual(
            initial_frame["wall"]["piston_face_area"],
            initial_frame["piston"]["piston_face_area"],
        )
        self.assertGreater(
            initial_frame["wall"]["chamber_length"],
            initial_frame["piston"]["chamber_length"],
        )

        for frame in document["frames"]:
            self.assertEqual(len(frame["wall"]["particle_positions"]), 8)
            self.assertEqual(len(frame["piston"]["particle_positions"]), 8)
            self.assertGreater(frame["wall"]["temperature"], 0.0)
            self.assertGreater(frame["piston"]["temperature"], 0.0)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path


class WebAssetTests(unittest.TestCase):
    def test_hidden_panels_are_not_overridden_by_component_styles(self) -> None:
        repository_root = Path(__file__).parent.parent
        stylesheet = repository_root / "web" / "styles.css"

        css = stylesheet.read_text(encoding="utf-8")

        self.assertIn("[hidden] { display: none !important; }", css)

    def test_animation_uses_fixed_frame_bounds_and_engine_components(self) -> None:
        repository_root = Path(__file__).parent.parent
        javascript = (repository_root / "web" / "animation.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("state.bounds = calculateSharedBounds()", javascript)
        self.assertIn("drawPiston(context", javascript)
        self.assertIn("drawEndWall(context", javascript)
        self.assertIn("drawActuatorRod(context", javascript)


if __name__ == "__main__":
    unittest.main()

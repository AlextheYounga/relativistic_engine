"""Export independently evolved frame states for the browser animation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .engine import Engine
from .experiment import (
    ExperimentConfig,
    build_engines,
    target_time_for_compression_fraction,
)


def write_animation_json(
    config: ExperimentConfig,
    output_path: Path,
    *,
    frame_count: int = 121,
    final_compression_fraction: float | None = None,
) -> Path:
    """Simulate matched frame states and write browser-ready JSON."""
    if frame_count < 2:
        raise ValueError("Animation requires at least two frames")

    final_fraction = _final_compression_fraction(
        config,
        final_compression_fraction,
    )
    wall_engine, piston_engine = build_engines(config)
    frames = []

    for fraction in np.linspace(0.0, final_fraction, frame_count):
        compression_fraction = float(fraction)
        wall_engine.run_until(
            target_time_for_compression_fraction(
                "WALL",
                compression_fraction,
                config.initial_chamber_length,
                config.piston_speed,
            )
        )
        piston_engine.run_until(
            target_time_for_compression_fraction(
                "PISTON",
                compression_fraction,
                config.initial_chamber_length,
                config.piston_speed,
            )
        )
        frames.append(
            {
                "compression_fraction": compression_fraction,
                "wall": _frame_state(wall_engine),
                "piston": _frame_state(piston_engine),
            }
        )

    document = {
        "metadata": {
            "particle_count": config.particle_count,
            "piston_speed": config.piston_speed,
            "frame_count": frame_count,
            "temperature_formula": "T = P * V / (m * R)",
        },
        "frames": frames,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(document, output_file, separators=(",", ":"), allow_nan=False)
    return output_path


def _final_compression_fraction(
    config: ExperimentConfig,
    requested_fraction: float | None,
) -> float:
    if requested_fraction is None:
        if not config.compression_stages:
            raise ValueError("At least one compression stage is required")
        requested_fraction = max(config.compression_stages)
    if not 0.0 <= requested_fraction < 1.0:
        raise ValueError(
            "Final compression fraction must be at least 0 and less than 1"
        )
    return requested_fraction


def _frame_state(engine: Engine) -> dict[str, Any]:
    snapshot = engine.snapshot()
    return {
        "time": snapshot.time,
        "piston_position": snapshot.piston_position,
        "wall_position": snapshot.wall_position,
        "chamber_volume": snapshot.chamber_volume,
        "pressure": snapshot.average_gas_stress,
        "temperature": snapshot.ideal_gas_temperature,
        "particle_positions": engine.positions.tolist(),
        "particle_velocities": engine.velocities.tolist(),
    }

"""Construction of physically equivalent initial frame slices."""

from __future__ import annotations

import numpy as np

from .relativity import gamma_from_velocity, transform_event, transform_velocity


def reflected_billiard_state(
    initial_position: np.ndarray,
    initial_velocity: np.ndarray,
    elapsed_time: np.ndarray | float,
    chamber_length: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Advance free motion with specular reflections between static walls."""
    unfolded = initial_position + initial_velocity * elapsed_time
    period = 2.0 * chamber_length
    folded = np.mod(unfolded, period)
    moving_right = folded <= chamber_length
    position = np.where(moving_right, folded, period - folded)
    velocity = np.where(moving_right, initial_velocity, -initial_velocity)
    return position, velocity


def build_equivalent_piston_frame_slice(
    positions_a: np.ndarray,
    velocities_a: np.ndarray,
    chamber_length: float,
    boost_speed: float,
    preparation_time: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Build the Frame-B slice simultaneous with the piston event."""
    lower = np.zeros_like(positions_a)
    upper = np.full_like(positions_a, boost_speed * chamber_length)

    for _ in range(70):
        middle = 0.5 * (lower + upper)
        position, _ = reflected_billiard_state(
            positions_a, velocities_a, middle, chamber_length
        )
        residual = middle - boost_speed * position
        upper = np.where(residual >= 0.0, middle, upper)
        lower = np.where(residual < 0.0, middle, lower)

    elapsed = 0.5 * (lower + upper)
    position_a, velocity_a = reflected_billiard_state(
        positions_a, velocities_a, elapsed, chamber_length
    )
    time_a = -preparation_time + elapsed
    time_b, position_b = transform_event(time_a, position_a, boost_speed)
    velocity_b = transform_velocity(velocity_a, boost_speed)
    expected_time_b = -gamma_from_velocity(boost_speed) * preparation_time
    max_error = float(np.max(np.abs(time_b - expected_time_b)))
    if max_error > 1e-10:
        raise RuntimeError(
            f"Failed to construct a simultaneous Frame-B slice; max error={max_error:.3e}"
        )
    return position_b, velocity_b, expected_time_b

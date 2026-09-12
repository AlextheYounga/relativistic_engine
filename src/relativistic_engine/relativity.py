"""Small special-relativity transformations used by the simulation."""

from __future__ import annotations

import numpy as np

from .constants import PARTICLE_MASS


def _scalar_or_array(value: np.ndarray) -> np.ndarray | float:
    return float(value) if value.ndim == 0 else value


def gamma_from_velocity(velocity: np.ndarray | float) -> np.ndarray | float:
    """Return the Lorentz factor for a velocity with ``|v| < 1``."""
    value = np.asarray(velocity)
    return _scalar_or_array(1.0 / np.sqrt(1.0 - value * value))


def energy_from_velocity(
    velocity: np.ndarray | float, mass: float = PARTICLE_MASS
) -> np.ndarray | float:
    return mass * gamma_from_velocity(velocity)


def momentum_from_velocity(
    velocity: np.ndarray | float, mass: float = PARTICLE_MASS
) -> np.ndarray | float:
    return mass * gamma_from_velocity(velocity) * np.asarray(velocity)


def velocity_from_energy_momentum(energy: float, momentum: float) -> float:
    return momentum / energy


def transform_velocity(
    velocity: np.ndarray | float, frame_speed: float
) -> np.ndarray | float:
    """Transform velocity into a frame moving at ``frame_speed``."""
    value = np.asarray(velocity)
    transformed = (value - frame_speed) / (1.0 - frame_speed * value)
    return _scalar_or_array(transformed)


def inverse_transform_velocity(
    velocity_prime: np.ndarray | float, frame_speed: float
) -> np.ndarray | float:
    """Apply the inverse of :func:`transform_velocity`."""
    value = np.asarray(velocity_prime)
    transformed = (value + frame_speed) / (1.0 + frame_speed * value)
    return _scalar_or_array(transformed)


def transform_event(
    time: np.ndarray | float,
    position: np.ndarray | float,
    frame_speed: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Lorentz transform ``(t, x)`` to ``(t', x')``."""
    gamma = gamma_from_velocity(frame_speed)
    time_value = np.asarray(time)
    position_value = np.asarray(position)
    return (
        gamma * (time_value - frame_speed * position_value),
        gamma * (position_value - frame_speed * time_value),
    )


def momentum_in_rest_frame(
    energy: float, momentum: float, object_velocity: float
) -> float:
    gamma = gamma_from_velocity(object_velocity)
    return gamma * (momentum - object_velocity * energy)


def energy_in_rest_frame(
    energy: float, momentum: float, object_velocity: float
) -> float:
    gamma = gamma_from_velocity(object_velocity)
    return gamma * (energy - object_velocity * momentum)

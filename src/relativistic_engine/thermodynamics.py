"""Bulk thermodynamic measurements made on one frame's spatial slice."""

from __future__ import annotations

import numpy as np

from .constants import BOLTZMANN_CONSTANT


def bulk_average_pressure(
    momenta: np.ndarray,
    velocities: np.ndarray,
    chamber_volume: float,
) -> float:
    """Return the chamber-average longitudinal momentum flux."""
    if chamber_volume <= 0.0:
        raise ValueError("Chamber volume must be positive")
    if momenta.shape != velocities.shape:
        raise ValueError("Particle momenta and velocities must have the same shape")
    return float(np.sum(momenta * velocities) / chamber_volume)


def apparent_bulk_temperature(
    pressure: float,
    chamber_volume: float,
    particle_count: int,
    boltzmann_constant: float = BOLTZMANN_CONSTANT,
) -> float:
    """Infer an observer-frame bulk temperature from ``PV = Nk_B T``."""
    if chamber_volume <= 0.0:
        raise ValueError("Chamber volume must be positive")
    if particle_count <= 0:
        raise ValueError("Particle count must be positive")
    if boltzmann_constant <= 0.0:
        raise ValueError("Boltzmann constant must be positive")
    return pressure * chamber_volume / (particle_count * boltzmann_constant)

"""Bulk thermodynamic measurements made on one frame's spatial slice."""

from __future__ import annotations

import numpy as np


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


def ideal_gas_temperature(
    pressure: float,
    chamber_volume: float,
    trapped_gas_mass: float,
    specific_gas_constant: float,
) -> float:
    """Infer a bulk gas temperature from ``PV = mRT``."""
    if chamber_volume <= 0.0:
        raise ValueError("Chamber volume must be positive")
    if trapped_gas_mass <= 0.0:
        raise ValueError("Trapped gas mass must be positive")
    if specific_gas_constant <= 0.0:
        raise ValueError("Specific gas constant must be positive")
    return pressure * chamber_volume / (trapped_gas_mass * specific_gas_constant)

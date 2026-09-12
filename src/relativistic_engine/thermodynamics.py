"""Bulk thermodynamic measurements made on one frame's spatial slice."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


ABSOLUTE_ZERO_FAHRENHEIT = -459.67


def fahrenheit_to_kelvin(temperature: float) -> float:
    """Convert a Fahrenheit temperature to kelvin."""
    return (temperature - ABSOLUTE_ZERO_FAHRENHEIT) * 5.0 / 9.0


def kelvin_to_fahrenheit(temperature: float) -> float:
    """Convert a kelvin temperature to Fahrenheit."""
    if temperature < 0.0:
        raise ValueError("Kelvin temperature cannot be negative")
    return temperature * 9.0 / 5.0 + ABSOLUTE_ZERO_FAHRENHEIT


@dataclass(frozen=True)
class TemperatureCalibration:
    """Map normalized model temperatures onto an absolute Fahrenheit scale."""

    reference_model_temperature: float
    reference_fahrenheit: float

    def __post_init__(self) -> None:
        if self.reference_model_temperature <= 0.0:
            raise ValueError("Reference model temperature must be positive")
        if self.reference_fahrenheit <= ABSOLUTE_ZERO_FAHRENHEIT:
            raise ValueError("Reference temperature must be above absolute zero")

    def to_fahrenheit(self, model_temperature: float) -> float:
        """Scale an absolute model temperature and return Fahrenheit."""
        if model_temperature < 0.0:
            raise ValueError("Model temperature cannot be negative")
        reference_kelvin = fahrenheit_to_kelvin(self.reference_fahrenheit)
        temperature_kelvin = (
            model_temperature / self.reference_model_temperature * reference_kelvin
        )
        return kelvin_to_fahrenheit(temperature_kelvin)


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

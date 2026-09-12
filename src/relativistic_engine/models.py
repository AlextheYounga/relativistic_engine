"""Data records shared by simulation and reporting code."""

from dataclasses import dataclass

import numpy as np


@dataclass
class CollisionEvent:
    boundary: str
    time: float
    position: float
    incoming_energy: float
    incoming_momentum: float
    outgoing_energy: float
    outgoing_momentum: float
    boundary_velocity: float
    incoming_rest_kinetic_energy: float
    rest_frame_impulse: float


@dataclass
class IntervalBookkeeping:
    elapsed_coordinate_time: float = 0.0
    end_wall_proper_time: float = 0.0
    end_wall_frame_impulse: float = 0.0
    end_wall_rest_impulse: float = 0.0

    def reset(self) -> None:
        self.elapsed_coordinate_time = 0.0
        self.end_wall_proper_time = 0.0
        self.end_wall_frame_impulse = 0.0
        self.end_wall_rest_impulse = 0.0


@dataclass
class Snapshot:
    frame_name: str
    time: float
    compression_fraction: float
    piston_position: float
    piston_velocity: float
    wall_position: float
    wall_velocity: float
    chamber_length: float
    chamber_volume: float
    number_density: float
    energy_density: float
    average_gas_stress: float
    end_wall_pressure_frame_native: float
    end_wall_pressure_rest_frame: float
    mean_velocity: float
    mean_momentum: float
    mean_energy: float
    bulk_velocity_from_total_four_momentum: float
    random_kinetic_energy_per_particle: float
    internal_energy_estimate: float
    thermal_temperature_like_1d: float
    apparent_bulk_temperature: float
    velocity_quantiles: np.ndarray
    momentum_quantiles: np.ndarray
    energy_quantiles: np.ndarray
    local_bin_density: np.ndarray
    local_bin_stress: np.ndarray

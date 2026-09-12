"""Experiment configuration, setup, and command-line orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from .boundaries import BoundaryWorldlines
from .constants import AREA, C
from .engine import Engine
from .preparation import build_equivalent_piston_frame_slice
from .relativity import energy_from_velocity, gamma_from_velocity, momentum_from_velocity, transform_velocity
from .reporting import print_conservation, print_snapshot_pair
from .models import Snapshot


@dataclass
class ExperimentConfig:
    speed_of_light: float = C
    initial_chamber_length: float = 10.0
    cross_sectional_area: float = AREA
    piston_speed: float = 0.95
    particle_count: int = 1000
    preparation_time: float = 12.0
    thermal_rapidity_sigma: float = 0.20
    time_step: float = 0.0025
    random_seed: int = 7
    compression_stages: Tuple[float, ...] = (0.00, 0.25, 0.50, 0.75)
    spatial_bins: int = 10


def make_initial_wall_frame_gas(config: ExperimentConfig) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(config.random_seed)
    positions = rng.uniform(0.001, config.initial_chamber_length - 0.001, config.particle_count)
    velocities = np.tanh(rng.normal(0.0, config.thermal_rapidity_sigma, config.particle_count))
    total_energy = float(np.sum(energy_from_velocity(velocities)))
    total_momentum = float(np.sum(momentum_from_velocity(velocities)))
    return positions, transform_velocity(velocities, total_momentum / total_energy)


def build_engines(config: ExperimentConfig) -> tuple[Engine, Engine]:
    positions_a, velocities_a = make_initial_wall_frame_gas(config)
    positions_b, velocities_b, initial_time_b = build_equivalent_piston_frame_slice(
        positions_a, velocities_a, config.initial_chamber_length,
        config.piston_speed, config.preparation_time,
    )
    return (
        Engine(
            frame_name="WALL", initial_time=-config.preparation_time,
            particle_positions=positions_a, particle_velocities=velocities_a,
            worldlines=BoundaryWorldlines("WALL", config.initial_chamber_length, config.piston_speed),
            time_step=config.time_step,
        ),
        Engine(
            frame_name="PISTON", initial_time=initial_time_b,
            particle_positions=positions_b, particle_velocities=velocities_b,
            worldlines=BoundaryWorldlines("PISTON", config.initial_chamber_length, config.piston_speed),
            time_step=config.time_step,
        ),
    )


def target_time_for_compression_fraction(
    frame_name: str, fraction: float, chamber_length: float, piston_speed: float
) -> float:
    """Return the coordinate time for a matched piston worldline event."""
    time_a = fraction * chamber_length / piston_speed
    if frame_name == "WALL":
        return time_a
    if frame_name == "PISTON":
        return time_a / gamma_from_velocity(piston_speed)
    raise ValueError(frame_name)


def run_experiment(config: ExperimentConfig) -> None:
    print("RELATIVISTIC PISTON TEMPERATURE TEST")
    print("=" * 95)
    print(f"particles                : {config.particle_count}")
    print(f"piston speed             : {config.piston_speed:.5f} c")
    print(f"gamma                    : {gamma_from_velocity(config.piston_speed):.8f}")
    print(f"wall-frame initial length: {config.initial_chamber_length:.5f}")
    print(f"piston-frame t=0 length  : {config.initial_chamber_length / gamma_from_velocity(config.piston_speed):.5f}")
    print(f"time step                : {config.time_step:.6f}\n")
    print("Physics mode: purely elastic piston compression only.")
    print("No wall rupture, ignition, escape, phase change, or other irreversible state is modeled.")
    engine_a, engine_b = build_engines(config)
    print(f"\nIndependent initial slices:\n  Frame A starts at t_A = {engine_a.time:.8f}\n  Frame B starts at t_B = {engine_b.time:.8f}")
    print("  These slices are physically equivalent but not the same set of simultaneous events.")
    snapshots: List[tuple[Snapshot, Snapshot]] = []
    for fraction in config.compression_stages:
        engine_a.run_until(target_time_for_compression_fraction("WALL", fraction, config.initial_chamber_length, config.piston_speed))
        engine_b.run_until(target_time_for_compression_fraction("PISTON", fraction, config.initial_chamber_length, config.piston_speed))
        snapshot_a = engine_a.snapshot_and_reset_interval(config.spatial_bins)
        snapshot_b = engine_b.snapshot_and_reset_interval(config.spatial_bins)
        snapshots.append((snapshot_a, snapshot_b))
        print_snapshot_pair(snapshot_a, snapshot_b)
    print_conservation(engine_a)
    print_conservation(engine_b)
    print("\nTEMPERATURE INTERPRETATION\n" + "=" * 95)
    print("The row 'normal frame-native T = P/n' uses each frame's simultaneous stress and density, with k_B = 1.")
    print("The bulk-removed estimate removes common motion using total four-momentum, then uses T = 2<K_random>.")
    print("This collisionless 1D toy gas is not a complete relativistic thermodynamic temperature model.")

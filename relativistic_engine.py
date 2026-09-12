#!/usr/bin/env python3
"""
Relativistic piston temperature experiment (1D kinetic toy model)
====================================================================

Purpose
-------
Evolve the same engine independently in two inertial coordinate systems:

    Frame A: initial chamber/end-wall rest frame
    Frame B: inertial frame moving at +0.95c relative to A, so the piston is
             at rest after its acceleration event.

The gas trajectories are NOT generated in A and replayed in B.  Both engines
are initialized on their own simultaneous hypersurfaces from a common,
pre-compression physical preparation and are then advanced independently.

Important limitation
--------------------
This is a 1D collisionless gas with prescribed, infinitely massive boundaries.
There is deliberately NO ignition, wall rupture, escape, chemistry, or other
irreversible state.  The only energy transfer comes from elastic collisions
with the moving piston/wall.  The experiment asks a narrower question: what
"temperature" does each independently evolved reference frame calculate?

It is NOT a full relativistic hydrodynamics or relativistic thermodynamics
solver.  In particular, P/n below is the ordinary 1D ideal-gas-style
frame-native temperature-like quantity with k_B = 1.

Units: c = 1, particle rest mass = 1, k_B = 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Basic relativity helpers
# ---------------------------------------------------------------------------

C = 1.0
PARTICLE_MASS = 1.0
AREA = 1.0


def gamma_from_velocity(velocity: np.ndarray | float) -> np.ndarray | float:
    """Lorentz factor for |v| < 1."""
    velocity = np.asarray(velocity)
    result = 1.0 / np.sqrt(1.0 - velocity * velocity)
    return float(result) if result.ndim == 0 else result


def energy_from_velocity(velocity: np.ndarray | float, mass: float = PARTICLE_MASS):
    return mass * gamma_from_velocity(velocity)


def momentum_from_velocity(velocity: np.ndarray | float, mass: float = PARTICLE_MASS):
    return mass * gamma_from_velocity(velocity) * np.asarray(velocity)


def velocity_from_energy_momentum(energy: float, momentum: float) -> float:
    return momentum / energy


def transform_velocity(velocity: np.ndarray | float, frame_speed: float):
    """Velocity in a frame moving +frame_speed relative to the old frame."""
    velocity = np.asarray(velocity)
    transformed = (velocity - frame_speed) / (1.0 - frame_speed * velocity)
    return float(transformed) if transformed.ndim == 0 else transformed


def inverse_transform_velocity(velocity_prime: np.ndarray | float, frame_speed: float):
    """Inverse of transform_velocity."""
    velocity_prime = np.asarray(velocity_prime)
    transformed = (velocity_prime + frame_speed) / (1.0 + frame_speed * velocity_prime)
    return float(transformed) if transformed.ndim == 0 else transformed


def transform_event(time: np.ndarray | float, position: np.ndarray | float, frame_speed: float):
    """Lorentz transform (t, x) -> (t', x') for boost +frame_speed."""
    gamma = gamma_from_velocity(frame_speed)
    time = np.asarray(time)
    position = np.asarray(position)
    time_prime = gamma * (time - frame_speed * position)
    position_prime = gamma * (position - frame_speed * time)
    return time_prime, position_prime


def momentum_in_rest_frame(energy: float, momentum: float, object_velocity: float) -> float:
    """Particle x-momentum as measured in an object's instantaneous rest frame."""
    gamma = gamma_from_velocity(object_velocity)
    return gamma * (momentum - object_velocity * energy)


def energy_in_rest_frame(energy: float, momentum: float, object_velocity: float) -> float:
    gamma = gamma_from_velocity(object_velocity)
    return gamma * (energy - object_velocity * momentum)


# ---------------------------------------------------------------------------
# Common physical preparation before the piston starts moving
# ---------------------------------------------------------------------------


def reflected_billiard_state(
    initial_position: np.ndarray,
    initial_velocity: np.ndarray,
    elapsed_time: np.ndarray | float,
    chamber_length: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Exact free motion with specular reflections between two STATIC walls at
    x=0 and x=L.  Used only to construct the equivalent pre-compression slice
    for Frame B.
    """
    unfolded = initial_position + initial_velocity * elapsed_time
    period = 2.0 * chamber_length
    folded = np.mod(unfolded, period)

    moving_right_branch = folded <= chamber_length
    position = np.where(
        moving_right_branch,
        folded,
        period - folded,
    )
    velocity = np.where(
        moving_right_branch,
        initial_velocity,
        -initial_velocity,
    )
    return position, velocity


def build_equivalent_piston_frame_slice(
    positions_a: np.ndarray,
    velocities_a: np.ndarray,
    chamber_length: float,
    boost_speed: float,
    preparation_time: float,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Frame A begins on t_A = -preparation_time.

    Frame B begins on the simultaneous hypersurface through the SAME piston
    event.  In B that hypersurface is t_B = -gamma * preparation_time.

    A point on that B slice obeys:

        t_A - beta*x_A = -preparation_time

    Write t_A = -preparation_time + s.  Then we solve:

        s = beta * x_A(s)

    along each particle's exact pre-compression billiard worldline.

    This avoids the invalid shortcut of taking A's t=const snapshot and simply
    length-contracting every particle at the same A time.
    """
    beta = boost_speed

    # Root is guaranteed inside [0, beta*L] because x is always in [0, L].
    lower = np.zeros_like(positions_a)
    upper = np.full_like(positions_a, beta * chamber_length)

    for _ in range(70):
        middle = 0.5 * (lower + upper)
        x_middle, _ = reflected_billiard_state(
            positions_a,
            velocities_a,
            middle,
            chamber_length,
        )
        residual = middle - beta * x_middle
        upper = np.where(residual >= 0.0, middle, upper)
        lower = np.where(residual < 0.0, middle, lower)

    elapsed = 0.5 * (lower + upper)
    event_position_a, event_velocity_a = reflected_billiard_state(
        positions_a,
        velocities_a,
        elapsed,
        chamber_length,
    )
    event_time_a = -preparation_time + elapsed

    event_time_b, event_position_b = transform_event(
        event_time_a,
        event_position_a,
        beta,
    )
    event_velocity_b = transform_velocity(event_velocity_a, beta)

    # Numerical diagnostic: every transformed event should be simultaneous.
    expected_time_b = -gamma_from_velocity(beta) * preparation_time
    max_time_error = float(np.max(np.abs(event_time_b - expected_time_b)))
    if max_time_error > 1e-10:
        raise RuntimeError(
            f"Failed to construct a simultaneous Frame-B slice; max error={max_time_error:.3e}"
        )

    return event_position_b, event_velocity_b, expected_time_b


# ---------------------------------------------------------------------------
# Prescribed boundary worldlines
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BoundaryState:
    position: float
    velocity: float


class BoundaryWorldlines:
    """Exact worldlines for the two boundaries in one coordinate frame."""

    def __init__(
        self,
        frame_name: str,
        chamber_length: float,
        piston_speed: float,
    ) -> None:
        self.frame_name = frame_name
        self.length = chamber_length
        self.beta = piston_speed
        self.gamma = gamma_from_velocity(piston_speed)

    def piston(self, time: float) -> BoundaryState:
        if self.frame_name == "WALL":
            if time < 0.0:
                return BoundaryState(position=0.0, velocity=0.0)
            return BoundaryState(position=self.beta * time, velocity=self.beta)

        if self.frame_name == "PISTON":
            if time < 0.0:
                return BoundaryState(position=-self.beta * time, velocity=-self.beta)
            return BoundaryState(position=0.0, velocity=0.0)

        raise ValueError(self.frame_name)

    def wall(self, time: float) -> BoundaryState:
        if self.frame_name == "WALL":
            return BoundaryState(position=self.length, velocity=0.0)

        if self.frame_name == "PISTON":
            return BoundaryState(
                position=(self.length / self.gamma) - self.beta * time,
                velocity=-self.beta,
            )

        raise ValueError(self.frame_name)

    def chamber_length(self, time: float) -> float:
        return self.wall(time).position - self.piston(time).position

    def compression_fraction_after_start(self, time: float) -> float:
        if time < 0.0:
            return 0.0

        initial_length = self.chamber_length(0.0)
        current_length = self.chamber_length(time)
        return 1.0 - current_length / initial_length


# ---------------------------------------------------------------------------
# Diagnostics and event records
# ---------------------------------------------------------------------------


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
    frame_native_temperature_like: float
    velocity_quantiles: np.ndarray
    momentum_quantiles: np.ndarray
    energy_quantiles: np.ndarray
    local_bin_density: np.ndarray
    local_bin_stress: np.ndarray


# ---------------------------------------------------------------------------
# Independent kinetic engine
# ---------------------------------------------------------------------------


class Engine:
    def __init__(
        self,
        *,
        frame_name: str,
        initial_time: float,
        particle_positions: np.ndarray,
        particle_velocities: np.ndarray,
        worldlines: BoundaryWorldlines,
        time_step: float,
    ) -> None:
        self.frame_name = frame_name
        self.time = float(initial_time)
        self.positions = np.array(particle_positions, dtype=float, copy=True)
        self.velocities = np.array(particle_velocities, dtype=float, copy=True)
        self.worldlines = worldlines
        self.time_step = time_step

        self.collision_events: List[CollisionEvent] = []

        self.interval = IntervalBookkeeping()

        # Bookkeeping: net energy/momentum delivered to gas by prescribed
        # boundaries.  With infinite-mass prescribed boundaries, these are the
        # quantities that replace finite piston/wall energy tracking.
        self.boundary_energy_to_gas = 0.0
        self.boundary_momentum_to_gas = 0.0


        self.initial_total_gas_energy = self.total_gas_energy()
        self.initial_total_gas_momentum = self.total_gas_momentum()

    # ---------------------------- basic state ----------------------------

    def particle_energies(self) -> np.ndarray:
        return np.asarray(energy_from_velocity(self.velocities))

    def particle_momenta(self) -> np.ndarray:
        return np.asarray(momentum_from_velocity(self.velocities))

    def total_gas_energy(self) -> float:
        return float(np.sum(energy_from_velocity(self.velocities)))

    def total_gas_momentum(self) -> float:
        return float(np.sum(momentum_from_velocity(self.velocities)))

    # ------------------------ local collision law ------------------------

    def _reflect_from_boundary(
        self,
        incoming_velocity: float,
        boundary_velocity: float,
    ) -> Tuple[float, float, float, float, float]:
        """
        Purely elastic reflection, calculated entirely inside THIS simulation.

        1. Transform the particle into the boundary's instantaneous rest frame.
        2. Reverse its momentum there.
        3. Transform the outgoing particle back to this simulation frame.

        No ignition, wall failure, escape, or extra energy source exists.
        """
        incoming_energy = float(energy_from_velocity(incoming_velocity))
        incoming_momentum = float(momentum_from_velocity(incoming_velocity))

        incoming_rest_energy = energy_in_rest_frame(
            incoming_energy,
            incoming_momentum,
            boundary_velocity,
        )
        incoming_rest_momentum = momentum_in_rest_frame(
            incoming_energy,
            incoming_momentum,
            boundary_velocity,
        )
        incoming_rest_ke = incoming_rest_energy - PARTICLE_MASS

        outgoing_rest_energy = incoming_rest_energy
        outgoing_rest_momentum = -incoming_rest_momentum

        outgoing_rest_velocity = velocity_from_energy_momentum(
            outgoing_rest_energy,
            outgoing_rest_momentum,
        )
        outgoing_velocity = inverse_transform_velocity(
            outgoing_rest_velocity,
            boundary_velocity,
        )

        outgoing_energy = float(energy_from_velocity(outgoing_velocity))
        outgoing_momentum = float(momentum_from_velocity(outgoing_velocity))
        rest_frame_impulse = incoming_rest_momentum - outgoing_rest_momentum

        self.boundary_energy_to_gas += outgoing_energy - incoming_energy
        self.boundary_momentum_to_gas += outgoing_momentum - incoming_momentum

        return (
            outgoing_velocity,
            incoming_rest_ke,
            rest_frame_impulse,
            incoming_energy,
            outgoing_energy,
        )

    # ------------------------------ stepping -----------------------------

    def _step_constant_boundary_velocities(self, dt: float) -> None:
        """Advance one short interval that does not cross the t=0 acceleration event."""
        if dt <= 0.0:
            return

        t0 = self.time
        piston0 = self.worldlines.piston(t0)
        wall0 = self.worldlines.wall(t0)

        # Wall proper time is relevant for the local-rest pressure diagnostic.
        self.interval.elapsed_coordinate_time += dt
        self.interval.end_wall_proper_time += dt / gamma_from_velocity(wall0.velocity)

        indices = np.arange(len(self.positions))
        x0 = self.positions[indices]
        v0 = self.velocities[indices]

        # Candidate collision times with linearly moving boundaries.
        left_tau = np.full(len(indices), np.inf)
        right_tau = np.full(len(indices), np.inf)

        closing_left = piston0.velocity - v0
        mask_left = closing_left > 1e-14
        left_tau[mask_left] = (
            x0[mask_left] - piston0.position
        ) / closing_left[mask_left]

        closing_right = v0 - wall0.velocity
        mask_right = closing_right > 1e-14
        right_tau[mask_right] = (
            wall0.position - x0[mask_right]
        ) / closing_right[mask_right]

        left_hit = (left_tau >= -1e-12) & (left_tau <= dt + 1e-12)
        right_hit = (right_tau >= -1e-12) & (right_tau <= dt + 1e-12)

        # If numerical roundoff says both happen, keep only the earlier one.
        both = left_hit & right_hit
        left_hit[both] = left_tau[both] <= right_tau[both]
        right_hit[both] = ~left_hit[both]

        # No collision: simple free flight.
        no_hit = ~(left_hit | right_hit)
        self.positions[indices[no_hit]] = x0[no_hit] + v0[no_hit] * dt

        # Handle piston collisions one by one.
        left_local_indices = np.flatnonzero(left_hit)
        if len(left_local_indices):
            order = left_local_indices[np.argsort(left_tau[left_local_indices])]
            for local_i in order:
                particle_i = indices[local_i]
                tau = float(max(0.0, left_tau[local_i]))
                collision_time = t0 + tau
                boundary_position = piston0.position + piston0.velocity * tau

                incoming_velocity = float(v0[local_i])
                incoming_momentum = float(momentum_from_velocity(incoming_velocity))

                (
                    outgoing_velocity,
                    incoming_rest_ke,
                    rest_impulse,
                    incoming_energy,
                    outgoing_energy,
                ) = self._reflect_from_boundary(
                    incoming_velocity,
                    piston0.velocity,
                )

                outgoing_momentum = float(momentum_from_velocity(outgoing_velocity))

                remaining = dt - tau
                self.positions[particle_i] = boundary_position + outgoing_velocity * remaining
                self.velocities[particle_i] = outgoing_velocity

                self.collision_events.append(
                    CollisionEvent(
                        boundary="piston",
                        time=collision_time,
                        position=boundary_position,
                        incoming_energy=incoming_energy,
                        incoming_momentum=incoming_momentum,
                        outgoing_energy=outgoing_energy,
                        outgoing_momentum=outgoing_momentum,
                        boundary_velocity=piston0.velocity,
                        incoming_rest_kinetic_energy=incoming_rest_ke,
                        rest_frame_impulse=rest_impulse,
                    )
                )

        # Handle end-wall collisions.
        right_local_indices = np.flatnonzero(right_hit)
        if len(right_local_indices):
            order = right_local_indices[np.argsort(right_tau[right_local_indices])]
            for local_i in order:
                particle_i = indices[local_i]
                tau = float(max(0.0, right_tau[local_i]))
                collision_time = t0 + tau
                boundary_position = wall0.position + wall0.velocity * tau

                incoming_velocity = float(v0[local_i])
                incoming_energy = float(energy_from_velocity(incoming_velocity))
                incoming_momentum = float(momentum_from_velocity(incoming_velocity))

                (
                    outgoing_velocity,
                    incoming_rest_ke,
                    rest_impulse,
                    reflected_incoming_energy,
                    outgoing_energy,
                ) = self._reflect_from_boundary(
                    incoming_velocity,
                    wall0.velocity,
                )

                outgoing_momentum = float(momentum_from_velocity(outgoing_velocity))
                frame_impulse_to_wall = incoming_momentum - outgoing_momentum

                self.interval.end_wall_frame_impulse += abs(frame_impulse_to_wall)
                self.interval.end_wall_rest_impulse += abs(rest_impulse)

                remaining = dt - tau
                self.positions[particle_i] = boundary_position + outgoing_velocity * remaining
                self.velocities[particle_i] = outgoing_velocity

                self.collision_events.append(
                    CollisionEvent(
                        boundary="wall",
                        time=collision_time,
                        position=boundary_position,
                        incoming_energy=reflected_incoming_energy,
                        incoming_momentum=incoming_momentum,
                        outgoing_energy=outgoing_energy,
                        outgoing_momentum=outgoing_momentum,
                        boundary_velocity=wall0.velocity,
                        incoming_rest_kinetic_energy=incoming_rest_ke,
                        rest_frame_impulse=rest_impulse,
                    )
                )

        self.time = t0 + dt

        # Numerical safety check.  Do not silently "fix" particles; fail if the
        # step became too large for the one-collision-per-step assumption.
        left = self.worldlines.piston(self.time).position
        right = self.worldlines.wall(self.time).position
        if np.min(self.positions) < left - 2e-6 or np.max(self.positions) > right + 2e-6:
            raise RuntimeError(
                f"{self.frame_name}: particle left numerical chamber bounds. "
                "Reduce time_step."
            )

    def run_until(self, target_time: float) -> None:
        if target_time < self.time:
            raise ValueError("Engine cannot run backward")

        while self.time < target_time - 1e-14:
            dt = min(self.time_step, target_time - self.time)

            # Never cross the piston acceleration event inside one step.
            if self.time < 0.0 < self.time + dt:
                dt = -self.time

            self._step_constant_boundary_velocities(dt)

    # ----------------------------- measuring -----------------------------

    def snapshot(self, spatial_bins: int = 10) -> Snapshot:
        piston = self.worldlines.piston(self.time)
        wall = self.worldlines.wall(self.time)
        length = wall.position - piston.position
        volume = length * AREA

        active_positions = self.positions
        active_velocities = self.velocities
        particle_count = len(active_positions)

        energies = np.asarray(energy_from_velocity(active_velocities))
        momenta = np.asarray(momentum_from_velocity(active_velocities))

        total_energy = float(np.sum(energies))
        total_momentum = float(np.sum(momenta))

        number_density = particle_count / volume
        energy_density = total_energy / volume
        average_stress = float(np.sum(momenta * active_velocities) / volume)

        # Bulk velocity defined by total gas 4-momentum in this snapshot.
        bulk_velocity = total_momentum / total_energy
        bulk_gamma = gamma_from_velocity(bulk_velocity)
        com_energies = bulk_gamma * (energies - bulk_velocity * momenta)
        random_ke_per_particle = float(np.mean(com_energies - PARTICLE_MASS))

        thermal_temperature_like = 2.0 * random_ke_per_particle
        frame_native_temperature_like = average_stress / number_density

        # Actual wall loading accumulated since the previous measurement.
        native_pressure = (
            self.interval.end_wall_frame_impulse
            / max(self.interval.elapsed_coordinate_time, 1e-30)
            / AREA
        )
        rest_pressure = (
            self.interval.end_wall_rest_impulse
            / max(self.interval.end_wall_proper_time, 1e-30)
            / AREA
        )

        # Local bin diagnostics on this frame's own simultaneous slice.
        bin_edges = np.linspace(piston.position, wall.position, spatial_bins + 1)
        bin_width = length / spatial_bins
        bin_volume = bin_width * AREA

        # Last edge inclusive.
        bin_index = np.searchsorted(bin_edges, active_positions, side="right") - 1
        bin_index = np.clip(bin_index, 0, spatial_bins - 1)

        counts = np.bincount(bin_index, minlength=spatial_bins)
        local_density = counts / bin_volume

        local_stress_numerator = np.bincount(
            bin_index,
            weights=momenta * active_velocities,
            minlength=spatial_bins,
        )
        local_stress = local_stress_numerator / bin_volume

        return Snapshot(
            frame_name=self.frame_name,
            time=self.time,
            compression_fraction=self.worldlines.compression_fraction_after_start(self.time),
            piston_position=piston.position,
            piston_velocity=piston.velocity,
            wall_position=wall.position,
            wall_velocity=wall.velocity,
            chamber_length=length,
            chamber_volume=volume,
            number_density=number_density,
            energy_density=energy_density,
            average_gas_stress=average_stress,
            end_wall_pressure_frame_native=native_pressure,
            end_wall_pressure_rest_frame=rest_pressure,
            mean_velocity=float(np.mean(active_velocities)),
            mean_momentum=float(np.mean(momenta)),
            mean_energy=float(np.mean(energies)),
            bulk_velocity_from_total_four_momentum=bulk_velocity,
            random_kinetic_energy_per_particle=random_ke_per_particle,
            internal_energy_estimate=random_ke_per_particle * particle_count,
            thermal_temperature_like_1d=thermal_temperature_like,
            frame_native_temperature_like=frame_native_temperature_like,
            velocity_quantiles=np.quantile(active_velocities, [0.05, 0.25, 0.50, 0.75, 0.95]),
            momentum_quantiles=np.quantile(momenta, [0.05, 0.25, 0.50, 0.75, 0.95]),
            energy_quantiles=np.quantile(energies, [0.05, 0.25, 0.50, 0.75, 0.95]),
            local_bin_density=local_density,
            local_bin_stress=local_stress,
        )

    def snapshot_and_reset_interval(self, spatial_bins: int = 10) -> Snapshot:
        result = self.snapshot(spatial_bins=spatial_bins)
        self.interval.reset()
        return result

    # --------------------------- conservation ----------------------------

    def conservation_report(self) -> Dict[str, float]:
        final_energy = self.total_gas_energy()
        final_momentum = self.total_gas_momentum()

        return {
            "initial_gas_energy": self.initial_total_gas_energy,
            "final_gas_energy": final_energy,
            "boundary_energy_to_gas": self.boundary_energy_to_gas,
            "energy_residual": (
                final_energy
                - self.initial_total_gas_energy
                - self.boundary_energy_to_gas
            ),
            "initial_gas_momentum": self.initial_total_gas_momentum,
            "final_gas_momentum": final_momentum,
            "boundary_momentum_to_gas": self.boundary_momentum_to_gas,
            "momentum_residual": (
                final_momentum
                - self.initial_total_gas_momentum
                - self.boundary_momentum_to_gas
            ),
        }


# ---------------------------------------------------------------------------
# Experiment setup / matching logic
# ---------------------------------------------------------------------------


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

    # Pure elastic compression: no irreversible thresholds are enabled.

    compression_stages: Tuple[float, ...] = (0.00, 0.25, 0.50, 0.75)
    spatial_bins: int = 10


def make_initial_wall_frame_gas(config: ExperimentConfig) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(config.random_seed)

    positions = rng.uniform(
        0.001,
        config.initial_chamber_length - 0.001,
        size=config.particle_count,
    )

    # Sample rapidity rather than velocity directly so |v|<1 automatically.
    rapidities = rng.normal(0.0, config.thermal_rapidity_sigma, size=config.particle_count)
    velocities = np.tanh(rapidities)

    # Remove the tiny finite-sample drift in Frame A's preparation state.
    # This is a physical preparation choice, not a runtime frame-fixing step.
    total_energy = float(np.sum(energy_from_velocity(velocities)))
    total_momentum = float(np.sum(momentum_from_velocity(velocities)))
    bulk_velocity = total_momentum / total_energy
    velocities = transform_velocity(velocities, bulk_velocity)

    return positions, velocities


def build_engines(config: ExperimentConfig) -> Tuple[Engine, Engine]:
    positions_a, velocities_a = make_initial_wall_frame_gas(config)

    initial_time_a = -config.preparation_time

    positions_b, velocities_b, initial_time_b = build_equivalent_piston_frame_slice(
        positions_a,
        velocities_a,
        config.initial_chamber_length,
        config.piston_speed,
        config.preparation_time,
    )

    wall_worldlines = BoundaryWorldlines(
        "WALL",
        config.initial_chamber_length,
        config.piston_speed,
    )
    piston_worldlines = BoundaryWorldlines(
        "PISTON",
        config.initial_chamber_length,
        config.piston_speed,
    )

    engine_a = Engine(
        frame_name="WALL",
        initial_time=initial_time_a,
        particle_positions=positions_a,
        particle_velocities=velocities_a,
        worldlines=wall_worldlines,
        time_step=config.time_step,
    )

    engine_b = Engine(
        frame_name="PISTON",
        initial_time=initial_time_b,
        particle_positions=positions_b,
        particle_velocities=velocities_b,
        worldlines=piston_worldlines,
        time_step=config.time_step,
    )

    return engine_a, engine_b


def target_time_for_compression_fraction(
    frame_name: str,
    fraction: float,
    chamber_length: float,
    piston_speed: float,
) -> float:
    """
    Match snapshots using the same event on the piston's worldline:
    "the piston has completed fraction X of its wall-frame journey."

    A piston event at x = fraction*L has:
        t_A = fraction*L / beta

    In the piston frame, that same piston event has:
        t_B = t_A / gamma
    """
    t_a = fraction * chamber_length / piston_speed
    if frame_name == "WALL":
        return t_a
    if frame_name == "PISTON":
        return t_a / gamma_from_velocity(piston_speed)
    raise ValueError(frame_name)


# ---------------------------------------------------------------------------
# Reporting / cross-frame diagnostics
# ---------------------------------------------------------------------------



def print_snapshot_pair(snapshot_a: Snapshot, snapshot_b: Snapshot) -> None:
    print(f"\nMATCHED PISTON EVENT: {100*snapshot_a.compression_fraction:5.1f}% journey")
    print("-" * 95)
    print(f"{'quantity':38s} {'WALL FRAME':>24s} {'PISTON FRAME':>24s}")
    print("-" * 95)

    rows = [
        ("simultaneous chamber length", snapshot_a.chamber_length, snapshot_b.chamber_length),
        ("number density n", snapshot_a.number_density, snapshot_b.number_density),
        ("gas stress / pressure P", snapshot_a.average_gas_stress, snapshot_b.average_gas_stress),
        ("NORMAL T = P / n", snapshot_a.frame_native_temperature_like, snapshot_b.frame_native_temperature_like),
        ("bulk-removed thermal estimate", snapshot_a.thermal_temperature_like_1d, snapshot_b.thermal_temperature_like_1d),
    ]

    for label, value_a, value_b in rows:
        print(f"{label:38s} {value_a:24.8f} {value_b:24.8f}")

    print(
        "  T=P/n uses each frame's own simultaneous stress and density directly; "
        "k_B = 1."
    )


def print_conservation(engine: Engine) -> None:
    report = engine.conservation_report()
    print(f"\n{engine.frame_name} FRAME CONSERVATION BOOKKEEPING")
    print("-" * 70)
    for key, value in report.items():
        print(f"{key:32s} {value: .12e}")


def run_experiment(config: ExperimentConfig) -> None:
    print("RELATIVISTIC PISTON TEMPERATURE TEST")
    print("=" * 95)
    print(f"particles                : {config.particle_count}")
    print(f"piston speed             : {config.piston_speed:.5f} c")
    print(f"gamma                    : {gamma_from_velocity(config.piston_speed):.8f}")
    print(f"wall-frame initial length: {config.initial_chamber_length:.5f}")
    print(
        f"piston-frame t=0 length  : "
        f"{config.initial_chamber_length/gamma_from_velocity(config.piston_speed):.5f}"
    )
    print(f"time step                : {config.time_step:.6f}")
    print()
    print("Physics mode: purely elastic piston compression only.")
    print("No wall rupture, ignition, escape, phase change, or other irreversible state is modeled.")

    engine_a, engine_b = build_engines(config)

    print("\nIndependent initial slices:")
    print(f"  Frame A starts at t_A = {engine_a.time:.8f}")
    print(f"  Frame B starts at t_B = {engine_b.time:.8f}")
    print(
        "  These slices are physically equivalent but not the same set of "
        "simultaneous events."
    )

    snapshots: List[Tuple[Snapshot, Snapshot]] = []

    for fraction in config.compression_stages:
        target_a = target_time_for_compression_fraction(
            "WALL",
            fraction,
            config.initial_chamber_length,
            config.piston_speed,
        )
        target_b = target_time_for_compression_fraction(
            "PISTON",
            fraction,
            config.initial_chamber_length,
            config.piston_speed,
        )

        engine_a.run_until(target_a)
        engine_b.run_until(target_b)

        snapshot_a = engine_a.snapshot_and_reset_interval(config.spatial_bins)
        snapshot_b = engine_b.snapshot_and_reset_interval(config.spatial_bins)
        snapshots.append((snapshot_a, snapshot_b))

        print_snapshot_pair(snapshot_a, snapshot_b)

    print_conservation(engine_a)
    print_conservation(engine_b)

    print("\nTEMPERATURE INTERPRETATION")
    print("=" * 95)
    print(
        "The row 'normal frame-native T = P/n' is the deliberately simple "
        "temperature-like calculation performed directly from EACH frame's own "
        "simultaneous gas stress P and number density n, with k_B = 1."
    )
    print(
        "The 'thermal estimate (bulk removed)' first removes the gas's common "
        "bulk motion using its total four-momentum, then converts mean random "
        "kinetic energy to the 1D nonrelativistic-style estimate T = 2<K_random>."
    )
    print(
        "Because this is a collisionless 1D toy gas, neither number should be "
        "treated as a complete relativistic thermodynamic temperature.  Their "
        "purpose here is to show exactly what each independent frame computes."
    )


if __name__ == "__main__":
    run_experiment(ExperimentConfig())

"""Independent collisionless kinetic engine."""

from __future__ import annotations

import numpy as np

from .boundaries import BoundaryWorldlines
from .constants import AREA, PARTICLE_MASS, SPECIFIC_GAS_CONSTANT
from .models import CollisionEvent, IntervalBookkeeping, Snapshot
from .relativity import (
    energy_from_velocity,
    energy_in_rest_frame,
    gamma_from_velocity,
    inverse_transform_velocity,
    momentum_from_velocity,
    momentum_in_rest_frame,
    velocity_from_energy_momentum,
)
from .thermodynamics import bulk_average_pressure, ideal_gas_temperature


class Engine:
    """Advance particles and prescribed boundaries in one coordinate frame."""

    def __init__(
        self,
        *,
        frame_name: str,
        initial_time: float,
        particle_positions: np.ndarray,
        particle_velocities: np.ndarray,
        worldlines: BoundaryWorldlines,
        time_step: float,
        cross_sectional_area: float = AREA,
        specific_gas_constant: float = SPECIFIC_GAS_CONSTANT,
    ) -> None:
        if cross_sectional_area <= 0.0:
            raise ValueError("Cross-sectional area must be positive")
        if specific_gas_constant <= 0.0:
            raise ValueError("Specific gas constant must be positive")
        self.frame_name = frame_name
        self.time = float(initial_time)
        self.positions = np.array(particle_positions, dtype=float, copy=True)
        self.velocities = np.array(particle_velocities, dtype=float, copy=True)
        self.worldlines = worldlines
        self.time_step = time_step
        self.cross_sectional_area = cross_sectional_area
        self.trapped_gas_mass = len(self.positions) * PARTICLE_MASS
        self.specific_gas_constant = specific_gas_constant
        self.collision_events: list[CollisionEvent] = []
        self.interval = IntervalBookkeeping()
        self.boundary_energy_to_gas = 0.0
        self.boundary_momentum_to_gas = 0.0
        self.initial_total_gas_energy = self.total_gas_energy()
        self.initial_total_gas_momentum = self.total_gas_momentum()

    def particle_energies(self) -> np.ndarray:
        return np.asarray(energy_from_velocity(self.velocities))

    def particle_momenta(self) -> np.ndarray:
        return np.asarray(momentum_from_velocity(self.velocities))

    def total_gas_energy(self) -> float:
        return float(np.sum(self.particle_energies()))

    def total_gas_momentum(self) -> float:
        return float(np.sum(self.particle_momenta()))

    def _reflect_from_boundary(
        self, incoming_velocity: float, boundary_velocity: float
    ) -> tuple[float, float, float, float, float]:
        incoming_energy = float(energy_from_velocity(incoming_velocity))
        incoming_momentum = float(momentum_from_velocity(incoming_velocity))
        rest_energy = energy_in_rest_frame(
            incoming_energy, incoming_momentum, boundary_velocity
        )
        rest_momentum = momentum_in_rest_frame(
            incoming_energy, incoming_momentum, boundary_velocity
        )
        rest_ke = rest_energy - PARTICLE_MASS
        outgoing_velocity = inverse_transform_velocity(
            velocity_from_energy_momentum(rest_energy, -rest_momentum),
            boundary_velocity,
        )
        outgoing_energy = float(energy_from_velocity(outgoing_velocity))
        outgoing_momentum = float(momentum_from_velocity(outgoing_velocity))
        rest_impulse = 2.0 * rest_momentum
        self.boundary_energy_to_gas += outgoing_energy - incoming_energy
        self.boundary_momentum_to_gas += outgoing_momentum - incoming_momentum
        return (
            outgoing_velocity,
            rest_ke,
            rest_impulse,
            incoming_energy,
            outgoing_energy,
        )

    def _record_collision(
        self,
        boundary: str,
        collision_time: float,
        position: float,
        incoming_velocity: float,
        boundary_velocity: float,
    ) -> float:
        incoming_momentum = float(momentum_from_velocity(incoming_velocity))
        (
            outgoing_velocity,
            incoming_rest_ke,
            rest_impulse,
            incoming_energy,
            outgoing_energy,
        ) = self._reflect_from_boundary(incoming_velocity, boundary_velocity)
        outgoing_momentum = float(momentum_from_velocity(outgoing_velocity))
        if boundary == "wall":
            self.interval.end_wall_frame_impulse += abs(
                incoming_momentum - outgoing_momentum
            )
            self.interval.end_wall_rest_impulse += abs(rest_impulse)
        self.collision_events.append(
            CollisionEvent(
                boundary=boundary,
                time=collision_time,
                position=position,
                incoming_energy=incoming_energy,
                incoming_momentum=incoming_momentum,
                outgoing_energy=outgoing_energy,
                outgoing_momentum=outgoing_momentum,
                boundary_velocity=boundary_velocity,
                incoming_rest_kinetic_energy=incoming_rest_ke,
                rest_frame_impulse=rest_impulse,
            )
        )
        return outgoing_velocity

    def _step_constant_boundary_velocities(self, dt: float) -> None:
        if dt <= 0:
            return
        t0 = self.time
        piston = self.worldlines.piston(t0)
        wall = self.worldlines.wall(t0)
        self.interval.elapsed_coordinate_time += dt
        self.interval.end_wall_proper_time += dt / gamma_from_velocity(wall.velocity)

        indices = np.arange(len(self.positions))
        positions = self.positions.copy()
        velocities = self.velocities.copy()
        left_tau = np.full(len(indices), np.inf)
        right_tau = np.full(len(indices), np.inf)
        closing_left = piston.velocity - velocities
        mask = closing_left > 1e-14
        left_tau[mask] = (positions[mask] - piston.position) / closing_left[mask]
        closing_right = velocities - wall.velocity
        mask = closing_right > 1e-14
        right_tau[mask] = (wall.position - positions[mask]) / closing_right[mask]
        left_hit = (left_tau >= -1e-12) & (left_tau <= dt + 1e-12)
        right_hit = (right_tau >= -1e-12) & (right_tau <= dt + 1e-12)
        both = left_hit & right_hit
        left_hit[both] = left_tau[both] <= right_tau[both]
        right_hit[both] = ~left_hit[both]
        no_hit = ~(left_hit | right_hit)
        self.positions[indices[no_hit]] = positions[no_hit] + velocities[no_hit] * dt

        for local_i in np.flatnonzero(left_hit)[np.argsort(left_tau[left_hit])]:
            particle_i = indices[local_i]
            tau = float(max(0.0, left_tau[local_i]))
            outgoing = self._record_collision(
                "piston",
                t0 + tau,
                piston.position + piston.velocity * tau,
                float(velocities[local_i]),
                piston.velocity,
            )
            self.positions[particle_i] = (
                piston.position + piston.velocity * tau + outgoing * (dt - tau)
            )
            self.velocities[particle_i] = outgoing

        for local_i in np.flatnonzero(right_hit)[np.argsort(right_tau[right_hit])]:
            particle_i = indices[local_i]
            tau = float(max(0.0, right_tau[local_i]))
            outgoing = self._record_collision(
                "wall",
                t0 + tau,
                wall.position + wall.velocity * tau,
                float(velocities[local_i]),
                wall.velocity,
            )
            self.positions[particle_i] = (
                wall.position + wall.velocity * tau + outgoing * (dt - tau)
            )
            self.velocities[particle_i] = outgoing

        self.time = t0 + dt
        left = self.worldlines.piston(self.time).position
        right = self.worldlines.wall(self.time).position
        if (
            np.min(self.positions) < left - 2e-6
            or np.max(self.positions) > right + 2e-6
        ):
            raise RuntimeError(
                f"{self.frame_name}: particle left numerical chamber bounds. Reduce time_step."
            )

    def run_until(self, target_time: float) -> None:
        if target_time < self.time:
            raise ValueError("Engine cannot run backward")
        while self.time < target_time - 1e-14:
            dt = min(self.time_step, target_time - self.time)
            if self.time < 0 < self.time + dt:
                dt = -self.time
            self._step_constant_boundary_velocities(dt)

    def snapshot(self, spatial_bins: int = 10) -> Snapshot:
        piston = self.worldlines.piston(self.time)
        wall = self.worldlines.wall(self.time)
        length = wall.position - piston.position
        volume = length * self.cross_sectional_area
        energies = self.particle_energies()
        momenta = self.particle_momenta()
        count = len(self.positions)
        total_energy = float(np.sum(energies))
        total_momentum = float(np.sum(momenta))
        density = count / volume
        pressure = bulk_average_pressure(momenta, self.velocities, volume)
        bulk_velocity = total_momentum / total_energy
        bulk_gamma = gamma_from_velocity(bulk_velocity)
        random_ke = float(
            np.mean(bulk_gamma * (energies - bulk_velocity * momenta) - PARTICLE_MASS)
        )
        edges = np.linspace(piston.position, wall.position, spatial_bins + 1)
        bin_index = np.clip(
            np.searchsorted(edges, self.positions, side="right") - 1,
            0,
            spatial_bins - 1,
        )
        bin_volume = length / spatial_bins * self.cross_sectional_area
        counts = np.bincount(bin_index, minlength=spatial_bins)
        local_stress = (
            np.bincount(
                bin_index, weights=momenta * self.velocities, minlength=spatial_bins
            )
            / bin_volume
        )
        elapsed = max(self.interval.elapsed_coordinate_time, 1e-30)
        proper = max(self.interval.end_wall_proper_time, 1e-30)
        quantiles = [0.05, 0.25, 0.50, 0.75, 0.95]
        return Snapshot(
            frame_name=self.frame_name,
            time=self.time,
            compression_fraction=self.worldlines.compression_fraction_after_start(
                self.time
            ),
            piston_position=piston.position,
            piston_velocity=piston.velocity,
            wall_position=wall.position,
            wall_velocity=wall.velocity,
            chamber_length=length,
            chamber_volume=volume,
            trapped_gas_mass=self.trapped_gas_mass,
            specific_gas_constant=self.specific_gas_constant,
            number_density=density,
            energy_density=total_energy / volume,
            average_gas_stress=pressure,
            end_wall_pressure_frame_native=self.interval.end_wall_frame_impulse
            / elapsed
            / self.cross_sectional_area,
            end_wall_pressure_rest_frame=self.interval.end_wall_rest_impulse
            / proper
            / self.cross_sectional_area,
            mean_velocity=float(np.mean(self.velocities)),
            mean_momentum=float(np.mean(momenta)),
            mean_energy=float(np.mean(energies)),
            bulk_velocity_from_total_four_momentum=bulk_velocity,
            random_kinetic_energy_per_particle=random_ke,
            internal_energy_estimate=random_ke * count,
            thermal_temperature_like_1d=2.0 * random_ke,
            ideal_gas_temperature=ideal_gas_temperature(
                pressure,
                volume,
                self.trapped_gas_mass,
                self.specific_gas_constant,
            ),
            velocity_quantiles=np.quantile(self.velocities, quantiles),
            momentum_quantiles=np.quantile(momenta, quantiles),
            energy_quantiles=np.quantile(energies, quantiles),
            local_bin_density=counts / bin_volume,
            local_bin_stress=local_stress,
        )

    def snapshot_and_reset_interval(self, spatial_bins: int = 10) -> Snapshot:
        result = self.snapshot(spatial_bins)
        self.interval.reset()
        return result

    def conservation_report(self) -> dict[str, float]:
        final_energy = self.total_gas_energy()
        final_momentum = self.total_gas_momentum()
        return {
            "initial_gas_energy": self.initial_total_gas_energy,
            "final_gas_energy": final_energy,
            "boundary_energy_to_gas": self.boundary_energy_to_gas,
            "energy_residual": final_energy
            - self.initial_total_gas_energy
            - self.boundary_energy_to_gas,
            "initial_gas_momentum": self.initial_total_gas_momentum,
            "final_gas_momentum": final_momentum,
            "boundary_momentum_to_gas": self.boundary_momentum_to_gas,
            "momentum_residual": final_momentum
            - self.initial_total_gas_momentum
            - self.boundary_momentum_to_gas,
        }

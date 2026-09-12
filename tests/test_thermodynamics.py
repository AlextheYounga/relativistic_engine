import unittest

import numpy as np

from relativistic_engine.boundaries import BoundaryWorldlines
from relativistic_engine.engine import Engine
from relativistic_engine.relativity import (
    gamma_from_velocity,
    momentum_from_velocity,
    transform_velocity,
)
from relativistic_engine.thermodynamics import (
    apparent_bulk_temperature,
    bulk_average_pressure,
)


class ApparentBulkTemperatureTests(unittest.TestCase):
    def test_uses_pressure_volume_particle_count_and_boltzmann_constant(self) -> None:
        pressure = 12.0
        volume = 5.0

        temperature = apparent_bulk_temperature(
            pressure,
            volume,
            particle_count=10,
            boltzmann_constant=2.0,
        )

        self.assertEqual(temperature, 3.0)

    def test_bulk_motion_raises_longitudinal_apparent_temperature(self) -> None:
        rest_velocities = np.array([-0.1, 0.1])
        rest_volume = 10.0
        rest_pressure = bulk_average_pressure(
            np.asarray(momentum_from_velocity(rest_velocities)),
            rest_velocities,
            rest_volume,
        )
        rest_temperature = apparent_bulk_temperature(
            rest_pressure, rest_volume, len(rest_velocities)
        )

        frame_speed = 0.8
        observed_velocities = np.asarray(
            transform_velocity(rest_velocities, frame_speed)
        )
        observed_volume = rest_volume / gamma_from_velocity(frame_speed)
        observed_pressure = bulk_average_pressure(
            np.asarray(momentum_from_velocity(observed_velocities)),
            observed_velocities,
            observed_volume,
        )
        observed_temperature = apparent_bulk_temperature(
            observed_pressure, observed_volume, len(observed_velocities)
        )

        self.assertGreater(observed_temperature, rest_temperature)

    def test_engine_snapshot_reports_apparent_bulk_temperature(self) -> None:
        velocities = np.array([-0.2, 0.2])
        engine = Engine(
            frame_name="WALL",
            initial_time=-1.0,
            particle_positions=np.array([2.0, 8.0]),
            particle_velocities=velocities,
            worldlines=BoundaryWorldlines("WALL", 10.0, 0.8),
            time_step=0.01,
            cross_sectional_area=2.0,
            boltzmann_constant=4.0,
        )

        snapshot = engine.snapshot(spatial_bins=2)

        expected_pressure = float(
            np.sum(momentum_from_velocity(velocities) * velocities)
            / snapshot.chamber_volume
        )
        expected_temperature = (
            expected_pressure * snapshot.chamber_volume / (len(velocities) * 4.0)
        )
        self.assertEqual(snapshot.chamber_volume, 20.0)
        self.assertAlmostEqual(snapshot.average_gas_stress, expected_pressure)
        self.assertAlmostEqual(snapshot.apparent_bulk_temperature, expected_temperature)


if __name__ == "__main__":
    unittest.main()

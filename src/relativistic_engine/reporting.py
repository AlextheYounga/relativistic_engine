"""Compact text reports for experiment results."""

from .engine import Engine
from .models import Snapshot
from .thermodynamics import TemperatureCalibration


def print_measurement_header(
    trapped_gas_mass: float,
    specific_gas_constant: float,
    temperature_calibration: TemperatureCalibration,
) -> None:
    """Print the invariant inputs and columns used for all stage readings."""
    print("\nTEMPERATURE: T = P * V / (m * R)")
    print(f"m = {trapped_gas_mass:.3f}    R = {specific_gas_constant:.3f}")
    print(
        "Fahrenheit calibration: initial WALL temperature = "
        f"{temperature_calibration.reference_fahrenheit:.2f} deg F"
    )
    print()
    print(
        f"{'STAGE':>7}  {'FRAME':<7}  {'TIME':>10}  "
        f"{'VOLUME':>12}  {'PRESSURE':>14}  {'TEMP (deg F)':>14}"
    )
    print("-" * 86)


def print_snapshot_pair(
    snapshot_a: Snapshot,
    snapshot_b: Snapshot,
    temperature_calibration: TemperatureCalibration,
) -> None:
    """Print one row per frame for a matched piston event."""
    stage = f"{100 * snapshot_a.compression_fraction:.1f}%"
    _print_snapshot(stage, snapshot_a, temperature_calibration)
    _print_snapshot("", snapshot_b, temperature_calibration)


def _print_snapshot(
    stage: str,
    snapshot: Snapshot,
    temperature_calibration: TemperatureCalibration,
) -> None:
    print(
        f"{stage:>7}  {snapshot.frame_name:<7}  {snapshot.time:10.5f}  "
        f"{snapshot.chamber_volume:12.5f}  "
        f"{snapshot.average_gas_stress:14.6f}  "
        f"{temperature_calibration.to_fahrenheit(snapshot.ideal_gas_temperature):14,.2f}"
    )


def print_conservation(engine_a: Engine, engine_b: Engine) -> None:
    """Print the conservation totals from both independently evolved frames."""
    report_a = engine_a.conservation_report()
    report_b = engine_b.conservation_report()
    rows = [
        (
            "gas energy change",
            report_a["final_gas_energy"] - report_a["initial_gas_energy"],
            report_b["final_gas_energy"] - report_b["initial_gas_energy"],
        ),
        (
            "boundary energy supplied",
            report_a["boundary_energy_to_gas"],
            report_b["boundary_energy_to_gas"],
        ),
        ("energy residual", report_a["energy_residual"], report_b["energy_residual"]),
        (
            "gas momentum change",
            report_a["final_gas_momentum"] - report_a["initial_gas_momentum"],
            report_b["final_gas_momentum"] - report_b["initial_gas_momentum"],
        ),
        (
            "boundary momentum supplied",
            report_a["boundary_momentum_to_gas"],
            report_b["boundary_momentum_to_gas"],
        ),
        (
            "momentum residual",
            report_a["momentum_residual"],
            report_b["momentum_residual"],
        ),
    ]

    print("\nCONSERVATION")
    print(f"{'QUANTITY':<28}  {'WALL':>18}  {'PISTON':>18}")
    print("-" * 68)
    for label, value_a, value_b in rows:
        print(f"{label:<28}  {value_a:18.8e}  {value_b:18.8e}")

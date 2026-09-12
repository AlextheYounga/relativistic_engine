"""Text reports for experiment results."""

from .engine import Engine
from .models import Snapshot


def print_snapshot_pair(snapshot_a: Snapshot, snapshot_b: Snapshot) -> None:
    print(
        f"\nMATCHED PISTON EVENT: {100 * snapshot_a.compression_fraction:5.1f}% journey"
    )
    print("-" * 95)
    print(f"{'quantity':38s} {'WALL FRAME':>24s} {'PISTON FRAME':>24s}")
    print("-" * 95)
    rows = [
        (
            "simultaneous chamber length",
            snapshot_a.chamber_length,
            snapshot_b.chamber_length,
        ),
        (
            "chamber volume V",
            snapshot_a.chamber_volume,
            snapshot_b.chamber_volume,
        ),
        ("number density n", snapshot_a.number_density, snapshot_b.number_density),
        (
            "bulk-average pressure P",
            snapshot_a.average_gas_stress,
            snapshot_b.average_gas_stress,
        ),
        (
            "trapped gas mass m",
            snapshot_a.trapped_gas_mass,
            snapshot_b.trapped_gas_mass,
        ),
        (
            "specific gas constant R",
            snapshot_a.specific_gas_constant,
            snapshot_b.specific_gas_constant,
        ),
        (
            "ideal-gas thermometer T = PV/(mR)",
            snapshot_a.ideal_gas_temperature,
            snapshot_b.ideal_gas_temperature,
        ),
    ]
    for label, value_a, value_b in rows:
        print(f"{label:38s} {value_a:24.8f} {value_b:24.8f}")
    print("  Each frame inserts its own pressure and volume into T = PV/(mR).")


def print_conservation(engine: Engine) -> None:
    print(f"\n{engine.frame_name} FRAME CONSERVATION BOOKKEEPING\n" + "-" * 70)
    for key, value in engine.conservation_report().items():
        print(f"{key:32s} {value: .12e}")

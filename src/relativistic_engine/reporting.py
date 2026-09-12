"""Text reports for experiment results."""

from .engine import Engine
from .models import Snapshot


def print_snapshot_pair(snapshot_a: Snapshot, snapshot_b: Snapshot) -> None:
    print(f"\nMATCHED PISTON EVENT: {100 * snapshot_a.compression_fraction:5.1f}% journey")
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
    print("  T=P/n uses each frame's own simultaneous stress and density directly; k_B = 1.")


def print_conservation(engine: Engine) -> None:
    print(f"\n{engine.frame_name} FRAME CONSERVATION BOOKKEEPING\n" + "-" * 70)
    for key, value in engine.conservation_report().items():
        print(f"{key:32s} {value: .12e}")

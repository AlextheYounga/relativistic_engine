"""Compatibility entry point for the packaged implementation."""

from src.relativistic_engine import *
from src.relativistic_engine.experiment import ExperimentConfig, run_experiment


if __name__ == "__main__":
    run_experiment(ExperimentConfig())

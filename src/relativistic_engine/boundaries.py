"""Prescribed piston and end-wall worldlines."""

from dataclasses import dataclass

from .relativity import gamma_from_velocity


@dataclass(frozen=True)
class BoundaryState:
    position: float
    velocity: float


class BoundaryWorldlines:
    """Exact worldlines for both boundaries in one coordinate frame."""

    def __init__(self, frame_name: str, chamber_length: float, piston_speed: float) -> None:
        self.frame_name = frame_name
        self.length = chamber_length
        self.beta = piston_speed
        self.gamma = gamma_from_velocity(piston_speed)

    def piston(self, time: float) -> BoundaryState:
        if self.frame_name == "WALL":
            return BoundaryState(0.0, 0.0) if time < 0 else BoundaryState(self.beta * time, self.beta)
        if self.frame_name == "PISTON":
            return BoundaryState(-self.beta * time, -self.beta) if time < 0 else BoundaryState(0.0, 0.0)
        raise ValueError(self.frame_name)

    def wall(self, time: float) -> BoundaryState:
        if self.frame_name == "WALL":
            return BoundaryState(self.length, 0.0)
        if self.frame_name == "PISTON":
            return BoundaryState(self.length / self.gamma - self.beta * time, -self.beta)
        raise ValueError(self.frame_name)

    def chamber_length(self, time: float) -> float:
        return self.wall(time).position - self.piston(time).position

    def compression_fraction_after_start(self, time: float) -> float:
        if time < 0:
            return 0.0
        initial = self.chamber_length(0.0)
        return 1.0 - self.chamber_length(time) / initial

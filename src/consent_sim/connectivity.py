
from dataclasses import dataclass


@dataclass(frozen=True)
class Outage:
    """A network outage during [start, end)."""

    start: float
    end: float

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError("Outage end must be after start")

    def contains(self, at_time: float) -> bool:
        return self.start <= at_time < self.end


class ConnectivitySchedule:
    """Deterministic network connectivity simulation."""

    def __init__(self, outages=None):
        self.outages = list(outages or [])

    def is_online(self, at_time: float) -> bool:
        return not any(
            outage.contains(at_time)
            for outage in self.outages
        )

    def add_outage(self, start: float, end: float) -> None:
        self.outages.append(Outage(start, end))


import random

from .connectivity import ConnectivitySchedule, Outage


def generate_random_outages(
    seed: int,
    horizon: float,
    outage_count: int,
    outage_duration: float,
) -> ConnectivitySchedule:
    """Generate reproducible, non-overlapping network outages."""

    if horizon <= 0:
        raise ValueError("Horizon must be positive")

    if outage_count < 0:
        raise ValueError("Outage count cannot be negative")

    if outage_duration < 0:
        raise ValueError("Outage duration cannot be negative")

    if outage_count * outage_duration > horizon:
        raise ValueError("Outages cannot fit within the horizon")

    if outage_count == 0 or outage_duration == 0:
        return ConnectivitySchedule()

    rng = random.Random(seed)

    # Randomly allocate the unused timeline as gaps.
    free_time = horizon - outage_count * outage_duration

    cuts = sorted(
        [0.0, free_time]
        + [rng.uniform(0, free_time) for _ in range(outage_count)]
    )

    gaps = [
        cuts[i + 1] - cuts[i]
        for i in range(len(cuts) - 1)
    ]

    outages = []
    cursor = gaps[0]

    for i in range(outage_count):
        start = cursor
        end = start + outage_duration

        outages.append(Outage(start, end))

        cursor = end + gaps[i + 1]

    return ConnectivitySchedule(outages)

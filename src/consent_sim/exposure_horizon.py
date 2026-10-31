
from dataclasses import dataclass

from .connectivity import ConnectivitySchedule
from .exposure import SubjectExposure, calculate_strategy_exposure
from .runner import ExperimentTrace
from .simulator import Strategy
from .workload import Workload


@dataclass(frozen=True)
class HorizonExposureSummary:
    strategy: Strategy
    observation_end: float
    subject_exposures: tuple[SubjectExposure, ...]


def calculate_horizon_exposure(
    workload: Workload,
    trace: ExperimentTrace,
    connectivity: ConnectivitySchedule,
    strategy: Strategy,
    observation_end: float,
) -> HorizonExposureSummary:
    """Clip potential exposure intervals to the observation horizon."""

    if observation_end <= 0:
        raise ValueError("Observation horizon must be positive")

    exposures = calculate_strategy_exposure(
        workload,
        trace,
        connectivity,
        strategy,
    )

    clipped_exposures = []

    for exposure in exposures:
        intervals = []

        for start, end in exposure.exposure_intervals:
            clipped_start = max(
                start,
                exposure.revoked_at,
            )
            clipped_end = min(
                end,
                observation_end,
            )

            if clipped_start < clipped_end:
                intervals.append(
                    (clipped_start, clipped_end)
                )

        total = sum(
            end - start
            for start, end in intervals
        )

        clipped_exposures.append(
            SubjectExposure(
                subject_id=exposure.subject_id,
                revoked_at=exposure.revoked_at,
                total_exposure_seconds=total,
                exposure_intervals=tuple(intervals),
            )
        )

    return HorizonExposureSummary(
        strategy=strategy,
        observation_end=observation_end,
        subject_exposures=tuple(clipped_exposures),
    )


from dataclasses import dataclass

from .exposure_horizon import HorizonExposureSummary
from .simulator import SimulationResult


@dataclass(frozen=True)
class ExposureValidation:
    checked_requests: int
    unauthorized_approvals: int
    matched_approvals: int
    mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return len(self.mismatches) == 0


def validate_exposure_consistency(
    results: list[SimulationResult],
    exposure_summary: HorizonExposureSummary,
    request_subjects: dict[str, str],
) -> ExposureValidation:
    """
    Check whether unauthorized approvals fall within
    calculated post-revocation exposure intervals.

    This is a one-way consistency check:
    every unauthorized approval must lie inside an exposure
    interval. It does not establish that every exposure
    interval necessarily contains a request.
    """

    exposure_by_subject = {
        exposure.subject_id: exposure
        for exposure in exposure_summary.subject_exposures
    }

    checked = 0
    unauthorized = 0
    matched = 0
    mismatches = []

    for result in results:
        if not result.unauthorized_approval:
            continue

        unauthorized += 1
        checked += 1

        subject_id = request_subjects.get(result.request_id)

        if subject_id is None:
            mismatches.append(
                f"{result.request_id}: missing subject mapping"
            )
            continue

        exposure = exposure_by_subject.get(subject_id)

        if exposure is None:
            mismatches.append(
                f"{result.request_id}: missing exposure record"
            )
            continue

        inside_exposure = any(
            start <= result.generation_time < end
            for start, end in exposure.exposure_intervals
        )

        if inside_exposure:
            matched += 1
        else:
            mismatches.append(
                f"{result.request_id}: unauthorized approval "
                f"outside exposure interval"
            )

    return ExposureValidation(
        checked_requests=checked,
        unauthorized_approvals=unauthorized,
        matched_approvals=matched,
        mismatches=tuple(mismatches),
    )


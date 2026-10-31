
from dataclasses import dataclass

from .connectivity import ConnectivitySchedule


@dataclass(frozen=True)
class ExposureWindow:
    revocation_time: float
    exposure_end: float
    duration: float


def calculate_exposure_window(
    revocation_time: float,
    authorization_expiry: float,
    connectivity: ConnectivitySchedule,
) -> ExposureWindow:
    """
    Calculate the potential stale-authorization exposure
    window after consent revocation.

    Assumes:
    - Online requests revalidate consent immediately.
    - Offline requests can use cached authorization.
    - Authorization expires at authorization_expiry.
    """

    if authorization_expiry < revocation_time:
        return ExposureWindow(
            revocation_time=revocation_time,
            exposure_end=revocation_time,
            duration=0.0,
        )

    if connectivity.is_online(revocation_time):
        return ExposureWindow(
            revocation_time=revocation_time,
            exposure_end=revocation_time,
            duration=0.0,
        )

    exposure_end = authorization_expiry

    for outage in connectivity.outages:
        if outage.contains(revocation_time):
            exposure_end = min(
                exposure_end,
                outage.end,
            )
            break

    return ExposureWindow(
        revocation_time=revocation_time,
        exposure_end=exposure_end,
        duration=max(
            0.0,
            exposure_end - revocation_time,
        ),
    )

@dataclass(frozen=True)
class CumulativeExposure:
    revocation_time: float
    authorization_expiry: float
    total_exposure_seconds: float
    exposure_intervals: tuple[tuple[float, float], ...]


def calculate_cumulative_exposure(
    revocation_time: float,
    authorization_expiry: float,
    connectivity: ConnectivitySchedule,
) -> CumulativeExposure:
    """
    Calculate total potential offline exposure after revocation.

    Assumptions:
    - Online requests always revalidate current consent.
    - Offline requests may use an unexpired cached lease.
    - Cached authorization is not permanently invalidated
      merely because connectivity temporarily returns.
    - Outages are treated as half-open intervals [start, end).
    """

    if authorization_expiry <= revocation_time:
        return CumulativeExposure(
            revocation_time=revocation_time,
            authorization_expiry=authorization_expiry,
            total_exposure_seconds=0.0,
            exposure_intervals=(),
        )

    overlapping = []

    for outage in connectivity.outages:
        start = max(revocation_time, outage.start)
        end = min(authorization_expiry, outage.end)

        if start < end:
            overlapping.append((start, end))

    overlapping.sort()

    merged = []

    for start, end in overlapping:
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged.append((start, end))

    total = sum(
        end - start
        for start, end in merged
    )

    return CumulativeExposure(
        revocation_time=revocation_time,
        authorization_expiry=authorization_expiry,
        total_exposure_seconds=total,
        exposure_intervals=tuple(merged),
    )

from .runner import ExperimentTrace
from .workload import Workload


@dataclass(frozen=True)
class SubjectExposure:
    subject_id: str
    revoked_at: float
    total_exposure_seconds: float
    exposure_intervals: tuple[tuple[float, float], ...]


def calculate_trace_exposure(
    workload: Workload,
    trace: ExperimentTrace,
    connectivity: ConnectivitySchedule,
) -> list[SubjectExposure]:
    """
    Calculate potential offline exposure using actual lease
    issuance records and revocation events.

    Assumes each subject has one requester-purpose pair.
    """

    exposures = []

    for revocation in workload.revocations:
        subject_leases = [
            lease
            for lease in trace.lease_issuances
            if lease.subject_id == revocation.subject_id
            and lease.requester_id == revocation.requester_id
            and lease.purpose == revocation.purpose
            and lease.issued_at <= revocation.at_time
        ]

        intervals = []

        for lease in subject_leases:
            exposure = calculate_cumulative_exposure(
                revocation_time=revocation.at_time,
                authorization_expiry=lease.expires_at,
                connectivity=connectivity,
            )

            intervals.extend(exposure.exposure_intervals)

        intervals.sort()

        merged = []

        for start, end in intervals:
            if merged and start <= merged[-1][1]:
                previous_start, previous_end = merged[-1]
                merged[-1] = (
                    previous_start,
                    max(previous_end, end),
                )
            else:
                merged.append((start, end))

        total = sum(
            end - start
            for start, end in merged
        )

        exposures.append(
            SubjectExposure(
                subject_id=revocation.subject_id,
                revoked_at=revocation.at_time,
                total_exposure_seconds=total,
                exposure_intervals=tuple(merged),
            )
        )

    return exposures

from .simulator import Strategy


def calculate_strategy_exposure(
    workload: Workload,
    trace: ExperimentTrace,
    connectivity: ConnectivitySchedule,
    strategy: Strategy,
) -> list[SubjectExposure]:
    """
    Calculate potential post-revocation exposure by strategy.

    ONE_TIME:
        Cached authorization is accepted online and offline.

    FAIL_CLOSED:
        Online registry checks block revoked consent.
        Offline requests are denied.

    SHORT_LEASE:
        Online registry checks block revoked consent.
        Offline requests may use an unexpired cached lease.
    """

    if strategy == Strategy.SHORT_LEASE:
        return calculate_trace_exposure(
            workload,
            trace,
            connectivity,
        )

    exposures = []

    for revocation in workload.revocations:
        subject_leases = [
            lease
            for lease in trace.lease_issuances
            if lease.subject_id == revocation.subject_id
            and lease.requester_id == revocation.requester_id
            and lease.purpose == revocation.purpose
            and lease.issued_at <= revocation.at_time
        ]

        if strategy == Strategy.FAIL_CLOSED:
            intervals = ()

        elif strategy == Strategy.ONE_TIME:
            intervals = tuple(
                (revocation.at_time, lease.expires_at)
                for lease in subject_leases
                if lease.expires_at > revocation.at_time
            )

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Merge overlapping authorization intervals.
        merged = []

        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                previous_start, previous_end = merged[-1]
                merged[-1] = (
                    previous_start,
                    max(previous_end, end),
                )
            else:
                merged.append((start, end))

        total = sum(
            end - start
            for start, end in merged
        )

        exposures.append(
            SubjectExposure(
                subject_id=revocation.subject_id,
                revoked_at=revocation.at_time,
                total_exposure_seconds=total,
                exposure_intervals=tuple(merged),
            )
        )

    return exposures

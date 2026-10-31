
from dataclasses import dataclass

from .authorization import AuthorizationService
from .connectivity import ConnectivitySchedule
from .models import AuthorizationLease, GenerationRequest
from .registry import ConsentRegistry
from .simulator import ConsentSimulator, SimulationResult, Strategy
from .workload import Workload


@dataclass(frozen=True)
class ExperimentConfig:
    lease_duration: float = 60.0
    one_time_duration: float = 1000.0


@dataclass(frozen=True)
class LeaseIssuanceRecord:
    subject_id: str
    requester_id: str
    purpose: str
    issued_at: float
    expires_at: float


@dataclass(frozen=True)
class ExperimentTrace:
    results: list[SimulationResult]
    lease_issuances: list[LeaseIssuanceRecord]


def run_experiment_with_trace(
    workload: Workload,
    connectivity: ConnectivitySchedule,
    strategy: Strategy,
    config: ExperimentConfig,
) -> ExperimentTrace:
    """Run a chronological authorization experiment with a lease trace."""

    if config.lease_duration <= 0:
        raise ValueError("Lease duration must be positive")

    if config.one_time_duration <= 0:
        raise ValueError("One-time duration must be positive")

    registry = ConsentRegistry()
    authorization = AuthorizationService(registry)
    simulator = ConsentSimulator(authorization, connectivity)

    requester_id = "requester_1"
    purpose = "FACE_SWAP"

    # Initialize consent for every subject.
    for subject_id in workload.subject_ids:
        registry.grant(
            subject_id,
            requester_id,
            purpose,
            at_time=0,
        )

    # Issue initial leases and record each issuance.
    leases: dict[str, AuthorizationLease] = {}
    lease_issuances: list[LeaseIssuanceRecord] = []

    for subject_id in workload.subject_ids:
        lease = authorization.issue_lease(
            subject_id,
            requester_id,
            purpose,
            at_time=0,
            ttl_seconds=(
                config.one_time_duration
                if strategy == Strategy.ONE_TIME
                else config.lease_duration
            ),
        )

        leases[subject_id] = lease

        lease_issuances.append(
            LeaseIssuanceRecord(
                subject_id=subject_id,
                requester_id=requester_id,
                purpose=purpose,
                issued_at=lease.issued_at,
                expires_at=lease.expires_at,
            )
        )

    # Combine requests and revocations into a chronological timeline.
    # Revocations take precedence at equal timestamps.
    events = []

    for event in workload.revocations:
        events.append(
            (event.at_time, 0, "revoke", event)
        )

    for request in workload.requests:
        events.append(
            (request.requested_at, 1, "request", request)
        )

    events.sort(key=lambda item: (item[0], item[1]))

    results: list[SimulationResult] = []

    for at_time, _, event_type, event in events:

        if event_type == "revoke":
            registry.revoke(
                event.subject_id,
                event.requester_id,
                event.purpose,
                at_time,
            )
            continue

        request: GenerationRequest = event
        lease = leases[request.subject_id]

        # Only SHORT_LEASE can renew expired leases.
        # Renewal requires connectivity and active consent.
        if (
            strategy == Strategy.SHORT_LEASE
            and not lease.is_valid(at_time)
            and connectivity.is_online(at_time)
            and registry.is_authorized(
                request.subject_id,
                request.requester_id,
                request.purpose,
                at_time,
            )
        ):
            lease = authorization.issue_lease(
                request.subject_id,
                request.requester_id,
                request.purpose,
                at_time,
                config.lease_duration,
            )

            leases[request.subject_id] = lease

            lease_issuances.append(
                LeaseIssuanceRecord(
                    subject_id=request.subject_id,
                    requester_id=request.requester_id,
                    purpose=request.purpose,
                    issued_at=lease.issued_at,
                    expires_at=lease.expires_at,
                )
            )

        result = simulator.evaluate(
            strategy=strategy,
            request=request,
            lease=lease,
            generation_time=at_time,
        )

        results.append(result)

    return ExperimentTrace(
        results=results,
        lease_issuances=lease_issuances,
    )


def run_experiment(
    workload: Workload,
    connectivity: ConnectivitySchedule,
    strategy: Strategy,
    config: ExperimentConfig,
) -> list[SimulationResult]:
    """Run an experiment and return authorization decisions."""

    return run_experiment_with_trace(
        workload,
        connectivity,
        strategy,
        config,
    ).results


from dataclasses import dataclass
from enum import Enum

from .authorization import AuthorizationService
from .connectivity import ConnectivitySchedule
from .models import AuthorizationLease, GenerationRequest


class Strategy(str, Enum):
    ONE_TIME = "one_time"
    FAIL_CLOSED = "fail_closed"
    SHORT_LEASE = "short_lease"


@dataclass(frozen=True)
class SimulationResult:
    strategy: Strategy
    request_id: str
    generation_time: float
    allowed: bool
    ground_truth_authorized: bool
    lease_issued_at: float | None = None
    lease_expires_at: float | None = None

    @property
    def unauthorized_approval(self) -> bool:
        return self.allowed and not self.ground_truth_authorized

    @property
    def legitimate_denial(self) -> bool:
        return not self.allowed and self.ground_truth_authorized


class ConsentSimulator:
    """Evaluates authorization strategies at generation time."""

    def __init__(
        self,
        authorization: AuthorizationService,
        connectivity: ConnectivitySchedule,
    ):
        self.authorization = authorization
        self.connectivity = connectivity

    def evaluate(
        self,
        strategy: Strategy,
        request: GenerationRequest,
        lease: AuthorizationLease,
        generation_time: float,
    ) -> SimulationResult:

        lease_valid = self.authorization.verify_lease(
            lease,
            request,
            generation_time,
        )

        online = self.connectivity.is_online(generation_time)

        if strategy == Strategy.ONE_TIME:
            # Accept the original lease until expiry.
            allowed = lease_valid

        elif strategy == Strategy.FAIL_CLOSED:
            # Require fresh consent confirmation.
            allowed = (
                online
                and generation_time >= request.requested_at
                and self.authorization.registry.is_authorized(
                    request.subject_id,
                    request.requester_id,
                    request.purpose,
                    generation_time,
                )
            )

        elif strategy == Strategy.SHORT_LEASE:
            if online:
                # Revalidate when the registry is reachable.
                allowed = self.authorization.verify_with_registry(
                    lease,
                    request,
                    generation_time,
                )
            else:
                # During an outage, accept an unexpired lease.
                allowed = lease_valid

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Ground truth always comes from the authoritative registry.
        ground_truth = self.authorization.registry.is_authorized(
            request.subject_id,
            request.requester_id,
            request.purpose,
            generation_time,
        )

        return SimulationResult(
            strategy=strategy,
            request_id=request.request_id,
            generation_time=generation_time,
            allowed=allowed,
            ground_truth_authorized=ground_truth,
            lease_issued_at=lease.issued_at,
            lease_expires_at=lease.expires_at,
        )

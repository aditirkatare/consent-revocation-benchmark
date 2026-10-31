
from uuid import uuid4

from .models import AuthorizationLease, GenerationRequest
from .registry import ConsentRegistry


class AuthorizationService:
    """Issues and validates simulated authorization leases."""

    def __init__(self, registry: ConsentRegistry):
        self.registry = registry

    def issue_lease(
        self,
        subject_id: str,
        requester_id: str,
        purpose: str,
        at_time: float,
        ttl_seconds: float,
    ) -> AuthorizationLease:
        if ttl_seconds <= 0:
            raise ValueError("Lease duration must be positive")

        if not self.registry.is_authorized(
            subject_id,
            requester_id,
            purpose,
            at_time,
        ):
            raise PermissionError("Consent is not active")

        return AuthorizationLease(
            lease_id=str(uuid4()),
            subject_id=subject_id,
            requester_id=requester_id,
            purpose=purpose,
            issued_at=at_time,
            expires_at=at_time + ttl_seconds,
        )

    def verify_lease(
        self,
        lease: AuthorizationLease,
        request: GenerationRequest,
        at_time: float,
    ) -> bool:
        """Check lease binding and expiry, not current consent."""

        if lease.subject_id != request.subject_id:
            return False

        if lease.requester_id != request.requester_id:
            return False

        if lease.purpose != request.purpose:
            return False

        if at_time < request.requested_at:
            return False

        return lease.is_valid(at_time)

    def verify_with_registry(
        self,
        lease: AuthorizationLease,
        request: GenerationRequest,
        at_time: float,
    ) -> bool:
        """Require both a valid lease and active registry consent."""

        if not self.verify_lease(lease, request, at_time):
            return False

        return self.registry.is_authorized(
            request.subject_id,
            request.requester_id,
            request.purpose,
            at_time,
        )

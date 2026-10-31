
from dataclasses import dataclass
from enum import Enum


class ConsentStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


@dataclass(frozen=True)
class ConsentRecord:
    subject_id: str
    requester_id: str
    purpose: str
    granted_at: float
    revoked_at: float | None = None

    def is_active(self, at_time: float) -> bool:
        if at_time < self.granted_at:
            return False

        if self.revoked_at is not None and at_time >= self.revoked_at:
            return False

        return True


@dataclass(frozen=True)
class AuthorizationLease:
    lease_id: str
    subject_id: str
    requester_id: str
    purpose: str
    issued_at: float
    expires_at: float

    def is_valid(self, at_time: float) -> bool:
        return self.issued_at <= at_time < self.expires_at


@dataclass(frozen=True)
class GenerationRequest:
    request_id: str
    subject_id: str
    requester_id: str
    purpose: str
    requested_at: float

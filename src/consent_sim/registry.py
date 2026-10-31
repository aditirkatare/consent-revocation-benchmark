
from dataclasses import replace

from .models import ConsentRecord


class ConsentRegistry:
    """Trusted consent registry with historical consent records."""

    def __init__(self):
        self._records: dict[
            tuple[str, str, str], list[ConsentRecord]
        ] = {}

    def grant(
        self,
        subject_id: str,
        requester_id: str,
        purpose: str,
        at_time: float,
    ) -> ConsentRecord:
        key = (subject_id, requester_id, purpose)
        history = self._records.setdefault(key, [])

        if history:
            latest = history[-1]

            if at_time < latest.granted_at:
                raise ValueError("Cannot grant consent in the past")

            if latest.is_active(at_time):
                raise ValueError("Consent is already active")

            if (
                latest.revoked_at is not None
                and at_time < latest.revoked_at
            ):
                raise ValueError(
                    "Cannot grant before the previous revocation"
                )

        record = ConsentRecord(
            subject_id=subject_id,
            requester_id=requester_id,
            purpose=purpose,
            granted_at=at_time,
        )

        history.append(record)
        return record

    def revoke(
        self,
        subject_id: str,
        requester_id: str,
        purpose: str,
        at_time: float,
    ) -> ConsentRecord:
        key = (subject_id, requester_id, purpose)
        history = self._records.get(key, [])

        if not history:
            raise ValueError("No consent record exists")

        latest = history[-1]

        if not latest.is_active(at_time):
            raise ValueError("Consent is not active at this time")

        revoked_record = replace(
            latest,
            revoked_at=at_time,
        )

        history[-1] = revoked_record
        return revoked_record

    def is_authorized(
        self,
        subject_id: str,
        requester_id: str,
        purpose: str,
        at_time: float,
    ) -> bool:
        key = (subject_id, requester_id, purpose)
        history = self._records.get(key, [])

        return any(
            record.is_active(at_time)
            for record in history
        )

    def get_record(
        self,
        subject_id: str,
        requester_id: str,
        purpose: str,
    ) -> ConsentRecord | None:
        key = (subject_id, requester_id, purpose)
        history = self._records.get(key, [])

        return history[-1] if history else None


import random
from dataclasses import dataclass

from .models import GenerationRequest


@dataclass(frozen=True)
class WorkloadConfig:
    seed: int = 42
    num_subjects: int = 100
    num_requests: int = 1000
    duration_seconds: float = 1000.0
    revocation_probability: float = 0.3


@dataclass(frozen=True)
class RevocationEvent:
    subject_id: str
    requester_id: str
    purpose: str
    at_time: float


@dataclass(frozen=True)
class Workload:
    requests: list[GenerationRequest]
    revocations: list[RevocationEvent]
    subject_ids: list[str]


def generate_workload(config: WorkloadConfig) -> Workload:
    """Generate deterministic synthetic consent-revocation events."""

    if config.num_subjects <= 0:
        raise ValueError("num_subjects must be positive")

    if config.num_requests < 0:
        raise ValueError("num_requests cannot be negative")

    if config.duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")

    if not 0 <= config.revocation_probability <= 1:
        raise ValueError(
            "revocation_probability must be between 0 and 1"
        )

    rng = random.Random(config.seed)

    subject_ids = [
        f"subject_{i:04d}"
        for i in range(config.num_subjects)
    ]

    requester_id = "requester_1"
    purpose = "FACE_SWAP"

    revocations = []

    for subject_id in subject_ids:
        if rng.random() < config.revocation_probability:
            revocations.append(
                RevocationEvent(
                    subject_id=subject_id,
                    requester_id=requester_id,
                    purpose=purpose,
                    at_time=rng.uniform(
                        config.duration_seconds * 0.2,
                        config.duration_seconds * 0.8,
                    ),
                )
            )

    requests = []

    for i in range(config.num_requests):
        subject_id = rng.choice(subject_ids)

        request = GenerationRequest(
            request_id=f"request_{i:06d}",
            subject_id=subject_id,
            requester_id=requester_id,
            purpose=purpose,
            requested_at=rng.uniform(
                0,
                config.duration_seconds,
            ),
        )

        requests.append(request)

    requests.sort(
        key=lambda request: (
            request.requested_at,
            request.request_id,
        )
    )

    revocations.sort(
        key=lambda event: (
            event.at_time,
            event.subject_id,
        )
    )

    return Workload(
        requests=requests,
        revocations=revocations,
        subject_ids=subject_ids,
    )

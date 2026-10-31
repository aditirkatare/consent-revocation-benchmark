
import pytest

from consent_sim.authorization import AuthorizationService
from consent_sim.models import GenerationRequest
from consent_sim.registry import ConsentRegistry


@pytest.fixture
def setup():
    registry = ConsentRegistry()
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)

    service = AuthorizationService(registry)

    request = GenerationRequest(
        request_id="request_1",
        subject_id="subject_1",
        requester_id="requester_1",
        purpose="FACE_SWAP",
        requested_at=20,
    )

    return registry, service, request


def test_lease_issued_with_active_consent(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    assert lease.issued_at == 20
    assert lease.expires_at == 80


def test_lease_denied_without_consent(setup):
    registry, service, request = setup

    with pytest.raises(PermissionError):
        service.issue_lease(
            "unknown", "requester_1", "FACE_SWAP", 20, 60
        )


def test_lease_valid_before_expiry(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    assert service.verify_lease(lease, request, 79)


def test_lease_invalid_at_exact_expiry(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    assert not service.verify_lease(lease, request, 80)


def test_lease_rejected_for_wrong_subject(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    wrong_request = GenerationRequest(
        "request_2", "subject_2", "requester_1", "FACE_SWAP", 20
    )

    assert not service.verify_lease(lease, wrong_request, 30)


def test_lease_rejected_for_wrong_requester(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    wrong_request = GenerationRequest(
        "request_2", "subject_1", "requester_2", "FACE_SWAP", 20
    )

    assert not service.verify_lease(lease, wrong_request, 30)


def test_lease_rejected_for_wrong_purpose(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    wrong_request = GenerationRequest(
        "request_2", "subject_1", "requester_1", "SELF_EDIT", 20
    )

    assert not service.verify_lease(lease, wrong_request, 30)


def test_cached_lease_remains_valid_after_revocation(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    registry.revoke(
        "subject_1", "requester_1", "FACE_SWAP", 40
    )

    assert service.verify_lease(lease, request, 50)


def test_registry_revalidation_blocks_revoked_consent(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    registry.revoke(
        "subject_1", "requester_1", "FACE_SWAP", 40
    )

    assert not service.verify_with_registry(lease, request, 50)


def test_zero_or_negative_ttl_rejected(setup):
    registry, service, request = setup

    with pytest.raises(ValueError):
        service.issue_lease(
            "subject_1", "requester_1", "FACE_SWAP", 20, 0
        )

    with pytest.raises(ValueError):
        service.issue_lease(
            "subject_1", "requester_1", "FACE_SWAP", 20, -5
        )


def test_lease_cannot_be_used_before_request_time(setup):
    registry, service, request = setup

    lease = service.issue_lease(
        "subject_1", "requester_1", "FACE_SWAP", 20, 60
    )

    assert not service.verify_lease(lease, request, 19)

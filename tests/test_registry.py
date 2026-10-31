
import pytest

from consent_sim.registry import ConsentRegistry


@pytest.fixture
def registry():
    return ConsentRegistry()


def test_consent_is_active_after_grant(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)

    assert registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 20
    )


def test_consent_is_inactive_before_grant(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)

    assert not registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 5
    )


def test_consent_is_revoked_at_exact_timestamp(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)
    registry.revoke("subject_1", "requester_1", "FACE_SWAP", 100)

    assert registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 99
    )

    assert not registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 100
    )


def test_consent_remains_revoked_after_revocation(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)
    registry.revoke("subject_1", "requester_1", "FACE_SWAP", 100)

    assert not registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 150
    )


def test_unknown_subject_is_denied(registry):
    assert not registry.is_authorized(
        "unknown", "requester_1", "FACE_SWAP", 20
    )


def test_duplicate_active_grant_is_rejected(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)

    with pytest.raises(ValueError):
        registry.grant("subject_1", "requester_1", "FACE_SWAP", 20)


def test_revoking_nonexistent_consent_is_rejected(registry):
    with pytest.raises(ValueError):
        registry.revoke("subject_1", "requester_1", "FACE_SWAP", 100)


def test_revoking_before_grant_is_rejected(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 100)

    with pytest.raises(ValueError):
        registry.revoke("subject_1", "requester_1", "FACE_SWAP", 50)


def test_consent_is_bound_to_requester(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)

    assert not registry.is_authorized(
        "subject_1", "requester_2", "FACE_SWAP", 20
    )


def test_consent_is_bound_to_purpose(registry):
    registry.grant("subject_1", "requester_1", "SELF_EDIT", 10)

    assert not registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 20
    )

def test_regrant_preserves_historical_consent(registry):
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)
    registry.revoke("subject_1", "requester_1", "FACE_SWAP", 100)
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 200)

    assert registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 50
    )

    assert not registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 150
    )

    assert registry.is_authorized(
        "subject_1", "requester_1", "FACE_SWAP", 250
    )

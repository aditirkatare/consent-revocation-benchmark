
import pytest

from consent_sim.authorization import AuthorizationService
from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.models import GenerationRequest
from consent_sim.registry import ConsentRegistry
from consent_sim.simulator import ConsentSimulator, Strategy


@pytest.fixture
def setup():
    registry = ConsentRegistry()
    registry.grant("subject_1", "requester_1", "FACE_SWAP", 10)

    authorization = AuthorizationService(registry)

    lease = authorization.issue_lease(
        "subject_1",
        "requester_1",
        "FACE_SWAP",
        at_time=20,
        ttl_seconds=60,
    )

    request = GenerationRequest(
        request_id="request_1",
        subject_id="subject_1",
        requester_id="requester_1",
        purpose="FACE_SWAP",
        requested_at=20,
    )

    # The registry becomes unreachable from time 40 to 100.
    connectivity = ConnectivitySchedule([Outage(40, 100)])

    simulator = ConsentSimulator(authorization, connectivity)

    return registry, simulator, request, lease


def test_all_strategies_allow_valid_online_request(setup):
    registry, simulator, request, lease = setup

    for strategy in Strategy:
        result = simulator.evaluate(
            strategy, request, lease, generation_time=30
        )
        assert result.allowed
        assert result.ground_truth_authorized


def test_fail_closed_denies_during_outage(setup):
    registry, simulator, request, lease = setup

    result = simulator.evaluate(
        Strategy.FAIL_CLOSED, request, lease, generation_time=50
    )

    assert not result.allowed
    assert result.legitimate_denial


def test_short_lease_allows_during_outage_before_expiry(setup):
    registry, simulator, request, lease = setup

    result = simulator.evaluate(
        Strategy.SHORT_LEASE, request, lease, generation_time=50
    )

    assert result.allowed
    assert not result.unauthorized_approval


def test_one_time_allows_during_outage_before_expiry(setup):
    registry, simulator, request, lease = setup

    result = simulator.evaluate(
        Strategy.ONE_TIME, request, lease, generation_time=50
    )

    assert result.allowed


def test_short_lease_denies_at_expiry(setup):
    registry, simulator, request, lease = setup

    result = simulator.evaluate(
        Strategy.SHORT_LEASE, request, lease, generation_time=80
    )

    assert not result.allowed


def test_revocation_causes_offline_unauthorized_approval(setup):
    registry, simulator, request, lease = setup

    registry.revoke(
        "subject_1", "requester_1", "FACE_SWAP", at_time=45
    )

    result = simulator.evaluate(
        Strategy.SHORT_LEASE, request, lease, generation_time=50
    )

    assert result.allowed
    assert not result.ground_truth_authorized
    assert result.unauthorized_approval


def test_fail_closed_blocks_after_revocation(setup):
    registry, simulator, request, lease = setup

    registry.revoke(
        "subject_1", "requester_1", "FACE_SWAP", at_time=45
    )

    result = simulator.evaluate(
        Strategy.FAIL_CLOSED, request, lease, generation_time=50
    )

    assert not result.allowed
    assert not result.unauthorized_approval


def test_online_revalidation_blocks_revoked_consent(setup):
    registry, simulator, request, lease = setup

    registry.revoke(
        "subject_1", "requester_1", "FACE_SWAP", at_time=45
    )

    # Network is online again at time 100.
    for strategy in (Strategy.FAIL_CLOSED, Strategy.SHORT_LEASE):
        result = simulator.evaluate(
            strategy, request, lease, generation_time=100
        )
        assert not result.allowed


def test_one_time_accepts_revoked_consent_until_expiry(setup):
    registry, simulator, request, lease = setup

    registry.revoke(
        "subject_1", "requester_1", "FACE_SWAP", at_time=35
    )

    result = simulator.evaluate(
        Strategy.ONE_TIME, request, lease, generation_time=39
    )

    assert result.unauthorized_approval


def test_invalid_strategy_rejected(setup):
    registry, simulator, request, lease = setup

    with pytest.raises(ValueError):
        simulator.evaluate(
            "invalid_strategy", request, lease, generation_time=30
        )

def test_fail_closed_allows_online_request_with_expired_lease(setup):
    registry, simulator, request, lease = setup

    # The lease expires at time 80.
    # Consent is still active at time 100.
    result = simulator.evaluate(
        Strategy.FAIL_CLOSED,
        request,
        lease,
        generation_time=100,
    )

    assert result.allowed
    assert result.ground_truth_authorized
    assert not result.legitimate_denial
    assert not result.unauthorized_approval
def test_short_lease_allows_offline_one_second_before_expiry(setup):
    registry, simulator, request, lease = setup

    result = simulator.evaluate(
        Strategy.SHORT_LEASE,
        request,
        lease,
        generation_time=79,
    )

    assert result.allowed
    assert result.ground_truth_authorized


def test_short_lease_denies_offline_at_exact_expiry(setup):
    registry, simulator, request, lease = setup

    result = simulator.evaluate(
        Strategy.SHORT_LEASE,
        request,
        lease,
        generation_time=80,
    )

    assert not result.allowed
    assert result.legitimate_denial


def test_short_lease_rejects_revoked_consent_when_online(setup):
    registry, simulator, request, lease = setup

    registry.revoke(
        "subject_1",
        "requester_1",
        "FACE_SWAP",
        at_time=35,
    )

    result = simulator.evaluate(
        Strategy.SHORT_LEASE,
        request,
        lease,
        generation_time=39,
    )

    assert not result.allowed
    assert result.unauthorized_approval is False

import pytest

from consent_sim.metrics import calculate_metrics
from consent_sim.simulator import SimulationResult, Strategy


def make_result(allowed, authorized):
    return SimulationResult(
        strategy=Strategy.SHORT_LEASE,
        request_id="test",
        generation_time=10,
        allowed=allowed,
        ground_truth_authorized=authorized,
    )


def test_all_legitimate_requests_approved():
    results = [
        make_result(True, True),
        make_result(True, True),
    ]

    metrics = calculate_metrics(results)

    assert metrics.total_requests == 2
    assert metrics.legitimate_denial_rate == 0
    assert metrics.unauthorized_approval_rate is None
    assert metrics.overall_approval_rate == 1


def test_all_unauthorized_requests_blocked():
    results = [
        make_result(False, False),
        make_result(False, False),
    ]

    metrics = calculate_metrics(results)

    assert metrics.unauthorized_approval_rate == 0
    assert metrics.legitimate_denial_rate is None
    assert metrics.overall_approval_rate == 0


def test_mixed_authorization_outcomes():
    results = [
        make_result(True, True),
        make_result(False, True),
        make_result(True, False),
        make_result(False, False),
    ]

    metrics = calculate_metrics(results)

    assert metrics.total_requests == 4
    assert metrics.legitimate_requests == 2
    assert metrics.unauthorized_requests == 2
    assert metrics.allowed_requests == 2

    assert metrics.unauthorized_approvals == 1
    assert metrics.legitimate_denials == 1

    assert metrics.unauthorized_approval_rate == pytest.approx(0.5)
    assert metrics.legitimate_denial_rate == pytest.approx(0.5)
    assert metrics.overall_approval_rate == pytest.approx(0.5)


def test_empty_results():
    metrics = calculate_metrics([])

    assert metrics.total_requests == 0
    assert metrics.unauthorized_approval_rate is None
    assert metrics.legitimate_denial_rate is None
    assert metrics.overall_approval_rate is None


def test_all_unauthorized_requests_approved():
    results = [
        make_result(True, False),
        make_result(True, False),
    ]

    metrics = calculate_metrics(results)

    assert metrics.unauthorized_approvals == 2
    assert metrics.unauthorized_approval_rate == 1


def test_all_legitimate_requests_denied():
    results = [
        make_result(False, True),
        make_result(False, True),
    ]

    metrics = calculate_metrics(results)

    assert metrics.legitimate_denials == 2
    assert metrics.legitimate_denial_rate == 1


import pytest
from consent_sim.runner import run_experiment_with_trace
from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.models import GenerationRequest
from consent_sim.runner import ExperimentConfig, run_experiment
from consent_sim.simulator import Strategy
from consent_sim.workload import RevocationEvent, Workload


def make_workload(request_times, revocation_time=None):
    requests = [
        GenerationRequest(
            request_id=f"request_{i}",
            subject_id="subject_1",
            requester_id="requester_1",
            purpose="FACE_SWAP",
            requested_at=time,
        )
        for i, time in enumerate(request_times)
    ]

    revocations = []

    if revocation_time is not None:
        revocations.append(
            RevocationEvent(
                subject_id="subject_1",
                requester_id="requester_1",
                purpose="FACE_SWAP",
                at_time=revocation_time,
            )
        )

    return Workload(
        requests=requests,
        revocations=revocations,
        subject_ids=["subject_1"],
    )


def test_valid_online_request_allowed():
    workload = make_workload([10])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    assert len(results) == 1
    assert results[0].allowed


def test_fail_closed_blocks_revoked_consent():
    workload = make_workload([10, 30], revocation_time=20)

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].allowed
    assert not results[1].allowed
    assert not results[1].ground_truth_authorized


def test_one_time_accepts_revoked_consent_before_expiry():
    workload = make_workload([30], revocation_time=20)

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].unauthorized_approval


def test_short_lease_offline_exposure_after_revocation():
    workload = make_workload([30], revocation_time=20)
    connectivity = ConnectivitySchedule([Outage(15, 40)])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].unauthorized_approval


def test_short_lease_online_blocks_revocation():
    workload = make_workload([30], revocation_time=20)

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert not results[0].allowed
    assert not results[0].unauthorized_approval


def test_fail_closed_denies_during_outage():
    workload = make_workload([30])
    connectivity = ConnectivitySchedule([Outage(20, 40)])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].legitimate_denial


def test_short_lease_allows_valid_offline_request():
    workload = make_workload([30])
    connectivity = ConnectivitySchedule([Outage(20, 40)])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].allowed
    assert results[0].ground_truth_authorized


def test_expired_lease_denied_during_outage():
    workload = make_workload([70])
    connectivity = ConnectivitySchedule([Outage(50, 100)])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].legitimate_denial


def test_expired_lease_refreshed_when_online():
    workload = make_workload([70])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].allowed


def test_revocation_takes_precedence_at_same_timestamp():
    workload = make_workload([20], revocation_time=20)

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    assert not results[0].allowed
    assert not results[0].ground_truth_authorized


def test_results_follow_chronological_order():
    workload = make_workload([50, 10, 30])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
        ExperimentConfig(lease_duration=60),
    )

    assert [result.generation_time for result in results] == [
        10, 30, 50
    ]


def test_invalid_lease_duration_rejected():
    workload = make_workload([10])

    with pytest.raises(ValueError):
        run_experiment(
            workload,
            ConnectivitySchedule(),
            Strategy.SHORT_LEASE,
            ExperimentConfig(lease_duration=0),
        )

def test_one_time_does_not_refresh_expired_authorization():
    workload = make_workload([30, 70, 1000, 1100])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
        ExperimentConfig(
            lease_duration=60,
            one_time_duration=1000,
        ),
    )

    assert len(results) == 4

    # One-time authorization remains valid before expiry.
    assert results[0].allowed
    assert results[1].allowed

    # Authorization expires at exactly 1000 seconds.
    assert not results[2].allowed

    # It must not renew, even when online.
    assert not results[3].allowed

    # Consent remains active throughout the experiment.
    assert all(
        result.ground_truth_authorized
        for result in results
    )

    # Expired authorization causes legitimate denials.
    assert results[2].legitimate_denial
    assert results[3].legitimate_denial

def test_fail_closed_does_not_require_lease_renewal():
    workload = make_workload([30, 70, 130, 200])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    assert len(results) == 4

    # Consent remains active throughout the experiment.
    assert all(
        result.ground_truth_authorized
        for result in results
    )

    # All requests must succeed through online revalidation,
    # including those after the initial lease expires.
    assert all(result.allowed for result in results)

    # No legitimate request should be denied.
    assert not any(
        result.legitimate_denial
        for result in results
    )
def test_short_lease_renews_after_expiry_when_online():
    workload = make_workload([30, 70, 130])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert len(results) == 3
    assert all(result.allowed for result in results)


def test_short_lease_does_not_renew_after_revocation():
    workload = make_workload(
        [30, 70, 130],
        revocation_time=50,
    )

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].allowed
    assert not results[1].allowed
    assert not results[2].allowed


def test_short_lease_offline_expiry_causes_legitimate_denial():
    workload = make_workload([30, 70, 90])

    connectivity = ConnectivitySchedule([
        Outage(50, 100),
    ])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].allowed
    assert results[1].legitimate_denial
    assert results[2].legitimate_denial
def test_short_lease_blocks_revocation_when_online():
    workload = make_workload(
        [10, 30, 70],
        revocation_time=20,
    )

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=300),
    )

    assert results[0].allowed
    assert not results[1].allowed
    assert not results[2].allowed
def test_short_lease_revalidates_at_outage_end():
    workload = make_workload(
        [49, 50],
        revocation_time=20,
    )

    connectivity = ConnectivitySchedule([
        Outage(10, 50),
    ])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=100),
    )

    assert results[0].unauthorized_approval
    assert not results[1].allowed
def test_short_lease_recovers_after_connectivity_returns():
    workload = make_workload([70, 110])

    connectivity = ConnectivitySchedule([
        Outage(50, 100),
    ])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].legitimate_denial
    assert results[1].allowed

def test_short_lease_records_initial_lease_lifetime():
    workload = make_workload([30])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].lease_issued_at == 0
    assert results[0].lease_expires_at == 60


def test_short_lease_records_renewed_lease_lifetime():
    workload = make_workload([30, 70])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].lease_issued_at == 0
    assert results[0].lease_expires_at == 60

    assert results[1].lease_issued_at == 70
    assert results[1].lease_expires_at == 130


def test_short_lease_does_not_renew_during_outage():
    workload = make_workload([70])

    connectivity = ConnectivitySchedule([
        Outage(50, 100),
    ])

    results = run_experiment(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert results[0].lease_issued_at == 0
    assert results[0].lease_expires_at == 60
    assert results[0].legitimate_denial


def test_one_time_records_independent_authorization_lifetime():
    workload = make_workload([70])

    results = run_experiment(
        workload,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
        ExperimentConfig(
            lease_duration=60,
            one_time_duration=1000,
        ),
    )

    assert results[0].lease_issued_at == 0
    assert results[0].lease_expires_at == 1000
    assert results[0].allowed

def test_trace_records_initial_lease():
    workload = make_workload([30])

    trace = run_experiment_with_trace(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert len(trace.results) == 1
    assert len(trace.lease_issuances) == 1

    issuance = trace.lease_issuances[0]

    assert issuance.subject_id == "subject_1"
    assert issuance.issued_at == 0
    assert issuance.expires_at == 60


def test_trace_records_lease_renewal():
    workload = make_workload([30, 70])

    trace = run_experiment_with_trace(
        workload,
        ConnectivitySchedule(),
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert len(trace.lease_issuances) == 2

    assert [
        (record.issued_at, record.expires_at)
        for record in trace.lease_issuances
    ] == [
        (0, 60),
        (70, 130),
    ]


def test_trace_does_not_record_offline_renewal():
    workload = make_workload([70])

    connectivity = ConnectivitySchedule([
        Outage(50, 100),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    assert len(trace.lease_issuances) == 1
    assert trace.results[0].legitimate_denial


def test_trace_one_time_issues_only_initial_authorization():
    workload = make_workload([30, 70, 130])

    trace = run_experiment_with_trace(
        workload,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
        ExperimentConfig(
            lease_duration=60,
            one_time_duration=1000,
        ),
    )

    assert len(trace.lease_issuances) == 1
    assert trace.lease_issuances[0].expires_at == 1000


def test_trace_fail_closed_does_not_renew_leases():
    workload = make_workload([30, 70, 130])

    trace = run_experiment_with_trace(
        workload,
        ConnectivitySchedule(),
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    assert len(trace.lease_issuances) == 1
    assert all(result.allowed for result in trace.results)

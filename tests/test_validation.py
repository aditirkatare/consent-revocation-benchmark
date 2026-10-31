
from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.validation import validate_exposure_consistency
from consent_sim.workload import (
    RevocationEvent,
    Workload,
)
from consent_sim.models import GenerationRequest


def make_workload():
    return Workload(
        subject_ids=["subject_1"],
        revocations=[
            RevocationEvent(
                subject_id="subject_1",
                requester_id="requester_1",
                purpose="FACE_SWAP",
                at_time=20,
            )
        ],
        requests=[
            GenerationRequest(
                request_id="r1",
                subject_id="subject_1",
                requester_id="requester_1",
                purpose="FACE_SWAP",
                requested_at=30,
            )
        ],
    )


def run_validation(strategy, connectivity):
    workload = make_workload()

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        strategy,
        ExperimentConfig(
            lease_duration=60,
            one_time_duration=100,
        ),
    )

    summary = calculate_horizon_exposure(
        workload,
        trace,
        connectivity,
        strategy,
        observation_end=100,
    )

    return validate_exposure_consistency(
        trace.results,
        summary,
        {"r1": "subject_1"},
    )


def test_one_time_unauthorized_approval_matches_exposure():
    validation = run_validation(
        Strategy.ONE_TIME,
        ConnectivitySchedule(),
    )

    assert validation.passed
    assert validation.matched_approvals == 1


def test_short_lease_offline_approval_matches_exposure():
    validation = run_validation(
        Strategy.SHORT_LEASE,
        ConnectivitySchedule([
            Outage(10, 50),
        ]),
    )

    assert validation.passed
    assert validation.matched_approvals == 1


def test_fail_closed_has_no_unauthorized_approvals():
    validation = run_validation(
        Strategy.FAIL_CLOSED,
        ConnectivitySchedule([
            Outage(10, 50),
        ]),
    )

    assert validation.passed
    assert validation.unauthorized_approvals == 0


def test_short_lease_online_has_no_unauthorized_approvals():
    validation = run_validation(
        Strategy.SHORT_LEASE,
        ConnectivitySchedule(),
    )

    assert validation.passed
    assert validation.unauthorized_approvals == 0

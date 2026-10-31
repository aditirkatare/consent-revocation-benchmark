
import pytest

from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.workload import RevocationEvent, Workload


def make_workload(revocation_time):
    return Workload(
        requests=[],
        revocations=[
            RevocationEvent(
                subject_id="subject_1",
                requester_id="requester_1",
                purpose="FACE_SWAP",
                at_time=revocation_time,
            )
        ],
        subject_ids=["subject_1"],
    )


def test_one_time_exposure_clipped_to_horizon():
    workload = make_workload(50)
    connectivity = ConnectivitySchedule()

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.ONE_TIME,
        ExperimentConfig(one_time_duration=200),
    )

    summary = calculate_horizon_exposure(
        workload,
        trace,
        connectivity,
        Strategy.ONE_TIME,
        observation_end=100,
    )

    exposure = summary.subject_exposures[0]

    assert exposure.total_exposure_seconds == 50
    assert exposure.exposure_intervals == ((50, 100),)


def test_short_lease_exposure_clipped_to_horizon():
    workload = make_workload(50)
    connectivity = ConnectivitySchedule([
        Outage(40, 200),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=150),
    )

    summary = calculate_horizon_exposure(
        workload,
        trace,
        connectivity,
        Strategy.SHORT_LEASE,
        observation_end=100,
    )

    assert summary.subject_exposures[0].total_exposure_seconds == 50


def test_fail_closed_exposure_remains_zero():
    workload = make_workload(50)
    connectivity = ConnectivitySchedule([
        Outage(40, 200),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.FAIL_CLOSED,
        ExperimentConfig(),
    )

    summary = calculate_horizon_exposure(
        workload,
        trace,
        connectivity,
        Strategy.FAIL_CLOSED,
        observation_end=100,
    )

    assert summary.subject_exposures[0].total_exposure_seconds == 0


def test_revocation_after_horizon_has_zero_exposure():
    workload = make_workload(150)
    connectivity = ConnectivitySchedule()

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.ONE_TIME,
        ExperimentConfig(one_time_duration=300),
    )

    summary = calculate_horizon_exposure(
        workload,
        trace,
        connectivity,
        Strategy.ONE_TIME,
        observation_end=100,
    )

    assert summary.subject_exposures[0].total_exposure_seconds == 0


def test_invalid_horizon_rejected():
    workload = make_workload(50)
    connectivity = ConnectivitySchedule()

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.ONE_TIME,
        ExperimentConfig(),
    )

    with pytest.raises(ValueError):
        calculate_horizon_exposure(
            workload,
            trace,
            connectivity,
            Strategy.ONE_TIME,
            observation_end=0,
        )

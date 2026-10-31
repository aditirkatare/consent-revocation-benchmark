
import pytest

from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure import calculate_exposure_window


def test_online_revocation_has_zero_exposure():
    connectivity = ConnectivitySchedule()

    result = calculate_exposure_window(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.duration == 0


def test_offline_exposure_ends_at_lease_expiry():
    connectivity = ConnectivitySchedule([
        Outage(40, 200),
    ])

    result = calculate_exposure_window(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.duration == 50


def test_offline_exposure_ends_at_reconnection():
    connectivity = ConnectivitySchedule([
        Outage(40, 80),
    ])

    result = calculate_exposure_window(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.duration == 30


def test_expired_authorization_has_zero_exposure():
    connectivity = ConnectivitySchedule([
        Outage(40, 200),
    ])

    result = calculate_exposure_window(
        revocation_time=100,
        authorization_expiry=50,
        connectivity=connectivity,
    )

    assert result.duration == 0


def test_revocation_at_outage_boundary():
    connectivity = ConnectivitySchedule([
        Outage(50, 100),
    ])

    result = calculate_exposure_window(
        revocation_time=50,
        authorization_expiry=80,
        connectivity=connectivity,
    )

    assert result.duration == 30


def test_revocation_at_reconnection_boundary():
    connectivity = ConnectivitySchedule([
        Outage(40, 50),
    ])

    result = calculate_exposure_window(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.duration == 0


def test_exposure_never_negative():
    connectivity = ConnectivitySchedule([
        Outage(40, 100),
    ])

    result = calculate_exposure_window(
        revocation_time=80,
        authorization_expiry=60,
        connectivity=connectivity,
    )

    assert result.duration >= 0


def test_exposure_end_is_correct():
    connectivity = ConnectivitySchedule([
        Outage(40, 90),
    ])

    result = calculate_exposure_window(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.exposure_end == 90
    assert result.duration == pytest.approx(40)

from consent_sim.exposure import calculate_cumulative_exposure


def test_cumulative_exposure_across_two_outages():
    connectivity = ConnectivitySchedule([
        Outage(40, 60),
        Outage(80, 120),
    ])

    result = calculate_cumulative_exposure(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.exposure_intervals == (
        (50, 60),
        (80, 100),
    )
    assert result.total_exposure_seconds == pytest.approx(30)


def test_overlapping_outages_are_not_double_counted():
    connectivity = ConnectivitySchedule([
        Outage(40, 90),
        Outage(60, 110),
    ])

    result = calculate_cumulative_exposure(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=connectivity,
    )

    assert result.exposure_intervals == ((50, 100),)
    assert result.total_exposure_seconds == pytest.approx(50)


def test_online_periods_have_zero_cumulative_exposure():
    result = calculate_cumulative_exposure(
        revocation_time=50,
        authorization_expiry=100,
        connectivity=ConnectivitySchedule(),
    )

    assert result.total_exposure_seconds == 0
    assert result.exposure_intervals == ()


def test_expired_lease_has_zero_cumulative_exposure():
    result = calculate_cumulative_exposure(
        revocation_time=100,
        authorization_expiry=80,
        connectivity=ConnectivitySchedule([
            Outage(50, 150),
        ]),
    )

    assert result.total_exposure_seconds == 0


def test_outage_after_expiry_does_not_contribute():
    result = calculate_cumulative_exposure(
        revocation_time=20,
        authorization_expiry=60,
        connectivity=ConnectivitySchedule([
            Outage(80, 120),
        ]),
    )

    assert result.total_exposure_seconds == 0


def test_adjacent_outages_merge():
    result = calculate_cumulative_exposure(
        revocation_time=40,
        authorization_expiry=100,
        connectivity=ConnectivitySchedule([
            Outage(40, 60),
            Outage(60, 80),
        ]),
    )

    assert result.exposure_intervals == ((40, 80),)
    assert result.total_exposure_seconds == 40

from consent_sim.runner import (
    ExperimentConfig,
    run_experiment_with_trace,
)
from consent_sim.simulator import Strategy
from consent_sim.workload import RevocationEvent, Workload
from consent_sim.exposure import calculate_trace_exposure


def make_exposure_workload(revocation_time):
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


def test_trace_exposure_single_outage():
    workload = make_exposure_workload(50)

    connectivity = ConnectivitySchedule([
        Outage(40, 100),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=80),
    )

    exposures = calculate_trace_exposure(
        workload,
        trace,
        connectivity,
    )

    assert len(exposures) == 1
    assert exposures[0].total_exposure_seconds == 30


def test_trace_exposure_multiple_outages():
    workload = make_exposure_workload(50)

    connectivity = ConnectivitySchedule([
        Outage(40, 60),
        Outage(70, 100),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=90),
    )

    exposures = calculate_trace_exposure(
        workload,
        trace,
        connectivity,
    )

    assert exposures[0].total_exposure_seconds == 30
    assert exposures[0].exposure_intervals == (
        (50, 60),
        (70, 90),
    )


def test_trace_exposure_zero_when_online():
    workload = make_exposure_workload(50)

    connectivity = ConnectivitySchedule()

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=100),
    )

    exposures = calculate_trace_exposure(
        workload,
        trace,
        connectivity,
    )

    assert exposures[0].total_exposure_seconds == 0


def test_trace_exposure_zero_after_expiry():
    workload = make_exposure_workload(100)

    connectivity = ConnectivitySchedule([
        Outage(40, 150),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=60),
    )

    exposures = calculate_trace_exposure(
        workload,
        trace,
        connectivity,
    )

    assert exposures[0].total_exposure_seconds == 0

from consent_sim.exposure import calculate_strategy_exposure


def test_one_time_exposure_includes_online_periods():
    workload = make_exposure_workload(50)

    connectivity = ConnectivitySchedule()

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.ONE_TIME,
        ExperimentConfig(one_time_duration=100),
    )

    exposures = calculate_strategy_exposure(
        workload,
        trace,
        connectivity,
        Strategy.ONE_TIME,
    )

    assert exposures[0].total_exposure_seconds == 50
    assert exposures[0].exposure_intervals == ((50, 100),)


def test_fail_closed_has_zero_post_revocation_exposure():
    workload = make_exposure_workload(50)

    connectivity = ConnectivitySchedule([
        Outage(40, 100),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.FAIL_CLOSED,
        ExperimentConfig(lease_duration=60),
    )

    exposures = calculate_strategy_exposure(
        workload,
        trace,
        connectivity,
        Strategy.FAIL_CLOSED,
    )

    assert exposures[0].total_exposure_seconds == 0


def test_short_lease_exposure_only_during_outage():
    workload = make_exposure_workload(50)

    connectivity = ConnectivitySchedule([
        Outage(40, 80),
    ])

    trace = run_experiment_with_trace(
        workload,
        connectivity,
        Strategy.SHORT_LEASE,
        ExperimentConfig(lease_duration=100),
    )

    exposures = calculate_strategy_exposure(
        workload,
        trace,
        connectivity,
        Strategy.SHORT_LEASE,
    )

    assert exposures[0].total_exposure_seconds == 30


def test_one_time_exposure_ends_at_authorization_expiry():
    workload = make_exposure_workload(50)

    trace = run_experiment_with_trace(
        workload,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
        ExperimentConfig(one_time_duration=80),
    )

    exposures = calculate_strategy_exposure(
        workload,
        trace,
        ConnectivitySchedule(),
        Strategy.ONE_TIME,
    )

    assert exposures[0].total_exposure_seconds == 30

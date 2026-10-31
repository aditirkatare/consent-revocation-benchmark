
import pytest

from consent_sim.workload import WorkloadConfig, generate_workload


def test_default_workload_size():
    workload = generate_workload(WorkloadConfig())

    assert len(workload.subject_ids) == 100
    assert len(workload.requests) == 1000


def test_same_seed_produces_identical_workload():
    config = WorkloadConfig(seed=42)

    first = generate_workload(config)
    second = generate_workload(config)

    assert first == second


def test_different_seeds_produce_different_workloads():
    first = generate_workload(WorkloadConfig(seed=42))
    second = generate_workload(WorkloadConfig(seed=99))

    assert first != second


def test_request_ids_are_unique():
    workload = generate_workload(WorkloadConfig())

    request_ids = [
        request.request_id
        for request in workload.requests
    ]

    assert len(request_ids) == len(set(request_ids))


def test_requests_are_chronologically_sorted():
    workload = generate_workload(WorkloadConfig())

    timestamps = [
        request.requested_at
        for request in workload.requests
    ]

    assert timestamps == sorted(timestamps)


def test_revocations_are_chronologically_sorted():
    workload = generate_workload(WorkloadConfig())

    timestamps = [
        event.at_time
        for event in workload.revocations
    ]

    assert timestamps == sorted(timestamps)


def test_request_timestamps_within_duration():
    config = WorkloadConfig(duration_seconds=500)
    workload = generate_workload(config)

    assert all(
        0 <= request.requested_at <= 500
        for request in workload.requests
    )


def test_revocations_reference_valid_subjects():
    workload = generate_workload(WorkloadConfig())

    assert all(
        event.subject_id in workload.subject_ids
        for event in workload.revocations
    )


def test_zero_revocation_probability():
    config = WorkloadConfig(
        revocation_probability=0.0
    )

    workload = generate_workload(config)

    assert len(workload.revocations) == 0


def test_full_revocation_probability():
    config = WorkloadConfig(
        num_subjects=20,
        revocation_probability=1.0
    )

    workload = generate_workload(config)

    assert len(workload.revocations) == 20


@pytest.mark.parametrize(
    "config",
    [
        WorkloadConfig(num_subjects=0),
        WorkloadConfig(num_requests=-1),
        WorkloadConfig(duration_seconds=0),
        WorkloadConfig(revocation_probability=-0.1),
        WorkloadConfig(revocation_probability=1.1),
    ],
)
def test_invalid_configuration_rejected(config):
    with pytest.raises(ValueError):
        generate_workload(config)

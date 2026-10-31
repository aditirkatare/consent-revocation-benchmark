
import pytest

from consent_sim.random_outages import generate_random_outages


def test_random_outages_are_reproducible():
    first = generate_random_outages(42, 1000, 3, 100)
    second = generate_random_outages(42, 1000, 3, 100)

    assert first.outages == second.outages


def test_random_outages_are_within_horizon():
    schedule = generate_random_outages(42, 1000, 3, 100)

    assert all(
        0 <= outage.start < outage.end <= 1000
        for outage in schedule.outages
    )


def test_random_outages_do_not_overlap():
    schedule = generate_random_outages(42, 1000, 3, 100)

    for previous, current in zip(
        schedule.outages,
        schedule.outages[1:],
    ):
        assert previous.end <= current.start


def test_zero_outages():
    schedule = generate_random_outages(42, 1000, 0, 100)

    assert schedule.outages == []


def test_zero_duration():
    schedule = generate_random_outages(42, 1000, 3, 0)

    assert schedule.outages == []


@pytest.mark.parametrize(
    "horizon,count,duration",
    [
        (0, 3, 100),
        (1000, -1, 100),
        (1000, 3, -1),
        (100, 3, 50),
    ],
)
def test_invalid_outage_configuration(horizon, count, duration):
    with pytest.raises(ValueError):
        generate_random_outages(
            42,
            horizon,
            count,
            duration,
        )


import pytest

from consent_sim.connectivity import Outage, ConnectivitySchedule


def test_network_online_by_default():
    network = ConnectivitySchedule()

    assert network.is_online(0)
    assert network.is_online(100)


def test_network_offline_during_outage():
    network = ConnectivitySchedule([
        Outage(40, 100)
    ])

    assert not network.is_online(50)
    assert not network.is_online(99)


def test_network_online_before_outage():
    network = ConnectivitySchedule([
        Outage(40, 100)
    ])

    assert network.is_online(39)


def test_network_offline_at_exact_start():
    network = ConnectivitySchedule([
        Outage(40, 100)
    ])

    assert not network.is_online(40)


def test_network_online_at_exact_end():
    network = ConnectivitySchedule([
        Outage(40, 100)
    ])

    assert network.is_online(100)


def test_multiple_outages():
    network = ConnectivitySchedule([
        Outage(20, 40),
        Outage(70, 90),
    ])

    assert not network.is_online(30)
    assert network.is_online(50)
    assert not network.is_online(80)


def test_add_outage():
    network = ConnectivitySchedule()

    network.add_outage(10, 20)

    assert network.is_online(5)
    assert not network.is_online(15)
    assert network.is_online(20)


def test_invalid_outage_rejected():
    with pytest.raises(ValueError):
        Outage(100, 50)

    with pytest.raises(ValueError):
        Outage(50, 50)


def test_overlapping_outages():
    network = ConnectivitySchedule([
        Outage(20, 60),
        Outage(40, 80),
    ])

    assert not network.is_online(30)
    assert not network.is_online(70)
    assert network.is_online(80)

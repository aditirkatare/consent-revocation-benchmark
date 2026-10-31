
import pytest

from consent_sim.statistics import estimate_mean


def test_constant_values_have_zero_width_interval():
    result = estimate_mean([0.5] * 30)

    assert result.n == 30
    assert result.mean == pytest.approx(0.5)
    assert result.standard_deviation == 0
    assert result.ci_lower == pytest.approx(0.5)
    assert result.ci_upper == pytest.approx(0.5)


def test_varying_values_have_positive_interval_width():
    result = estimate_mean([i / 30 for i in range(30)])

    assert result.standard_deviation > 0
    assert result.ci_lower < result.mean
    assert result.ci_upper > result.mean


def test_single_observation_has_no_interval():
    result = estimate_mean([0.25])

    assert result.mean == 0.25
    assert result.ci_lower is None
    assert result.ci_upper is None


def test_empty_values_rejected():
    with pytest.raises(ValueError):
        estimate_mean([])


def test_nonfinite_values_rejected():
    with pytest.raises(ValueError):
        estimate_mean([float("nan")] * 30)


def test_wrong_sample_size_rejected():
    with pytest.raises(ValueError):
        estimate_mean([0.5] * 10)

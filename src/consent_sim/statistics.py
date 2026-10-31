
from dataclasses import dataclass
from math import sqrt
from statistics import mean, stdev


@dataclass(frozen=True)
class MeanEstimate:
    n: int
    mean: float
    standard_deviation: float
    ci_lower: float | None
    ci_upper: float | None


def estimate_mean(values: list[float]) -> MeanEstimate:
    """Estimate a mean and approximate 95% confidence interval."""

    if not values:
        raise ValueError("At least one observation is required")

    if any(not (-float("inf") < x < float("inf")) for x in values):
        raise ValueError("All observations must be finite")

    n = len(values)
    average = mean(values)

    if n == 1:
        return MeanEstimate(n, average, 0.0, None, None)

    sd = stdev(values)

    # Approximate 95% t critical value for 29 degrees of freedom.
    # Intended for the planned 30-seed experiment only.
    if n != 30:
        raise ValueError("Confidence intervals require exactly 30 seeds")

    margin = 2.04523 * sd / sqrt(n)

    return MeanEstimate(
        n=n,
        mean=average,
        standard_deviation=sd,
        ci_lower=average - margin,
        ci_upper=average + margin,
    )

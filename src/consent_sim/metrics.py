
from dataclasses import dataclass

from .simulator import SimulationResult


@dataclass(frozen=True)
class ExperimentMetrics:
    total_requests: int
    legitimate_requests: int
    unauthorized_requests: int
    allowed_requests: int
    unauthorized_approvals: int
    legitimate_denials: int
    unauthorized_approval_rate: float | None
    legitimate_denial_rate: float | None
    overall_approval_rate: float | None


def calculate_metrics(
    results: list[SimulationResult],
) -> ExperimentMetrics:
    """Calculate authorization metrics from simulation results."""

    total = len(results)

    legitimate = sum(
        result.ground_truth_authorized
        for result in results
    )

    unauthorized = total - legitimate

    allowed = sum(
        result.allowed
        for result in results
    )

    unauthorized_approvals = sum(
        result.unauthorized_approval
        for result in results
    )

    legitimate_denials = sum(
        result.legitimate_denial
        for result in results
    )

    return ExperimentMetrics(
        total_requests=total,
        legitimate_requests=legitimate,
        unauthorized_requests=unauthorized,
        allowed_requests=allowed,
        unauthorized_approvals=unauthorized_approvals,
        legitimate_denials=legitimate_denials,
        unauthorized_approval_rate=(
            unauthorized_approvals / unauthorized
            if unauthorized > 0 else None
        ),
        legitimate_denial_rate=(
            legitimate_denials / legitimate
            if legitimate > 0 else None
        ),
        overall_approval_rate=(
            allowed / total
            if total > 0 else None
        ),
    )

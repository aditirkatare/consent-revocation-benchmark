
import csv
from pathlib import Path

from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.metrics import calculate_metrics
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.workload import WorkloadConfig, generate_workload


LEASE_DURATIONS = [30, 60, 120, 300]
OUTAGE_DURATIONS = [0, 30, 60, 120, 180]
SEEDS = range(100, 130)
HORIZON = 1000.0


def make_connectivity(outage_duration):
    if outage_duration == 0:
        return ConnectivitySchedule()

    return ConnectivitySchedule([
        Outage(start, start + outage_duration)
        for start in (200, 500, 800)
    ])


def main():
    rows = []

    for seed in SEEDS:
        workload = generate_workload(
            WorkloadConfig(
                seed=seed,
                num_subjects=100,
                num_requests=1000,
                duration_seconds=HORIZON,
                revocation_probability=0.3,
            )
        )

        for outage_duration in OUTAGE_DURATIONS:
            connectivity = make_connectivity(outage_duration)

            for lease_duration in LEASE_DURATIONS:
                config = ExperimentConfig(
                    lease_duration=lease_duration,
                    one_time_duration=HORIZON,
                )

                for strategy in (
                    Strategy.FAIL_CLOSED,
                    Strategy.SHORT_LEASE,
                ):
                    trace = run_experiment_with_trace(
                        workload,
                        connectivity,
                        strategy,
                        config,
                    )

                    metrics = calculate_metrics(trace.results)

                    exposure = calculate_horizon_exposure(
                        workload,
                        trace,
                        connectivity,
                        strategy,
                        observation_end=HORIZON,
                    )

                    durations = [
                        item.total_exposure_seconds
                        for item in exposure.subject_exposures
                    ]

                    rows.append({
                        "seed": seed,
                        "outage_duration": outage_duration,
                        "lease_duration": lease_duration,
                        "strategy": strategy.value,
                        "unauthorized_approval_rate":
                            metrics.unauthorized_approval_rate,
                        "legitimate_denial_rate":
                            metrics.legitimate_denial_rate,
                        "mean_exposure_seconds": (
                            sum(durations) / len(durations)
                            if durations else None
                        ),
                    })

    output = Path("results/outage_sensitivity.csv")
    output.parent.mkdir(exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Completed {len(rows)} simulation runs")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()

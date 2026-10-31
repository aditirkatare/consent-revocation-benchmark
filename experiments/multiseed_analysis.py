
import csv
from pathlib import Path

from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.metrics import calculate_metrics
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.workload import WorkloadConfig, generate_workload


def main():
    rows = []
    durations = [10, 30, 60, 120, 300]

    for seed in range(100, 130):
        workload = generate_workload(
            WorkloadConfig(
                seed=seed,
                num_subjects=100,
                num_requests=1000,
                duration_seconds=1000,
                revocation_probability=0.3,
            )
        )

        connectivity = ConnectivitySchedule([
            Outage(200, 300),
            Outage(500, 650),
            Outage(800, 900),
        ])

        for duration in durations:
            config = ExperimentConfig(
                lease_duration=duration,
                one_time_duration=1000,
            )

            for strategy in Strategy:
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
                    observation_end=1000,
                )

                subject_durations = [
                    item.total_exposure_seconds
                    for item in exposure.subject_exposures
                ]

                mean_exposure = (
                    sum(subject_durations) / len(subject_durations)
                    if subject_durations else None
                )

                rows.append({
                    "seed": seed,
                    "lease_duration": duration,
                    "strategy": strategy.value,
                    "unauthorized_approval_rate":
                        metrics.unauthorized_approval_rate,
                    "legitimate_denial_rate":
                        metrics.legitimate_denial_rate,
                    "mean_exposure_seconds": mean_exposure,
                    "revoked_subjects": len(subject_durations),
                })

    output = Path("results/multiseed_results.csv")
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

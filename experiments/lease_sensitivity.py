
import csv
from pathlib import Path

from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.metrics import calculate_metrics
from consent_sim.runner import ExperimentConfig, run_experiment
from consent_sim.simulator import Strategy
from consent_sim.workload import WorkloadConfig, generate_workload


LEASE_DURATIONS = [10, 30, 60, 120, 300]
SEEDS = range(42, 52)


def main():
    rows = []

    for seed in SEEDS:
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

        for duration in LEASE_DURATIONS:
            config = ExperimentConfig(
                lease_duration=duration,
                one_time_duration=1000,
            )

            for strategy in Strategy:
                results = run_experiment(
                    workload,
                    connectivity,
                    strategy,
                    config,
                )

                metrics = calculate_metrics(results)

                rows.append({
                    "seed": seed,
                    "lease_duration": duration,
                    "strategy": strategy.value,
                    "total_requests": metrics.total_requests,
                    "unauthorized_requests": metrics.unauthorized_requests,
                    "legitimate_requests": metrics.legitimate_requests,
                    "unauthorized_approvals": metrics.unauthorized_approvals,
                    "legitimate_denials": metrics.legitimate_denials,
                    "unauthorized_approval_rate": metrics.unauthorized_approval_rate,
                    "legitimate_denial_rate": metrics.legitimate_denial_rate,
                    "overall_approval_rate": metrics.overall_approval_rate,
                })

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "lease_sensitivity.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} experimental runs")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()

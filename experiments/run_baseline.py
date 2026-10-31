
from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.metrics import calculate_metrics
from consent_sim.runner import ExperimentConfig, run_experiment
from consent_sim.simulator import Strategy
from consent_sim.workload import WorkloadConfig, generate_workload


def main():
    workload = generate_workload(
        WorkloadConfig(
            seed=42,
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

    config = ExperimentConfig(
        lease_duration=60,
        one_time_duration=1000,
    )

    print("CONSENT REVOCATION BENCHMARK")
    print("=" * 60)

    for strategy in Strategy:
        results = run_experiment(
            workload,
            connectivity,
            strategy,
            config,
        )

        metrics = calculate_metrics(results)

        print(f"\nStrategy: {strategy.value}")
        print(f"Total requests: {metrics.total_requests}")
        print(
            "Unauthorized approval rate:",
            metrics.unauthorized_approval_rate,
        )
        print(
            "Legitimate denial rate:",
            metrics.legitimate_denial_rate,
        )
        print(
            "Overall approval rate:",
            metrics.overall_approval_rate,
        )


if __name__ == "__main__":
    main()


from statistics import mean

from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.workload import WorkloadConfig, generate_workload


def main():
    duration = 1000.0

    workload = generate_workload(
        WorkloadConfig(
            seed=42,
            num_subjects=100,
            num_requests=1000,
            duration_seconds=duration,
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

    print("HORIZON-AWARE CONSENT REVOCATION EXPOSURE")
    print("=" * 60)

    for strategy in Strategy:
        trace = run_experiment_with_trace(
            workload,
            connectivity,
            strategy,
            config,
        )

        summary = calculate_horizon_exposure(
            workload,
            trace,
            connectivity,
            strategy,
            observation_end=duration,
        )

        durations = [
            exposure.total_exposure_seconds
            for exposure in summary.subject_exposures
        ]

        print(f"\nStrategy: {strategy.value}")
        print(f"Revoked subjects: {len(durations)}")
        print(
            f"Mean exposure (seconds): "
            f"{mean(durations) if durations else 0:.4f}"
        )
        print(
            f"Maximum exposure (seconds): "
            f"{max(durations) if durations else 0:.4f}"
        )

    print("\nAnalysis completed.")


if __name__ == "__main__":
    main()


from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.validation import validate_exposure_consistency
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

    request_subjects = {
        request.request_id: request.subject_id
        for request in workload.requests
    }

    config = ExperimentConfig(
        lease_duration=60,
        one_time_duration=1000,
    )

    print("EXPOSURE CONSISTENCY VALIDATION")
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

        validation = validate_exposure_consistency(
            trace.results,
            summary,
            request_subjects,
        )

        print(f"\nStrategy: {strategy.value}")
        print(f"Unauthorized approvals: {validation.unauthorized_approvals}")
        print(f"Matched approvals: {validation.matched_approvals}")
        print(f"Mismatches: {len(validation.mismatches)}")
        print(f"Validation passed: {validation.passed}")

        if validation.mismatches:
            for mismatch in validation.mismatches[:5]:
                print("  ", mismatch)


if __name__ == "__main__":
    main()

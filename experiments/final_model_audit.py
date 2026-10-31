
from consent_sim.connectivity import ConnectivitySchedule, Outage
from consent_sim.exposure_horizon import calculate_horizon_exposure
from consent_sim.runner import ExperimentConfig, run_experiment_with_trace
from consent_sim.simulator import Strategy
from consent_sim.workload import RevocationEvent, Workload
from consent_sim.models import GenerationRequest


def make_workload(request_times, revocation_time):
    return Workload(
        subject_ids=["subject_1"],
        revocations=[
            RevocationEvent(
                subject_id="subject_1",
                requester_id="requester_1",
                purpose="FACE_SWAP",
                at_time=revocation_time,
            )
        ],
        requests=[
            GenerationRequest(
                request_id=f"r{i}",
                subject_id="subject_1",
                requester_id="requester_1",
                purpose="FACE_SWAP",
                requested_at=t,
            )
            for i, t in enumerate(request_times)
        ],
    )


def main():
    workload = make_workload(
        request_times=[30, 50, 70, 100, 130],
        revocation_time=45,
    )

    connectivity = ConnectivitySchedule([
        Outage(40, 90),
        Outage(110, 150),
    ])

    config = ExperimentConfig(
        lease_duration=80,
        one_time_duration=200,
    )

    print("FINAL AUTHORIZATION MODEL AUDIT")
    print("=" * 65)

    for strategy in Strategy:
        trace = run_experiment_with_trace(
            workload,
            connectivity,
            strategy,
            config,
        )

        exposure = calculate_horizon_exposure(
            workload,
            trace,
            connectivity,
            strategy,
            observation_end=150,
        )

        print(f"\nStrategy: {strategy.value}")

        for result in trace.results:
            print(
                f"  t={result.generation_time:>5.0f} | "
                f"allowed={str(result.allowed):<5} | "
                f"authorized={str(result.ground_truth_authorized):<5} | "
                f"unauthorized_approval={result.unauthorized_approval}"
            )

        print(
            "  Potential exposure intervals:",
            exposure.subject_exposures[0].exposure_intervals,
        )

        print(
            "  Lease issuance events:",
            [
                (record.issued_at, record.expires_at)
                for record in trace.lease_issuances
            ],
        )


if __name__ == "__main__":
    main()

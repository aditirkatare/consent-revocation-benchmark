
# Research Assumptions and Limitations

## Research scope

This project evaluates consent revocation freshness in a synthetic authorization simulator for AI likeness generation.

It does not implement or test a production AI image-generation service.

## Authorization strategies

1. ONE_TIME: A pre-issued authorization remains usable until expiry, without subsequent registry checks.

2. FAIL_CLOSED: Authorization requires an online registry check. Offline requests are denied.

3. SHORT_LEASE: Authorization is revalidated online. Offline requests may use a cached, unexpired lease.

SHORT_LEASE is therefore a hybrid online-revalidated, offline-capable policy rather than a pure lease-only scheme.

## Initial conditions

- All simulated subjects begin with active consent.
- Initial authorization is provisioned at time zero.
- Network outages affect subsequent online authorization checks.
- Initial provisioning is assumed to occur before network disruption.

## Workload assumptions

- Synthetic requests and revocations are generated from seeded pseudorandom workloads.
- The experiment models one requester and one purpose per subject.
- Each subject has at most one revocation in the generated workload.
- Revocations are processed before requests at identical timestamps.
- A request's authorization decision is evaluated at its simulated generation time.

## Lease assumptions

- Cached leases are trusted simulator objects.
- Cryptographic signatures, token theft, replay, and compromised clients are outside the evaluated model.
- Short leases are renewed on demand when expired, connectivity is available, and consent remains active.
- An offline client may continue using an unexpired cached lease.
- Reconnection alone does not permanently invalidate a cached lease.

## Network assumptions

- Connectivity is represented as binary online/offline state.
- Fixed-outage experiments use predetermined outage intervals.
- Randomized-outage experiments vary outage placement with seeded generation.
- The simulator does not model network latency, packet loss, partial connectivity, or eventual consistency.

## Evaluation metrics

- Unauthorized approval rate: fraction of unauthorized requests that were approved.
- Legitimate denial rate: fraction of authorized requests that were denied.
- Potential exposure: cumulative duration during which revoked authorization could be accepted under the modeled policy.
- Exposure is clipped to the observation horizon.

## Statistical limitations

- Experimental runs are paired by seed.
- Confidence intervals summarize variability across synthetic workloads.
- Fixed-outage experiments do not vary network timing.
- Randomized-outage experiments introduce outage-timing variability.
- Results should not be generalized directly to deployed AI systems.

## Threats to validity

- Synthetic workload distributions may not resemble real authorization traffic.
- Outcomes depend on lease duration, revocation timing, request timing, and network outages.
- The simulator assumes a trusted consent registry.
- The experiments do not measure real generation latency, infrastructure overhead, or model-level enforcement.
- Security properties are limited to the authorization policies represented in the simulator.

## Interpretation

The experiments characterize security–availability trade-offs under explicitly stated assumptions.

They do not establish a universally optimal lease duration or guarantee prevention of unauthorized likeness generation.

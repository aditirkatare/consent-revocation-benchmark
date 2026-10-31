
# Experimental Results

## Project

Consent Revocation Freshness in AI Likeness Generation:
Security–Availability Trade-offs Under Intermittent Connectivity

## Experimental setup

The benchmark compares three authorization strategies:

1. ONE_TIME: Cached authorization without subsequent revocation checks.
2. FAIL_CLOSED: Online revalidation required for authorization.
3. SHORT_LEASE: Online revalidation with offline use of unexpired cached leases.

The primary experiment uses:

- 100 simulated subjects
- 1,000 generation requests per run
- 30 random seeds
- 1,000-second observation horizon
- 30% subject revocation probability
- Lease durations of 10, 30, 60, 120, and 300 seconds
- Three predefined network outages

## Primary results

| Strategy | Lease duration | Unauthorized approval rate | Legitimate denial rate | Mean exposure |
|---|---:|---:|---:|---:|
| ONE_TIME | 1000 s | 100.000% | 0.000% | 510.593 s |
| FAIL_CLOSED | N/A | 0.000% | 33.878% | 0.000 s |
| SHORT_LEASE | 10 s | 0.000% | 33.740% | 0.014 s |
| SHORT_LEASE | 30 s | 0.053% | 32.918% | 0.251 s |
| SHORT_LEASE | 60 s | 0.349% | 30.513% | 1.363 s |
| SHORT_LEASE | 120 s | 1.320% | 23.855% | 8.221 s |
| SHORT_LEASE | 300 s | 10.704% | 5.797% | 54.699 s |

Values represent means across 30 synthetic seeds.

## Paired comparison

Compared with FAIL_CLOSED, SHORT_LEASE at 60 seconds produced:

- 0.349 percentage points more unauthorized approvals.
- 3.365 percentage points fewer legitimate denials.
- 1.363 seconds more mean potential exposure.

At 300 seconds, SHORT_LEASE produced:

- 10.704 percentage points more unauthorized approvals.
- 28.081 percentage points fewer legitimate denials.
- 54.699 seconds more mean potential exposure.

## Randomized outage sensitivity

Randomized outage placement produced the same broad trade-off, although exact rates differed from fixed-outage experiments.

At a 300-second lease duration:

| Outage duration | Unauthorized approval rate | Legitimate denial rate |
|---|---:|---:|
| 30 s | 1.63% | 2.44% |
| 60 s | 3.21% | 5.67% |
| 120 s | 5.97% | 13.07% |
| 180 s | 7.15% | 22.68% |

## Validation

- 141 automated tests passed.
- Authorization decisions matched the expected final audit scenario.
- Observed unauthorized approvals were contained within calculated potential exposure intervals.
- Experiments were conducted using deterministic random seeds.

## Interpretation

The simulator demonstrates a security–availability trade-off between stale authorization acceptance and legitimate request denial.

Shorter leases reduce potential post-revocation exposure but may deny more legitimate requests during outages.

Longer leases improve offline availability while increasing stale-authorization risk.

These conclusions are specific to the synthetic workloads, authorization assumptions, and network schedules evaluated.

## Limitations

- No production AI generation system was tested.
- Consent records and authorization leases are simulated.
- Cryptographic token validation and adversarial clients are outside scope.
- Network latency and partial connectivity are not modeled.
- Statistical intervals describe synthetic run-to-run variability, not deployment uncertainty.
- No universally optimal lease duration is established.

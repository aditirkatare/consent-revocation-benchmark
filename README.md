
# Consent Revocation Benchmark

A reproducible Python simulation benchmark evaluating consent revocation freshness in AI likeness generation under intermittent network connectivity.

## Research question

How do authorization lease duration and network availability affect post-revocation authorization risk and legitimate request availability?

## Authorization strategies

| Strategy | Behavior |
|---|---|
| One-time | Uses cached authorization until expiry |
| Fail-closed | Requires online consent revalidation |
| Short-lease | Revalidates online and permits unexpired cached leases offline |

## Evaluation metrics

- Unauthorized approval rate
- Legitimate denial rate
- Potential post-revocation exposure duration
- Overall approval rate

## Experimental design

- 100 synthetic subjects
- 1,000 requests per run
- 30 random seeds
- 1,000-second observation horizon
- Fixed and randomized network outage experiments
- Lease duration sensitivity analysis
- Paired statistical comparisons

## Key findings

The synthetic benchmark identifies a security–availability trade-off.

With 60-second short leases, the mean unauthorized approval rate was 0.349%, while legitimate denial was 30.513%.

With 300-second short leases, unauthorized approvals increased to 10.704%, while legitimate denial decreased to 5.797%.

These findings describe modeled authorization behavior and should not be interpreted as measurements of deployed AI systems.

## Installation

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip install matplotlib
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Run experiments

```powershell
.\.venv\Scripts\python.exe experiments\multiseed_analysis.py
.\.venv\Scripts\python.exe experiments\paired_analysis.py
.\.venv\Scripts\python.exe experiments\outage_sensitivity.py
.\.venv\Scripts\python.exe experiments\randomized_outage_analysis.py
```

## Generate figures

```powershell
.\.venv\Scripts\python.exe experiments\generate_figures.py
```

## Documentation

- [Research assumptions](docs/research_assumptions.md)
- [Experimental results](docs/research_results.md)
- [Reproducibility guide](docs/reproducibility.md)

## Research scope

This repository provides a synthetic authorization benchmark, not a production AI likeness-generation system.

The project does not claim to prevent deepfakes or enforce consent at the model level.

## License

No license has been selected yet.

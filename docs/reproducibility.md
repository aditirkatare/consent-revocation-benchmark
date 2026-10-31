
# Reproducibility Guide

## Environment

- Python 3.10 or newer
- Windows PowerShell or compatible terminal
- Project installed in editable mode

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip install matplotlib
```

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Run experiments

```powershell
.\.venv\Scripts\python.exe experiments\run_baseline.py
.\.venv\Scripts\python.exe experiments\lease_sensitivity.py
.\.venv\Scripts\python.exe experiments\multiseed_analysis.py
.\.venv\Scripts\python.exe experiments\paired_analysis.py
.\.venv\Scripts\python.exe experiments\outage_sensitivity.py
.\.venv\Scripts\python.exe experiments\randomized_outage_analysis.py
```

## Generate summaries

```powershell
.\.venv\Scripts\python.exe experiments\multiseed_summary.py
.\.venv\Scripts\python.exe experiments\outage_summary.py
.\.venv\Scripts\python.exe experiments\randomized_outage_summary.py
```

## Generate figures

```powershell
.\.venv\Scripts\python.exe experiments\generate_figures.py
```

## Validate exposure consistency

```powershell
.\.venv\Scripts\python.exe experiments\validate_benchmark.py
```

## Outputs

- CSV experiment results: `results/`
- Figures: `results/figures/`
- Research assumptions: `docs/research_assumptions.md`

## Reproducibility notes

Experiments use fixed random seeds and deterministic simulation logic.

Results should be regenerated using the documented commands and compared before publication.

The code, Python version, and dependency versions should be recorded with the final release.


import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


RESULTS = Path("results")
FIGURES = RESULTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def read_csv(filename):
    with (RESULTS / filename).open(
        newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def plot_lease_tradeoff():
    rows = read_csv("multiseed_results.csv")
    groups = defaultdict(list)

    for row in rows:
        if row["strategy"] == "short_lease":
            groups[int(row["lease_duration"])].append(row)

    durations = sorted(groups)

    unauthorized = [
        mean(float(r["unauthorized_approval_rate"]) for r in groups[d]) * 100
        for d in durations
    ]
    denials = [
        mean(float(r["legitimate_denial_rate"]) for r in groups[d]) * 100
        for d in durations
    ]

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.plot(durations, unauthorized, marker="o",
            label="Unauthorized approval")
    ax.plot(durations, denials, marker="s",
            label="Legitimate denial")

    ax.set_xlabel("Lease duration (seconds)")
    ax.set_ylabel("Rate (%)")
    ax.set_title("Security–Availability Trade-off")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()

    fig.savefig(FIGURES / "lease_tradeoff.pdf")
    fig.savefig(FIGURES / "lease_tradeoff.png", dpi=300)
    plt.close(fig)


def plot_exposure():
    rows = read_csv("multiseed_results.csv")
    groups = defaultdict(list)

    for row in rows:
        if row["strategy"] == "short_lease":
            groups[int(row["lease_duration"])].append(row)

    durations = sorted(groups)
    exposure = [
        mean(float(r["mean_exposure_seconds"]) for r in groups[d])
        for d in durations
    ]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(durations, exposure, marker="o")

    ax.set_xlabel("Lease duration (seconds)")
    ax.set_ylabel("Mean exposure (seconds)")
    ax.set_title("Post-Revocation Exposure")
    ax.grid(alpha=0.25)
    fig.tight_layout()

    fig.savefig(FIGURES / "exposure.pdf")
    fig.savefig(FIGURES / "exposure.png", dpi=300)
    plt.close(fig)


def plot_outage_comparison():
    fixed = read_csv("outage_sensitivity.csv")
    randomized = read_csv("randomized_outages.csv")

    fig, ax = plt.subplots(figsize=(7, 4.5))

    for dataset, label in [
        (fixed, "Fixed outages"),
        (randomized, "Randomized outages"),
    ]:
        groups = defaultdict(list)

        for row in dataset:
            if (
                row["strategy"] == "short_lease"
                and int(row["lease_duration"]) == 300
                and int(row["outage_duration"]) > 0
            ):
                groups[int(row["outage_duration"])].append(
                    float(row["unauthorized_approval_rate"])
                )

        durations = sorted(groups)
        rates = [
            mean(groups[d]) * 100
            for d in durations
        ]

        ax.plot(durations, rates, marker="o", label=label)

    ax.set_xlabel("Outage duration (seconds)")
    ax.set_ylabel("Unauthorized approval rate (%)")
    ax.set_title("Sensitivity to Outage Timing")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()

    fig.savefig(FIGURES / "outage_comparison.pdf")
    fig.savefig(FIGURES / "outage_comparison.png", dpi=300)
    plt.close(fig)


def main():
    plot_lease_tradeoff()
    plot_exposure()
    plot_outage_comparison()

    print("Generated 3 figures in results/figures/")
    print("Each figure is available as PDF and PNG.")


if __name__ == "__main__":
    main()

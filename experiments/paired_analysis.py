
import csv
from collections import defaultdict
from math import sqrt
from pathlib import Path
from statistics import mean, stdev


INPUT = Path("results/multiseed_results.csv")
OUTPUT = Path("results/paired_comparisons.csv")

METRICS = [
    "unauthorized_approval_rate",
    "legitimate_denial_rate",
    "mean_exposure_seconds",
]

T_CRITICAL_29 = 2.04523


def paired_estimate(differences):
    if len(differences) != 30:
        raise ValueError("Expected exactly 30 paired seeds")

    average = mean(differences)
    margin = T_CRITICAL_29 * stdev(differences) / sqrt(30)

    return average, average - margin, average + margin


def main():
    with INPUT.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    groups = defaultdict(dict)

    for row in rows:
        key = (int(row["lease_duration"]), int(row["seed"]))
        strategy = row["strategy"]

        if strategy in groups[key]:
            raise ValueError(f"Duplicate record: {key}, {strategy}")

        groups[key][strategy] = row

    output_rows = []

    for duration in [10, 30, 60, 120, 300]:
        pairs = [
            groups[(duration, seed)]
            for seed in range(100, 130)
        ]

        for metric in METRICS:
            differences = []

            for pair in pairs:
                short = pair["short_lease"][metric]
                closed = pair["fail_closed"][metric]

                if short == "" or closed == "":
                    raise ValueError(
                        f"Missing {metric} in paired comparison"
                    )

                differences.append(float(short) - float(closed))

            average, lower, upper = paired_estimate(differences)

            output_rows.append({
                "lease_duration": duration,
                "metric": metric,
                "paired_seeds": 30,
                "mean_difference": average,
                "ci_lower": lower,
                "ci_upper": upper,
            })

    OUTPUT.parent.mkdir(exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(output_rows[0]),
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print("PAIRED COMPARISON: SHORT_LEASE - FAIL_CLOSED")
    print("=" * 65)

    for row in output_rows:
        multiplier = (
            100 if row["metric"].endswith("_rate") else 1
        )
        unit = "percentage points" if multiplier == 100 else "seconds"

        print(
            f"{row['lease_duration']:>3}s | "
            f"{row['metric']}: "
            f"{row['mean_difference'] * multiplier:+.3f} "
            f"{unit} "
            f"[{row['ci_lower'] * multiplier:+.3f}, "
            f"{row['ci_upper'] * multiplier:+.3f}]"
        )

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()

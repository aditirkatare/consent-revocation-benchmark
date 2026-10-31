
import csv
from collections import defaultdict
from pathlib import Path

from consent_sim.statistics import estimate_mean


def main():
    with Path("results/multiseed_results.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    grouped = defaultdict(dict)

    for row in rows:
        key = (row["strategy"], int(row["lease_duration"]))
        seed = int(row["seed"])

        if seed in grouped[key]:
            raise ValueError("Duplicate seed within experimental group")

        grouped[key][seed] = row

    print("30-SEED EXPERIMENTAL SUMMARY")
    print("=" * 75)

    for (strategy, duration), by_seed in sorted(grouped.items()):
        print(f"\n{strategy} | lease duration: {duration}s")

        if len(by_seed) != 30:
            raise ValueError("Expected exactly 30 distinct seeds")

        for column, label, multiplier in [
            ("unauthorized_approval_rate", "Unauthorized approval", 100),
            ("legitimate_denial_rate", "Legitimate denial", 100),
            ("mean_exposure_seconds", "Mean exposure", 1),
        ]:
            values = [
                float(row[column])
                for row in by_seed.values()
                if row[column] != ""
            ]

            if len(values) != 30:
                print(f"  {label}: insufficient observations")
                continue

            estimate = estimate_mean(values)

            unit = "%" if multiplier == 100 else "s"

            print(
                f"  {label}: "
                f"{estimate.mean * multiplier:.3f}{unit} "
                f"(95% CI: "
                f"{estimate.ci_lower * multiplier:.3f} to "
                f"{estimate.ci_upper * multiplier:.3f}{unit})"
            )


if __name__ == "__main__":
    main()

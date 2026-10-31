
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


def main():
    with Path("results/outage_sensitivity.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    groups = defaultdict(list)

    for row in rows:
        key = (
            int(row["outage_duration"]),
            int(row["lease_duration"]),
            row["strategy"],
        )
        groups[key].append(row)

    print("OUTAGE SENSITIVITY SUMMARY")
    print("=" * 75)

    for (outage, lease, strategy), group in sorted(groups.items()):
        unauthorized = [
            float(row["unauthorized_approval_rate"])
            for row in group
            if row["unauthorized_approval_rate"] != ""
        ]

        denied = [
            float(row["legitimate_denial_rate"])
            for row in group
            if row["legitimate_denial_rate"] != ""
        ]

        exposure = [
            float(row["mean_exposure_seconds"])
            for row in group
            if row["mean_exposure_seconds"] != ""
        ]

        print(
            f"Outage={outage:>3}s | "
            f"Lease={lease:>3}s | "
            f"{strategy:<12} | "
            f"Unauthorized={mean(unauthorized) * 100:>6.2f}% | "
            f"Denial={mean(denied) * 100:>6.2f}% | "
            f"Exposure={mean(exposure):>7.2f}s"
        )


if __name__ == "__main__":
    main()

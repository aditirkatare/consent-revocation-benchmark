
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


def main():
    input_file = Path("results/lease_sensitivity.csv")

    with input_file.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    grouped = defaultdict(list)

    for row in rows:
        key = (
            row["strategy"],
            int(row["lease_duration"]),
        )
        grouped[key].append(row)

    print(
        f"{'Strategy':<15}"
        f"{'Lease':>8}"
        f"{'Unauthorized %':>18}"
        f"{'Legitimate denial %':>22}"
    )
    print("-" * 65)

    for (strategy, duration), group in sorted(grouped.items()):
        unauthorized_rates = [
            float(row["unauthorized_approval_rate"])
            for row in group
            if row["unauthorized_approval_rate"] != ""
        ]

        denial_rates = [
            float(row["legitimate_denial_rate"])
            for row in group
            if row["legitimate_denial_rate"] != ""
        ]

        unauthorized_mean = (
            mean(unauthorized_rates) * 100
            if unauthorized_rates else float("nan")
        )

        denial_mean = (
            mean(denial_rates) * 100
            if denial_rates else float("nan")
        )

        print(
            f"{strategy:<15}"
            f"{duration:>8}"
            f"{unauthorized_mean:>17.2f}%"
            f"{denial_mean:>21.2f}%"
        )


if __name__ == "__main__":
    main()

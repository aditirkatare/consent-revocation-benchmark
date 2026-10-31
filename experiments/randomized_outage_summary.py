
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

INPUT = Path("results/randomized_outages.csv")
OUTPUT = Path("results/randomized_outage_summary.csv")


def main():
    with INPUT.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    groups = defaultdict(dict)

    for row in rows:
        key = (
            int(row["outage_duration"]),
            int(row["lease_duration"]),
            row["strategy"],
        )
        seed = int(row["seed"])

        if seed in groups[key]:
            raise ValueError(f"Duplicate seed: {key}, {seed}")

        groups[key][seed] = row

    summaries = []

    for (outage, lease, strategy), by_seed in sorted(groups.items()):
        if len(by_seed) != 30:
            raise ValueError("Expected 30 independent seeds")

        unauthorized = mean(
            float(row["unauthorized_approval_rate"])
            for row in by_seed.values()
        )

        denial = mean(
            float(row["legitimate_denial_rate"])
            for row in by_seed.values()
        )

        summaries.append({
            "outage_duration": outage,
            "lease_duration": lease,
            "strategy": strategy,
            "seeds": len(by_seed),
            "unauthorized_approval_rate": unauthorized,
            "legitimate_denial_rate": denial,
        })

    OUTPUT.parent.mkdir(exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(summaries[0]),
        )
        writer.writeheader()
        writer.writerows(summaries)

    print("RANDOMIZED OUTAGE SUMMARY")
    print("=" * 80)

    for row in summaries:
        print(
            f"Outage={row['outage_duration']:>3}s | "
            f"Lease={row['lease_duration']:>3}s | "
            f"{row['strategy']:<12} | "
            f"Unauthorized={row['unauthorized_approval_rate'] * 100:>6.2f}% | "
            f"Denial={row['legitimate_denial_rate'] * 100:>6.2f}%"
        )

    print(f"\nSaved {len(summaries)} summary rows to {OUTPUT}")


if __name__ == "__main__":
    main()

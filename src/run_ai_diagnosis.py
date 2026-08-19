import csv
import json
import time
from pathlib import Path

from ai_diagnosis import diagnose_case


CASES_FILE = Path("datasets/cases.csv")
OUTPUT_FILE = Path("datasets/ai_diagnosis_results.csv")


FIELDS = [
    "case_id",
    "root_cause",
    "confidence",
    "evidence",
    "osi_layer",
    "concept",
    "next_command",
    "fix_steps",
    "human_review_required",
    "status"
]


def load_cases():
    with CASES_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def load_existing_results():
    if not OUTPUT_FILE.exists():
        return {}

    with OUTPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        rows = csv.DictReader(file)

        return {
            row["case_id"]: row
            for row in rows
            if row.get("status") == "SUCCESS"
        }


def save_results(results):
    ordered_results = []

    for case_id in sorted(
        results.keys(),
        key=lambda x: int(x.split("-")[1])
    ):
        ordered_results.append(results[case_id])

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS
        )

        writer.writeheader()
        writer.writerows(ordered_results)


def main():

    cases = load_cases()
    existing = load_existing_results()

    print()
    print("NetSage AI - Resumable Batch Diagnosis")
    print("=======================================")
    print(f"Total cases       : {len(cases)}")
    print(f"Already completed : {len(existing)}")
    print(
        f"Remaining         : "
        f"{len(cases) - len(existing)}"
    )
    print()

    results = dict(existing)

    for index, case in enumerate(cases, start=1):

        case_id = case["case_id"]

        # Never waste an API request on a successful case.
        if case_id in results:
            print(
                f"[{index}/{len(cases)}] "
                f"{case_id} -> SKIPPED (already successful)"
            )
            continue

        print(
            f"[{index}/{len(cases)}] "
            f"Diagnosing {case_id}...",
            end=" "
        )

        try:

            diagnosis = diagnose_case(case)

            results[case_id] = {
                "case_id": case_id,
                "root_cause": diagnosis["root_cause"],
                "confidence": diagnosis["confidence"],
                "evidence": json.dumps(
                    diagnosis["evidence"],
                    ensure_ascii=False
                ),
                "osi_layer": diagnosis["osi_layer"],
                "concept": diagnosis["concept"],
                "next_command": diagnosis["next_command"],
                "fix_steps": json.dumps(
                    diagnosis["fix_steps"],
                    ensure_ascii=False
                ),
                "human_review_required":
                    diagnosis["human_review_required"],
                "status": "SUCCESS"
            }

            # Save immediately after every successful case.
            save_results(results)

            print("SUCCESS")

        except Exception as error:

            print("ERROR")

            error_message = str(error)

            print(f"   {error_message}")

            # Don't permanently record API failures as successful results.
            # This allows the script to retry them later.

            if "429" in error_message:
                print()
                print(
                    "Gemini quota/rate limit detected."
                )
                print(
                    "Stopping batch to avoid wasting requests."
                )
                break

        # Small delay between API calls.
        time.sleep(2)

    successful = sum(
        1
        for result in results.values()
        if result.get("status") == "SUCCESS"
    )

    remaining = len(cases) - successful

    print()
    print("Batch Diagnosis Status")
    print("======================")
    print(f"Total cases : {len(cases)}")
    print(f"Successful  : {successful}")
    print(f"Remaining   : {remaining}")
    print(f"Output      : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
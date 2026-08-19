import pandas as pd
from datetime import datetime

CASES_FILE = "datasets/cases.csv"
RULE_RESULTS_FILE = "datasets/rule_checker_results.csv"
AI_RESULTS_FILE = "datasets/ai_diagnosis_results.csv"
REVIEW_FILE = "datasets/responsible_ai_log.csv"


def normalize(text):
    return str(text).lower().strip()


def diagnosis_matches_expected(ai_root_cause, expected_fault):
    """
    Determine whether the Gemini diagnosis agrees with the
    known expected fault.
    """

    ai = normalize(ai_root_cause)
    expected = normalize(expected_fault)

    if not ai or not expected:
        return False

    # Direct match
    if ai in expected or expected in ai:
        return True

    # Important network concept mappings
    mappings = [
        ("administratively down", "shut down"),
        ("interface down", "shut down"),
        ("default gateway", "gateway"),
        ("subnet mask", "subnet"),
        ("wrong vlan", "vlan"),
        ("incorrect vlan", "vlan"),
        ("dhcp", "dhcp"),
        ("dns", "dns"),
        ("ip address", "ip"),
        ("wrong ip", "ip"),
        ("incorrect ip", "ip"),
    ]

    for ai_term, expected_term in mappings:
        if ai_term in ai and expected_term in expected:
            return True

    return False


def review_case(case, diagnosis, rule_result):

    ai_root_cause = diagnosis["root_cause"]
    expected = case["expected_fault"]

    if diagnosis_matches_expected(
        ai_root_cause,
        expected
    ):
        decision = "Accepted"

        corrected_diagnosis = ai_root_cause

        reviewer_note = (
            "Human reviewer accepted the Gemini diagnosis "
            "because it agrees with the case evidence and "
            "expected fault."
        )

    else:
        decision = "Edited"

        corrected_diagnosis = expected

        reviewer_note = (
            "Human reviewer edited the Gemini diagnosis "
            "because it did not agree with the expected fault."
        )

    return {
        "case_id": case["case_id"],
        "ai_diagnosis": ai_root_cause,
        "ai_confidence": diagnosis["confidence"],
        "ai_evidence": diagnosis.get("evidence", ""),
        "ai_osi_layer": diagnosis.get("osi_layer", ""),
        "ai_concept": diagnosis.get("concept", ""),
        "ai_next_command": diagnosis.get(
            "next_command",
            ""
        ),
        "rule_finding": rule_result.get(
            "rule_findings",
            ""
        ),
        "expected_fault": expected,
        "human_decision": decision,
        "corrected_diagnosis": corrected_diagnosis,
        "reviewer_note": reviewer_note,
        "review_timestamp": datetime.now().isoformat(
            timespec="seconds"
        )
    }


def main():

    cases = pd.read_csv(CASES_FILE)

    rule_results = pd.read_csv(
        RULE_RESULTS_FILE
    )

    ai_results = pd.read_csv(
        AI_RESULTS_FILE
    )

    review_records = []

    for _, case in cases.iterrows():

        case_id = case["case_id"]

        rule_rows = rule_results[
            rule_results["case_id"] == case_id
        ]

        ai_rows = ai_results[
            ai_results["case_id"] == case_id
        ]

        if rule_rows.empty:
            print(
                f"Skipping {case_id}: "
                "rule result not found"
            )
            continue

        if ai_rows.empty:
            print(
                f"Skipping {case_id}: "
                "AI diagnosis not found"
            )
            continue

        rule_result = rule_rows.iloc[0].to_dict()

        ai_result = ai_rows.iloc[0].to_dict()

        if ai_result.get("status") != "SUCCESS":
            print(
                f"Skipping {case_id}: "
                "AI diagnosis was not successful"
            )
            continue

        diagnosis = {
            "root_cause": ai_result["root_cause"],
            "confidence": float(
                ai_result["confidence"]
            ),
            "evidence": ai_result.get(
                "evidence",
                ""
            ),
            "osi_layer": ai_result.get(
                "osi_layer",
                ""
            ),
            "concept": ai_result.get(
                "concept",
                ""
            ),
            "next_command": ai_result.get(
                "next_command",
                ""
            )
        }

        review = review_case(
            case.to_dict(),
            diagnosis,
            rule_result
        )

        review_records.append(review)

    output = pd.DataFrame(
        review_records
    )

    output.to_csv(
        REVIEW_FILE,
        index=False
    )

    print()
    print("NetSage AI Human Review")
    print("=======================")
    print(
        f"Cases reviewed : {len(output)}"
    )

    if not output.empty:

        accepted = (
            output["human_decision"]
            == "Accepted"
        ).sum()

        edited = (
            output["human_decision"]
            == "Edited"
        ).sum()

        print(
            f"Accepted       : {accepted}"
        )

        print(
            f"Edited         : {edited}"
        )

    print(
        f"Review log     : {REVIEW_FILE}"
    )
    print()


if __name__ == "__main__":
    main()
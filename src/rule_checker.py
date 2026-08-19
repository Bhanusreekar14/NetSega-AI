import pandas as pd
import re

INPUT_FILE = "datasets/cases.csv"
OUTPUT_FILE = "datasets/rule_checker_results.csv"


def check_evidence(row):
    evidence = str(row["show_outputs"]).lower()
    findings = []

    # 1. Duplicate IP
    if "duplicate" in evidence and "ip" in evidence:
        findings.append("Possible duplicate IP address")

    # 2. Wrong subnet mask
    if "subnet mask" in evidence:
        masks = re.findall(
            r"(?:255\.){3}\d+",
            evidence
        )

        if len(set(masks)) > 1:
            findings.append("Multiple subnet masks detected")

    # 3. Gateway mismatch
    if "default gateway" in evidence:
        if "wrong" in evidence or "incorrect" in evidence:
            findings.append("Possible default gateway mismatch")

    # 4. Interface down
    if (
        "administratively down" in evidence
        or "interface down" in evidence
        or "status down" in evidence
    ):
        findings.append("Interface may be down")

    # 5. VLAN issue
    if (
        "vlan" in evidence
        and (
            "missing" in evidence
            or "wrong" in evidence
            or "incorrect" in evidence
        )
    ):
        findings.append("Possible VLAN configuration issue")

    # 6. Missing route
    if (
        "routing table" in evidence
        or "no route" in evidence
        or "route missing" in evidence
    ):
        findings.append("Possible missing route")

    # 7. DHCP
    if (
        "dhcp" in evidence
        and (
            "disabled" in evidence
            or "unavailable" in evidence
            or "0.0.0.0" in evidence
        )
    ):
        findings.append("Possible DHCP configuration/service issue")

    # 8. DNS
    if (
        "dns" in evidence
        and (
            "timeout" in evidence
            or "timed out" in evidence
            or "disabled" in evidence
        )
    ):
        findings.append("Possible DNS configuration/service issue")

    # 9. FTP
    if (
        "ftp" in evidence
        and (
            "550" in evidence
            or "permission denied" in evidence
            or "peer reset" in evidence
        )
    ):
        findings.append("Possible FTP service or permission issue")

    # 10. HTTP
    if (
        "http" in evidence
        and (
            "connection refused" in evidence
            or "service unavailable" in evidence
            or "disabled" in evidence
        )
    ):
        findings.append("Possible HTTP service issue")

    return findings


def main():
    df = pd.read_csv(INPUT_FILE)

    results = []

    for _, row in df.iterrows():

        findings = check_evidence(row)

        results.append({
            "case_id": row["case_id"],
            "rule_findings": " | ".join(findings)
            if findings else "No deterministic issue detected",
            "issues_found": len(findings),
            "status": "ISSUE_FOUND"
            if findings
            else "NO_RULE_ISSUE"
        })

    output = pd.DataFrame(results)

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("NetSage AI Rule Checker")
    print("======================")
    print(f"Cases processed : {len(df)}")
    print(f"Issues detected : {(output['issues_found'] > 0).sum()}")
    print(f"Results saved   : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
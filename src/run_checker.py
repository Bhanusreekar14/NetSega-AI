import pandas as pd
import re

INPUT_FILE = "datasets/cases.csv"
OUTPUT_FILE = "datasets/rule_checker_results.csv"

def normalize(text):
    """Normalize text for concept matching."""
    text = str(text).lower()

    replacements = {
        "administratively shut down": "interface down",
        "administratively down": "interface down",
        "incorrect default gateway": "gateway",
        "wrong default gateway": "gateway",
        "default gateway mismatch": "gateway",
        "incorrect subnet mask": "subnet mask",
        "wrong subnet mask": "subnet mask",
        "wrong ip subnet": "ip address",
        "incorrect ip": "ip address",
        "wrong ip": "ip address",
        "dhcp pool": "dhcp",
        "dhcp server unavailable": "dhcp",
        "dhcp service disabled": "dhcp",
        "wrong vlan": "vlan",
        "incorrect vlan": "vlan",
        "vlan mismatch": "vlan",
        "dns server": "dns",
        "dns service": "dns",
        "ftp service": "ftp",
        "ftp permission": "ftp",
        "ftp credentials": "ftp",
        "http service": "http",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

def detect_concepts(text):
    """
    Detect network concepts from evidence text.
    """
    text = normalize(text)

    concepts = []

    patterns = {
        "interface": [
            "interface down",
            "interface shutdown",
            "port down",
            "link down"
        ],

        "gateway": [
            "gateway"
        ],

        "ip": [
            "ip address",
            "ip subnet",
            "ipv4"
        ],

        "subnet": [
            "subnet mask",
            "subnet"
        ],

        "vlan": [
            "vlan"
        ],

        "dhcp": [
            "dhcp",
            "0.0.0.0"
        ],

        "dns": [
            "dns",
            "nslookup",
            "name resolution"
        ],

        "routing": [
            "route",
            "routing",
            "routing table"
        ],

        "acl": [
            "acl",
            "access-list"
        ],

        "nat": [
            "nat",
            "translation"
        ],

        "ftp": [
            "ftp",
            "550",
            "permission denied",
            "peer reset"
        ],

        "http": [
            "http",
            "web server",
            "connection refused"
        ],

        "wireless": [
            "wireless",
            "wifi",
            "wi-fi",
            "ssid"
        ]
    }

    for concept, keywords in patterns.items():
        if any(keyword in text for keyword in keywords):
            concepts.append(concept)

    return concepts

def check_evidence(row):
    """
    Analyze show/test output and return deterministic findings.
    """
    evidence = str(row["show_outputs"])

    detected_concepts = detect_concepts(evidence)

    findings = []

    concept_messages = {
        "interface": "Interface/port status issue detected",
        "gateway": "Default gateway issue detected",
        "ip": "IP addressing issue detected",
        "subnet": "Subnet configuration issue detected",
        "vlan": "VLAN configuration issue detected",
        "dhcp": "DHCP issue detected",
        "dns": "DNS issue detected",
        "routing": "Routing issue detected",
        "acl": "ACL issue detected",
        "nat": "NAT issue detected",
        "ftp": "FTP issue detected",
        "http": "HTTP issue detected",
        "wireless": "Wireless configuration issue detected"
    }

    for concept in detected_concepts:
        findings.append(concept_messages[concept])

    return findings, detected_concepts

def expected_concepts(expected_fault, concept_tag):
    """
    Determine the expected network concepts using both
    expected_fault and concept_tag.
    """
    text = f"{expected_fault} {concept_tag}"
    return set(detect_concepts(text))

def compare_expected(expected_fault, concept_tag, detected_concepts):
    """
    Compare expected concepts with detected concepts.
    """

    expected = expected_concepts(
        expected_fault,
        concept_tag
    )

    detected = set(detected_concepts)

    if not detected:
        return "NO_DETECTION"

    # Exact concept overlap
    if expected.intersection(detected):
        return "MATCH"

    # Related concepts
    related = {
        "interface": {"interface"},
        "gateway": {"gateway"},
        "ip": {"ip", "subnet"},
        "subnet": {"subnet", "ip"},
        "vlan": {"vlan"},
        "dhcp": {"dhcp"},
        "dns": {"dns"},
        "routing": {"routing"},
        "acl": {"acl"},
        "nat": {"nat"},
        "ftp": {"ftp"},
        "http": {"http"},
        "wireless": {"wireless"}
    }

    for expected_concept in expected:
        if expected_concept in related:
            if detected.intersection(
                related[expected_concept]
            ):
                return "MATCH"

    return "MISMATCH"

def main():

    df = pd.read_csv(INPUT_FILE)

    results = []

    for _, row in df.iterrows():

        findings, detected_concepts = check_evidence(row)

        comparison = compare_expected(
            row["expected_fault"],
            row["concept_tag"],
            detected_concepts
        )

        results.append({
            "case_id": row["case_id"],
            "expected_fault": row["expected_fault"],
            "concept_tag": row["concept_tag"],
            "detected_concepts": ", ".join(
                detected_concepts
            ) if detected_concepts else "None",
            "rule_findings": " | ".join(
                findings
            ) if findings else "No deterministic issue detected",
            "issues_found": len(findings),
            "comparison": comparison,
            "status": (
                "ISSUE_FOUND"
                if findings
                else "NO_RULE_ISSUE"
            )
        })

    output = pd.DataFrame(results)

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    matches = (
        output["comparison"] == "MATCH"
    ).sum()

    mismatches = (
        output["comparison"] == "MISMATCH"
    ).sum()

    no_detection = (
        output["comparison"] == "NO_DETECTION"
    ).sum()

    print()
    print("NetSage AI Rule Checker")
    print("=======================")
    print(f"Cases processed : {len(df)}")
    print(
        f"Rule issues     : "
        f"{(output['issues_found'] > 0).sum()}"
    )
    print(f"Matches         : {matches}")
    print(f"Mismatches      : {mismatches}")
    print(f"No detection    : {no_detection}")
    print(
        f"Results saved   : {OUTPUT_FILE}"
    )
    print()

if __name__ == "__main__":
    main()

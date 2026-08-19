import json
import os
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
PROMPT_FILE = PROJECT_ROOT / "prompts" / "diagnose_prompt.md"

MODEL = "gemini-3.6-flash"
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)


def load_api_key():
    """Read GEMINI_API_KEY from the project's .env file."""

    if not ENV_FILE.exists():
        raise FileNotFoundError(".env file not found in project root.")

    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("GEMINI_API_KEY="):
            key = line.split("=", 1)[1].strip()

            if key:
                return key

    raise ValueError("GEMINI_API_KEY is missing from .env")


def load_system_prompt():
    """Load the project's diagnosis prompt."""

    if not PROMPT_FILE.exists():
        raise FileNotFoundError("prompts/diagnose_prompt.md not found.")

    return PROMPT_FILE.read_text()


def build_case_prompt(case):
    """Combine the project prompt with the actual network case."""

    system_prompt = load_system_prompt()

    case_information = f"""

## CASE TO ANALYZE

Case ID:
{case.get("case_id", "")}

Symptom:
{case.get("symptom", "")}

Topology:
{case.get("topology_note", "")}

Show/Test Output:
{case.get("show_outputs", "")}

Concept Tag:
{case.get("concept_tag", "")}

OSI Layer:
{case.get("osi_layer", "")}

IMPORTANT:
Use only the supplied evidence.
Do not invent command output.
Do not reveal or use the expected_fault field.
Return ONLY valid JSON.
"""

    return system_prompt + case_information


def call_gemini(prompt):
    """Send the diagnosis prompt to Gemini using urllib."""

    api_key = load_api_key()
    url = f"{API_URL}?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {error.code}: {error_body}")

    except urllib.error.URLError as error:
        raise RuntimeError(f"Gemini connection failed: {error.reason}")


def extract_text(api_response):
    """Extract generated text from Gemini response."""

    try:
        return api_response["candidates"][0]["content"]["parts"][0]["text"]

    except (KeyError, IndexError, TypeError):
        raise ValueError("Unexpected Gemini response format.")


def parse_diagnosis(text):
    """Convert Gemini's JSON response into a Python dictionary."""

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError as error:
        raise ValueError(f"Gemini returned invalid JSON: {error}\nResponse: {text}")


def validate_diagnosis(diagnosis):
    """Validate required diagnosis fields."""

    required_fields = [
        "root_cause",
        "confidence",
        "evidence",
        "osi_layer",
        "concept",
        "next_command",
        "fix_steps",
        "human_review_required"
    ]

    missing = [field for field in required_fields if field not in diagnosis]

    if missing:
        return {"valid": False, "error": f"Missing fields: {missing}"}

    confidence = diagnosis["confidence"]

    if not isinstance(confidence, (int, float)):
        return {"valid": False, "error": "Confidence must be numeric."}

    if not 0 <= confidence <= 1:
        return {"valid": False, "error": "Confidence must be between 0 and 1."}

    if diagnosis["human_review_required"] is not True:
        return {"valid": False, "error": "human_review_required must be true."}

    return {"valid": True}


def diagnose_case(case):
    """Run the complete Gemini diagnosis pipeline."""

    prompt = build_case_prompt(case)
    raw_response = call_gemini(prompt)
    generated_text = extract_text(raw_response)
    diagnosis = parse_diagnosis(generated_text)

    validation = validate_diagnosis(diagnosis)

    if not validation["valid"]:
        raise ValueError(f"Invalid diagnosis: {validation['error']}")

    return diagnosis


if __name__ == "__main__":

    demo_case = {
        "case_id": "CASE-001",
        "symptom": "Router interface is unavailable.",
        "topology_note": "PC -> Switch -> Router",
        "show_outputs": "GigabitEthernet0/1 is administratively down",
        "concept_tag": "Interface availability",
        "osi_layer": "Layer 1"
    }

    print()
    print("NetSage AI - Gemini Diagnosis")
    print("=============================")

    try:
        diagnosis = diagnose_case(demo_case)
        print(json.dumps(diagnosis, indent=2))
        print()
        print("Validation: PASSED")

    except Exception as error:
        print()
        print("Diagnosis failed:")
        print(error)

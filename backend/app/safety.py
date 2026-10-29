import re

EMERGENCY_PATTERNS = {
    "possible_cardiac_emergency": [
        r"\bchest pain\b",
        r"\bchest pressure\b",
        r"\bcrushing chest\b",
    ],
    "possible_breathing_emergency": [
        r"\bsevere shortness of breath\b",
        r"\bcannot breathe\b",
        r"\bcan't breathe\b",
        r"\bstruggling to breathe\b",
    ],
    "possible_stroke": [
        r"\bsudden facial droop\b",
        r"\bsudden weakness on one side\b",
        r"\bsudden difficulty speaking\b",
        r"\bsudden loss of speech\b",
    ],
    "possible_severe_allergic_reaction": [
        r"\bthroat swelling\b",
        r"\btongue swelling\b",
        r"\bswelling of the tongue\b",
        r"\bsevere allergic reaction\b",
    ],
    "possible_severe_bleeding": [
        r"\buncontrolled bleeding\b",
        r"\bvomiting blood\b",
        r"\bvomiting blood clots\b",
        r"\bblack tarry stools\b",
    ],
}


def screen_emergency_symptoms(text: str) -> dict:
    """Screen text for selected emergency warning signs."""

    normalized = re.sub(r"\s+", " ", text.casefold()).strip()
    flags = []

    for category, patterns in EMERGENCY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                flags.append(category)
                break

    if flags:
        return {
            "emergency_flag": True,
            "urgency": "RED",
            "matched_categories": flags,
            "message": (
                "Potential emergency warning signs were identified. "
                "Contact local emergency services or seek emergency "
                "medical care now. Do not delay care while using this app."
            ),
        }

    return {
        "emergency_flag": False,
        "urgency": None,
        "matched_categories": [],
        "message": (
            "No warning signs from this limited screening list were "
            "identified. This does not rule out a medical emergency."
        ),
    }


def get_medical_disclaimer() -> str:
    return (
        "MediAgent provides decision-support information, not a diagnosis "
        "or a substitute for a qualified healthcare professional. "
        "Interaction data may be incomplete. Do not start, stop, or change "
        "medication based solely on this tool."
    )
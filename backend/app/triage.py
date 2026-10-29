from app.safety import screen_emergency_symptoms


def classify_triage(symptoms: str) -> dict:
    """
    Basic prototype triage classification.

    RED is used for selected emergency warning signs.
    YELLOW means further clinical assessment is recommended.
    GREEN means no concerning feature was identified by this
    limited rule set; it does not establish that the patient is safe.
    """

    emergency = screen_emergency_symptoms(symptoms)

    if emergency["emergency_flag"]:
        return {
            "urgency": "RED",
            "reason": (
                "Potential emergency warning signs require immediate "
                "professional assessment."
            ),
            "emergency_screen": emergency,
        }

    symptoms_lower = symptoms.casefold()

    concerning_terms = [
        "worsening",
        "persistent",
        "severe pain",
        "high fever",
        "dehydration",
        "fainting",
        "confusion",
        "blood in stool",
        "blood in urine",
        "pregnant",
        "infant",
    ]

    matched_terms = [
        term for term in concerning_terms
        if term in symptoms_lower
    ]

    if matched_terms:
        return {
            "urgency": "YELLOW",
            "reason": (
                "Potentially concerning features were reported. "
                "Seek prompt assessment from a qualified healthcare "
                "professional; urgency depends on the full clinical context."
            ),
            "matched_terms": matched_terms,
            "emergency_screen": emergency,
        }

    return {
        "urgency": "YELLOW",
        "reason": (
            "The prototype cannot reliably establish that symptoms are "
            "low risk. Obtain appropriate clinical guidance, especially "
            "if symptoms persist, worsen, or cause concern."
        ),
        "matched_terms": [],
        "emergency_screen": emergency,
    }
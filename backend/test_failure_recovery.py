
from unittest.mock import patch

from app.agent import run_agent


def test_medical_search_failure_does_not_crash_agent():
    symptoms = "I have a persistent headache since yesterday."
    medications = ["apixaban", "bivalirudin"]

    with patch(
        "app.agent.search_medical_information",
        side_effect=RuntimeError("Simulated search failure"),
    ):
        result = run_agent(
            symptoms=symptoms,
            medications=medications,
        )

    # The assessment should return a result rather than crash.
    assert result["status"] == "completed"

    # Local triage should remain available.
    assert result["urgency"] in {"RED", "YELLOW", "GREEN"}

    # The failed search must not fabricate search results.
    search_result = result["medical_information"]
    assert search_result.get("results", []) == []

    # The failure should be visible in the execution trace or errors.
    assert (
        any(
            step["action"] in {
                "tool_error",
                "fallback_tool_error",
                "agent_error",
            }
            for step in result["trace"]
        )
        or len(result["agent_errors"]) > 0
    )

    print("PASS: Assessment survived the simulated search failure.")
    print("Urgency:", result["urgency"])
    print("Agent errors:", result["agent_errors"])


if __name__ == "__main__":
    test_medical_search_failure_does_not_crash_agent()

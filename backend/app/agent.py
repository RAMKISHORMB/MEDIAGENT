
import json
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from app.safety import get_medical_disclaimer, screen_emergency_symptoms
from app.tools import lookup_interactions, search_medical_information
from app.triage import classify_triage


load_dotenv()

MODEL_NAME = "openai/gpt-oss-20b"
MAX_ITERATIONS = 4

SYSTEM_PROMPT = """
You are MediAgent, a healthcare decision-support prototype.

Coordinate the available tools and produce a concise, cautious summary.

Rules:
1. Use classify_triage to assess the reported symptoms.
2. If at least two distinct medications are supplied, use
   lookup_interactions to check the available dataset.
3. Use search_medical_information when general health information
   may be useful.
4. Choose tools dynamically. Never claim a tool was used unless
   its result appears in the conversation.
5. Never invent diagnoses, tool results, interactions, or citations.
6. A missing interaction match does not establish medication safety.
7. Never tell the patient to start, stop, or change medication.
8. Emergency screening is performed separately and takes priority.
9. Explain uncertainty and recommend qualified medical assessment
   when appropriate.
10. Never claim that the patient is definitely safe.
11. Web results are general information, not personalized medical advice.
12. Do not override the application's locally calculated urgency.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "classify_triage",
            "description": (
                "Assess symptoms using the application's conservative "
                "local triage rules."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "string",
                        "description": "Reported patient symptoms.",
                    }
                },
                "required": ["symptoms"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_interactions",
            "description": (
                "Check medication pairs against the available interaction "
                "dataset. A missing match does not establish safety."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "medications": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Current medication names.",
                    }
                },
                "required": ["medications"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_medical_information",
            "description": (
                "Search trusted health websites for general medical "
                "information or home-care guidance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A focused health-information query.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_NAMES = {
    "classify_triage",
    "lookup_interactions",
    "search_medical_information",
}


def _timestamp() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _record(
    trace: list[dict[str, Any]],
    action: str,
    observation: Any,
) -> None:
    """Record an agent action or observation."""
    trace.append(
        {
            "timestamp": _timestamp(),
            "action": action,
            "observation": observation,
        }
    )


def _not_run(message: str) -> dict[str, Any]:
    """Build a consistent result for a tool that was not executed."""
    return {
        "status": "not_run",
        "matches": [],
        "results": [],
        "message": message,
    }


def _execute_tool(
    name: str,
    arguments: dict[str, Any],
    symptoms: str,
    medications: list[str],
) -> dict[str, Any]:
    """Validate and execute an approved tool."""

    if name == "classify_triage":
        return classify_triage(symptoms=symptoms)

    if name == "lookup_interactions":
        requested = arguments.get("medications", [])

        if not isinstance(requested, list):
            return {
                "status": "invalid_arguments",
                "matches": [],
                "message": "Medications must be supplied as a list.",
            }

        distinct_medications = {
            medication.casefold() for medication in medications
        }

        if len(distinct_medications) < 2:
            return _not_run(
                "At least two distinct medication names are required."
            )

        # Always use the patient's supplied medication list.
        return lookup_interactions(medications=medications)

    if name == "search_medical_information":
        query = arguments.get("query")

        if not isinstance(query, str) or not query.strip():
            return {
                "status": "invalid_arguments",
                "results": [],
                "message": "A non-empty search query is required.",
            }

        return search_medical_information(query=query.strip())

    return {
        "status": "rejected",
        "message": "Tool is not on the approved allowlist.",
    }


def run_agent(
    symptoms: str,
    medications: list[str],
) -> dict[str, Any]:
    """Run emergency screening followed by the autonomous tool loop."""

    trace: list[dict[str, Any]] = []
    observations: dict[str, Any] = {}
    agent_errors: list[dict[str, str]] = []

    symptoms = symptoms.strip()
    medications = [
        medication.strip()
        for medication in medications
        if isinstance(medication, str) and medication.strip()
    ]

    # 1. Emergency screening must precede all routine processing.
    emergency = screen_emergency_symptoms(symptoms)

    _record(
        trace,
        "emergency_screen",
        {
            "emergency_flag": emergency["emergency_flag"],
            "urgency": emergency.get("urgency"),
            "matched_categories": emergency.get("matched_categories", []),
        },
    )

    if emergency["emergency_flag"]:
        _record(
            trace,
            "agent_stopped",
            "Emergency warning signs detected. Routine processing skipped.",
        )

        return {
            "status": "completed",
            "urgency": "RED",
            "summary": emergency["message"],
            "emergency_screen": emergency,
            "triage": None,
            "interaction_check": _not_run(
                "Skipped because emergency warning signs were detected."
            ),
            "medical_information": _not_run(
                "Emergency assessment takes priority over web search."
            ),
            "observations": observations,
            "trace": trace,
            "agent_errors": agent_errors,
            "disclaimer": get_medical_disclaimer(),
        }

    # 2. Establish a local fallback before contacting the LLM.
    local_triage = classify_triage(symptoms)
    observations["classify_triage"] = local_triage

    interaction_result = _not_run("Interaction check has not run.")
    medical_information = _not_run("Medical-information search has not run.")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        _record(
            trace,
            "llm_unavailable",
            "GROQ_API_KEY is missing. Local triage fallback used.",
        )

        return {
            "status": "completed_with_fallback",
            "urgency": local_triage["urgency"],
            "summary": (
                "Automated tool orchestration is unavailable. "
                "Local triage rules were used. This is not a diagnosis."
            ),
            "emergency_screen": emergency,
            "triage": local_triage,
            "interaction_check": interaction_result,
            "medical_information": medical_information,
            "observations": observations,
            "trace": trace,
            "agent_errors": agent_errors,
            "disclaimer": get_medical_disclaimer(),
        }

    client = Groq(
        api_key=api_key,
        timeout=30.0,
        max_retries=2,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "symptoms": symptoms,
                    "medications": medications,
                    "task": (
                        "Assess the case using available tools. Check "
                        "medication pairs when applicable and search "
                        "for general health information when useful."
                    ),
                }
            ),
        },
    ]

    # 3. Repeatedly request a model decision and execute its tool calls.
    for iteration in range(MAX_ITERATIONS):
        _record(
            trace,
            "agent_iteration",
            {"iteration": iteration + 1},
        )

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_completion_tokens=2000,
            )

            choice = response.choices[0]
            assistant_message = choice.message
            tool_calls = assistant_message.tool_calls or []

            messages.append(
                assistant_message.model_dump(exclude_none=True)
            )

            if not tool_calls:
                _record(
                    trace,
                    "agent_final_response",
                    {
                        "content": assistant_message.content or "",
                        "finish_reason": choice.finish_reason,
                    },
                )
                break

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                result: dict[str, Any]

                try:
                    arguments = json.loads(
                        tool_call.function.arguments or "{}"
                    )

                    if not isinstance(arguments, dict):
                        raise ValueError(
                            "Tool arguments must be a JSON object."
                        )

                    if tool_name not in TOOL_NAMES:
                        result = {
                            "status": "rejected",
                            "message": "Unknown tool requested.",
                        }
                    else:
                        result = _execute_tool(
                            name=tool_name,
                            arguments=arguments,
                            symptoms=symptoms,
                            medications=medications,
                        )

                    if tool_name == "classify_triage":
                        if result.get("urgency") in {
                            "RED",
                            "YELLOW",
                            "GREEN",
                        }:
                            observations["classify_triage"] = result

                    elif tool_name == "lookup_interactions":
                        interaction_result = result
                        observations["lookup_interactions"] = result

                    elif tool_name == "search_medical_information":
                        medical_information = result
                        observations["search_medical_information"] = result

                    _record(
                        trace,
                        "tool_execution",
                        {
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result,
                        },
                    )

                except Exception as error:
                    result = {
                        "status": "tool_error",
                        "message": (
                            "The tool failed. Review the execution trace."
                        ),
                    }

                    agent_errors.append(
                        {
                            "tool": tool_name,
                            "error_type": type(error).__name__,
                        }
                    )

                    _record(
                        trace,
                        "tool_error",
                        {
                            "tool": tool_name,
                            "error_type": type(error).__name__,
                        },
                    )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

        except Exception as error:
            agent_errors.append(
                {
                    "tool": "groq_completion",
                    "error_type": type(error).__name__,
                }
            )

            _record(
                trace,
                "agent_error",
                {
                    "error_type": type(error).__name__,
                    "message": (
                        "The LLM request failed. Local triage results "
                        "will be retained."
                    ),
                },
            )
            break

    else:
        _record(
            trace,
            "iteration_limit_reached",
            {"max_iterations": MAX_ITERATIONS},
        )

    # 4. Keep urgency controlled by local rules, not generated text.
    final_triage = observations.get("classify_triage", local_triage)

    # 5. Perform a fallback interaction check if the model did not call it.
    distinct_medications = {
        medication.casefold() for medication in medications
    }

    if (
        len(distinct_medications) >= 2
        and "lookup_interactions" not in observations
    ):
        try:
            interaction_result = lookup_interactions(
                medications=medications
            )
            observations["lookup_interactions"] = interaction_result

            _record(
                trace,
                "fallback_tool_execution",
                {
                    "tool": "lookup_interactions",
                    "result": interaction_result,
                },
            )

        except Exception as error:
            agent_errors.append(
                {
                    "tool": "lookup_interactions_fallback",
                    "error_type": type(error).__name__,
                }
            )

            _record(
                trace,
                "fallback_tool_error",
                {"tool": "lookup_interactions"},
            )

    # 6. Flag dataset matches for professional review.
    matches = interaction_result.get("matches", [])

    if matches:
        _record(
            trace,
            "interaction_review_required",
            {
                "match_count": len(matches),
                "message": (
                    "Dataset matches require review by a pharmacist "
                    "or qualified healthcare professional."
                ),
            },
        )

    summary = (
        f"Local triage urgency: {final_triage.get('urgency', 'YELLOW')}. "
        f"{final_triage.get('reason', 'Clinical assessment may be needed')} "
        "This prototype cannot diagnose a condition."
    )

    if matches:
        summary += (
            f" The dataset returned {len(matches)} medication-pair "
            "match(es). These records require professional review."
        )

    if agent_errors:
        summary += (
            " One or more automated steps failed. Review the execution trace."
        )

    return {
        "status": "completed",
        "urgency": final_triage.get("urgency", "YELLOW"),
        "summary": summary,
        "emergency_screen": emergency,
        "triage": final_triage,
        "interaction_check": interaction_result,
        "medical_information": medical_information,
        "observations": observations,
        "trace": trace,
        "agent_errors": agent_errors,
        "disclaimer": get_medical_disclaimer(),
    }


if __name__ == "__main__":
    result = run_agent(
        symptoms="I have a persistent headache.",
        medications=["apixaban", "bivalirudin"],
    )
    print(json.dumps(result, indent=2, default=str))

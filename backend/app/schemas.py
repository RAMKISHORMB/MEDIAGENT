from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    symptoms: str = Field(
        min_length=1,
        max_length=5000,
        description="Symptoms reported by the user",
    )

    medications: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Current medication names",
    )


class TriageResponse(BaseModel):
    status: str
    urgency: str
    summary: dict | str
    interaction_check: dict
    trace: list[dict]
    disclaimer: str
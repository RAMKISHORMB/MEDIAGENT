from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import run_agent
from app.schemas import TriageRequest

app = FastAPI(
    title="MediAgent",
    description=(
        "Prototype patient triage and drug interaction decision support."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root():
    return {
        "name": "MediAgent",
        "status": "online",
        "message": "Patient Triage & Interaction Checker prototype",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/triage")
def triage(request: TriageRequest):
    try:
        return run_agent(
            symptoms=request.symptoms,
            medications=request.medications,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {type(error).__name__}",
        ) from error
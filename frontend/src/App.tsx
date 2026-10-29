
import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

type Tab = "assessment" | "execution";

type TraceStep = {
  step: number;
  timestamp?: string;
  action?: string;
  event?: string;
  type?: string;
  name?: string;
  observation?: unknown;
  [key: string]: unknown;
};

type InteractionMatch = {
  drug1: string;
  drug2: string;
  interaction_types?: string[];
  interaction_type?: string;
  source?: string;
};

type InteractionCheck = {
  status?: string;
  checked_pairs?: number;
  matches?: InteractionMatch[];
  message?: string;
  reason?: string;
};

type AgentResult = {
  status?: string;
  urgency: "RED" | "YELLOW" | "GREEN";
  summary?: unknown;
  emergency_screen?: Record<string, unknown>;
  triage?: Record<string, unknown>;
  interaction_check?: InteractionCheck;
  medical_information?: {
    status?: string;
    results?: Array<Record<string, unknown>>;
    message?: string;
  };
  trace?: TraceStep[];
  agent_errors?: Array<Record<string, unknown>>;
  disclaimer?: string;
};

function formatAction(step: TraceStep): string {
  const action = step.action ?? step.event ?? step.type ?? step.name;

  if (typeof action !== "string" || !action.trim()) {
    return "Execution Step";
  }

  return action
    .replace(/^undefined[_\s]*/i, "")
    .replaceAll("_", " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatStatus(status?: string): string {
  if (!status) return "Status unavailable";

  return status
    .replaceAll("_", " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function getMatchTypes(match: InteractionMatch): string {
  if (Array.isArray(match.interaction_types)) {
    return match.interaction_types.join(", ");
  }

  return match.interaction_type ?? "Interaction details unavailable";
}

function getObservation(step: TraceStep): unknown {
  if (step.observation !== undefined) {
    return step.observation;
  }

  const { step: _step, timestamp: _timestamp, action: _action, event: _event, type: _type, name: _name, ...details } = step;

  return Object.keys(details).length
    ? details
    : { message: "No observation details were provided." };
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("assessment");
  const [symptoms, setSymptoms] = useState("");
  const [medications, setMedications] = useState("");
  const [result, setResult] = useState<AgentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyzePatient() {
    if (!symptoms.trim()) {
      setError("Please enter the patient's symptoms.");
      setActiveTab("assessment");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const medicationList = [
      ...new Set(
        medications
          .split(/[,;\n]+/)
          .map((medication) => medication.trim().toLowerCase())
          .filter(Boolean),
      ),
    ];

    try {
      const response = await fetch(`${API_URL}/api/triage`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symptoms: symptoms.trim(),
          medications: medicationList,
        }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(
          `Backend returned ${response.status}: ${message}`,
        );
      }

      const data: AgentResult = await response.json();

      if (!data.urgency) {
        throw new Error(
          "The backend response is missing triage priority.",
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message}. Make sure the FastAPI backend is running at ${API_URL}.`
          : "Unable to connect to the backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  const urgency = result?.urgency ?? "YELLOW";
  const interactionCheck = result?.interaction_check;
  const interactionMatches = interactionCheck?.matches ?? [];
  const trace = result?.trace ?? [];
  const checkedPairs = interactionCheck?.checked_pairs ?? 0;

  const interactionMessage =
    interactionCheck?.message ??
    interactionCheck?.reason ??
    (checkedPairs === 0
      ? "The interaction check was not run or no medication pairs were checked. Enter at least two distinct medication names to request a pairwise check."
      : "No matching interaction records were returned. This does not establish that the medication combination is safe.");

  const medicalInformation = result?.medical_information;
  const medicalResults = medicalInformation?.results ?? [];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✚</div>

          <div>
            <h1>MediAgent</h1>
            <span>CLINICAL DECISION SUPPORT</span>
          </div>
        </div>

        <div className="sidebar-section">WORKSPACE</div>

        <button
          type="button"
          className={`nav-item ${
            activeTab === "assessment" ? "active" : ""
          }`}
          onClick={() => setActiveTab("assessment")}
          aria-current={
            activeTab === "assessment" ? "page" : undefined
          }
        >
          <span>◉</span>
          Patient assessment
        </button>

        <button
          type="button"
          className={`nav-item ${
            activeTab === "execution" ? "active" : ""
          }`}
          onClick={() => setActiveTab("execution")}
          aria-current={
            activeTab === "execution" ? "page" : undefined
          }
        >
          <span>≡</span>
          Agent execution
        </button>

        <div className="sidebar-bottom">
          <div className="status-dot" />

          <div>
            <strong>Local API</strong>
            <small>Expected at port 8000</small>
          </div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">
              HEALTHCARE INTELLIGENCE PLATFORM
            </div>

            <h2>
              {activeTab === "assessment"
                ? "Patient Triage & Interaction Checker"
                : "Agent Execution Monitor"}
            </h2>

            <p>
              {activeTab === "assessment"
                ? "Symptom assessment, medication screening, and transparent execution traces."
                : "Inspect recorded tool calls, observations, and execution results from the latest assessment."}
            </p>
          </div>

          <div className="prototype-badge">
            <span />
            PROTOTYPE
          </div>
        </header>

        <div className="safety-banner">
          <span className="banner-icon">⚠</span>

          <div>
            <strong>Clinical safety notice</strong>

            <p>
              This prototype supports demonstrations and is not a
              diagnostic system. It must not replace professional
              medical assessment.
            </p>
          </div>
        </div>

        {activeTab === "assessment" ? (
          <div className="workspace-grid">
            <section className="card patient-card">
              <div className="card-heading">
                <div className="heading-icon">✚</div>

                <div>
                  <h3>Patient assessment</h3>
                  <p>Enter symptoms and current medications.</p>
                </div>
              </div>

              <label htmlFor="symptoms">
                PATIENT SYMPTOMS <span>*</span>
              </label>

              <textarea
                id="symptoms"
                value={symptoms}
                onChange={(event) => setSymptoms(event.target.value)}
                placeholder="Example: I have a headache that has persisted since yesterday..."
                rows={5}
                maxLength={5000}
                disabled={loading}
              />

              <div className="field-hint">
                {symptoms.length}/5000 characters
              </div>

              <label htmlFor="medications">
                CURRENT MEDICATIONS{" "}
                <span className="optional">(OPTIONAL)</span>
              </label>

              <textarea
                id="medications"
                value={medications}
                onChange={(event) =>
                  setMedications(event.target.value)
                }
                placeholder={
                  "Enter medication names separated by commas.\nExample: Apixaban, Bivalirudin"
                }
                rows={3}
                disabled={loading}
              />

              <div className="field-hint">
                Use generic names where possible. Separate each
                medication with a comma.
              </div>

              {error && (
                <div className="error-message" role="alert">
                  {error}
                </div>
              )}

              <button
                type="button"
                className="analyze-button"
                onClick={analyzePatient}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    Run assessment <span>→</span>
                  </>
                )}
              </button>

              <div className="privacy-note">
                <span>◈</span>
                Demo only. Do not enter identifiable patient
                information.
              </div>
            </section>

            <section className="card results-card">
              <div className="card-heading">
                <div className="heading-icon">◷</div>

                <div>
                  <h3>Assessment results</h3>
                  <p>
                    Review the screening output and limitations.
                  </p>
                </div>
              </div>

              {!result && !loading && (
                <div className="empty-state">
                  <div className="empty-icon">◷</div>
                  <h3>Awaiting assessment</h3>

                  <p>
                    Submit symptoms to run the emergency screen,
                    triage rules, and applicable medication
                    interaction checks.
                  </p>

                  <div className="empty-steps">
                    <span>01&nbsp; Screen</span>
                    <span>02&nbsp; Check</span>
                    <span>03&nbsp; Review</span>
                  </div>
                </div>
              )}

              {loading && (
                <div className="loading-state">
                  <div className="loading-ring" />
                  <h3>Processing assessment</h3>
                  <p>Running the available screening tools...</p>
                </div>
              )}

              {result && (
                <div className="results-content">
                  <div
                    className={`urgency-panel urgency-${urgency.toLowerCase()}`}
                  >
                    <div>
                      <span className="result-label">
                        TRIAGE PRIORITY
                      </span>

                      <h2>{urgency}</h2>

                      <p>
                        {urgency === "RED"
                          ? "Potential emergency warning signs identified."
                          : urgency === "YELLOW"
                            ? "Professional clinical assessment is advised."
                            : "Lower urgency must be established by a validated assessment."}
                      </p>
                    </div>

                    <div className="urgency-symbol">
                      {urgency === "RED"
                        ? "!"
                        : urgency === "YELLOW"
                          ? "↗"
                          : "✓"}
                    </div>
                  </div>

                  {urgency === "RED" && (
                    <div className="emergency-note">
                      Seek emergency medical care now. Do not delay
                      care to use this application.
                    </div>
                  )}

                  <div className="result-section">
                    <div className="section-title">
                      <span>💊</span>
                      <h4>Medication interaction screening</h4>
                    </div>

                    <div className="interaction-summary">
                      <div>
                        <strong>{interactionMatches.length}</strong>
                        <small>Dataset matches</small>
                      </div>

                      <div>
                        <strong>{checkedPairs}</strong>
                        <small>Pairs checked</small>
                      </div>

                      <span className="status-pill">
                        {formatStatus(interactionCheck?.status)}
                      </span>
                    </div>

                    {interactionMatches.length > 0 ? (
                      <div className="match-list">
                        {interactionMatches.map((match, index) => (
                          <div
                            className="match-item"
                            key={`${match.drug1}-${match.drug2}-${index}`}
                          >
                            <strong>
                              {match.drug1} + {match.drug2}
                            </strong>

                            <p>{getMatchTypes(match)}</p>

                            <small>
                              Source:{" "}
                              {match.source ??
                                "Organizer-provided interaction dataset"}
                            </small>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="muted-note">
                        {interactionMessage}
                      </p>
                    )}

                    <p className="caution-text">
                      Dataset matches are not a complete clinical risk
                      assessment. A missing match does not mean a
                      combination is safe.
                    </p>
                  </div>

                  <div className="result-section">
                    <div className="section-title">
                      <span>◷</span>
                      <h4>Agent execution trace</h4>

                      <span className="trace-count">
                        {trace.length} steps
                      </span>
                    </div>

                    <div className="trace-list">
                      {trace.map((step, index) => (
                        <details
                          className="trace-step"
                          key={`${step.step ?? index}-${index}`}
                        >
                          <summary>
                            <span className="trace-number">
                              {String(
                                step.step ?? index + 1,
                              ).padStart(2, "0")}
                            </span>

                            <span className="trace-action">
                              {formatAction(step)}
                            </span>

                            <span className="trace-chevron">⌄</span>
                          </summary>

                          <pre>
                            {JSON.stringify(
                              getObservation(step),
                              null,
                              2,
                            )}
                          </pre>
                        </details>
                      ))}

                      {trace.length === 0 && (
                        <p className="muted-note">
                          No execution steps were returned by the
                          backend.
                        </p>
                      )}
                    </div>

                    <button
                      type="button"
                      className="analyze-button"
                      onClick={() => setActiveTab("execution")}
                    >
                      View full execution trace →
                    </button>
                  </div>

                  <div className="disclaimer-box">
                    <strong>Important limitation</strong>

                    <p>
                      {result.disclaimer ??
                        "MediAgent provides decision-support information, not a diagnosis or a substitute for a qualified healthcare professional. Interaction data may be incomplete. Do not start, stop, or change medication based solely on this tool."}
                    </p>
                  </div>
                </div>
              )}
            </section>
          </div>
        ) : (
          <section className="card execution-page">
            <div className="card-heading">
              <div className="heading-icon">≡</div>

              <div>
                <h3>Agent execution</h3>
                <p>
                  Inspect the actual execution trace from the latest
                  assessment.
                </p>
              </div>
            </div>

            {!result && (
              <div className="empty-state">
                <div className="empty-icon">≡</div>

                <h3>No execution trace available</h3>

                <p>
                  Run a patient assessment first. The agent's recorded
                  execution steps will appear here.
                </p>

                <button
                  type="button"
                  className="analyze-button"
                  onClick={() => setActiveTab("assessment")}
                >
                  Go to patient assessment →
                </button>
              </div>
            )}

            {result && (
              <>
                <div className="interaction-summary">
                  <div>
                    <strong>{trace.length}</strong>
                    <small>Recorded steps</small>
                  </div>

                  <div>
                    <strong>{formatStatus(result.status)}</strong>
                    <small>Agent status</small>
                  </div>

                  <div>
                    <strong>{formatStatus(urgency)}</strong>
                    <small>Triage priority</small>
                  </div>
                </div>

                {trace.length > 0 ? (
                  <div className="trace-list">
                    {trace.map((step, index) => (
                      <details
                        className="trace-step"
                        key={`${step.step ?? index}-${index}`}
                      >
                        <summary>
                          <span className="trace-number">
                            {String(
                              step.step ?? index + 1,
                            ).padStart(2, "0")}
                          </span>

                          <span className="trace-action">
                            {formatAction(step)}
                          </span>

                          <span className="trace-chevron">⌄</span>
                        </summary>

                        <pre>
                          {JSON.stringify(
                            getObservation(step),
                            null,
                            2,
                          )}
                        </pre>
                      </details>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <h3>No execution steps returned</h3>
                    <p>
                      The latest backend response contains no trace
                      entries.
                    </p>
                  </div>
                )}

                {result.agent_errors &&
                  result.agent_errors.length > 0 && (
                    <div className="error-message">
                      <strong>Recorded execution errors</strong>

                      <pre>
                        {JSON.stringify(
                          result.agent_errors,
                          null,
                          2,
                        )}
                      </pre>
                    </div>
                  )}

                <div className="result-section">
                  <div className="section-title">
                    <span>💊</span>
                    <h4>Interaction check summary</h4>
                  </div>

                  <p className="muted-note">
                    Status:{" "}
                    {formatStatus(interactionCheck?.status)}
                    {" · "}
                    {checkedPairs} medication pair(s) checked.
                  </p>

                  {interactionMatches.length > 0 ? (
                    <div className="match-list">
                      {interactionMatches.map((match, index) => (
                        <div
                          className="match-item"
                          key={`${match.drug1}-${match.drug2}-${index}`}
                        >
                          <strong>
                            {match.drug1} + {match.drug2}
                          </strong>

                          <p>{getMatchTypes(match)}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="muted-note">
                      {interactionMessage}
                    </p>
                  )}
                </div>

                <div className="result-section">
                  <div className="section-title">
                    <span>⌕</span>
                    <h4>Medical information search</h4>
                  </div>

                  <p className="muted-note">
                    Status:{" "}
                    {formatStatus(medicalInformation?.status)}
                  </p>

                  {medicalInformation?.message && (
                    <p className="muted-note">
                      {medicalInformation.message}
                    </p>
                  )}

                  {medicalResults.length > 0 && (
                    <div className="match-list">
                      {medicalResults.map((item, index) => (
                        <div
                          className="match-item"
                          key={`medical-result-${index}`}
                        >
                          <strong>
                            {String(item.title ?? "Medical resource")}
                          </strong>

                          {item.snippet !== undefined && (
                            <p>{String(item.snippet)}</p>
                          )}

                          {item.url !== undefined && (
                            <p>
                              {String(item.url)}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="disclaimer-box">
                  <strong>Execution transparency</strong>

                  <p>
                    This panel displays the execution information
                    returned by the latest backend assessment. It does
                    not independently validate clinical decisions or
                    establish patient safety.
                  </p>
                </div>
              </>
            )}

            <button
              type="button"
              className="analyze-button"
              onClick={() => setActiveTab("assessment")}
            >
              ← Back to patient assessment
            </button>
          </section>
        )}

        <footer>
          <span>MediAgent · Healthcare &amp; Biotech</span>
          <span>Prototype · Human clinical review required</span>
        </footer>
      </section>
    </main>
  );
}

export default App;
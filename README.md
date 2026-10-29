# MEDIAGENT 🩺
### AI-Powered Healthcare Triage & Medication Interaction Decision Support

MEDIAGENT is an AI-powered healthcare decision-support prototype that combines symptom-based triage, medication interaction lookup, and medical information retrieval in a tool-using AI agent.

The system uses a **ReAct-style agent workflow** to select tools, interpret their results, handle tool failures, and produce a structured assessment with an execution trace.

> **Disclaimer:** MEDIAGENT is an experimental prototype for demonstration and educational purposes. It is not a medical device and does not replace professional medical advice, diagnosis, or treatment.

## ✨ Features

- **Symptom-Based Triage:** Classifies reported symptoms into urgency levels and flags predefined emergency warning signs.
- **Medication Interaction Lookup:** Checks pairs of entered medications against an interaction dataset.
- **Medical Information Retrieval:** Searches selected trusted health information sources for relevant information.
- **Tool-Using AI Agent:** Dynamically selects from approved tools to support the assessment workflow.
- **Execution Trace:** Displays agent steps, tool observations, and execution results.
- **Failure Handling:** Records tool errors and attempts recovery when a tool fails.
- **Safety-First Fallbacks:** Applies local emergency screening and conservative triage logic.
- **Web Interface:** Provides a user interface for entering symptoms and medications and reviewing assessment results.

## 🏗️ Architecture

```text
                 ┌────────────────────────┐
                 │    React + TypeScript  │
                 │       Frontend         │
                 └───────────┬────────────┘
                             │ HTTP / JSON
                             ▼
                 ┌────────────────────────┐
                 │     FastAPI Backend    │
                 │                        │
                 │  Symptom Assessment    │
                 │  Emergency Screening   │
                 │  Triage Logic          │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │   AI Agent (Groq API)  │
                 │                        │
                 │   Tool Selection       │
                 │   Observation Analysis │
                 │   Failure Recovery     │
                 └───────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌───────────┐  ┌────────────┐  ┌────────────┐
        │ Medication│  │ Medical    │  │ Emergency  │
        │ Interaction│ │ Information│  │ Screening  │
        │ Dataset   │  │ Search     │  │ & Triage   │
        └───────────┘  └────────────┘  └────────────┘
```

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| AI Agent | Groq API, `openai/gpt-oss-20b` |
| Medical Information Search | DuckDuckGo search library |
| Medication Interaction Data | CSV-based dataset |
| API Documentation | FastAPI / Swagger UI |
| Version Control | Git and GitHub |

## 📁 Project Structure

```text
MEDIAGENT/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── safety.py
│   │   ├── triage.py
│   │   └── tools.py
│   ├── .env.example
│   └── requirements.txt
├── data/
│   ├── DDI_data.csv
│   └── interactions.json
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

*The structure above describes the main application components; individual files may vary.*

## ⚙️ Prerequisites

Install the following before running the application:

- Python 3.11 or another version compatible with the backend dependencies
- Node.js and npm
- Git
- A Groq API key

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/RAMKISHORMB/MEDIAGENT.git
cd MEDIAGENT
```

### 2. Set up the backend

Open a terminal in the project root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file inside the `backend` directory.

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace the placeholder with your own API key.

**Never commit your `.env` file or expose your API key publicly.**

### 4. Start the backend

From the `backend` directory, run:

```bash
python -m uvicorn app.main:app --reload
```

The API should be available at:

- API base: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 5. Set up the frontend

Open a second terminal:

```cmd
cd C:\path\to\MEDIAGENT\frontend
npm install
npm run dev
```

Replace `C:\path\to\MEDIAGENT` with your actual project directory.

Open the local frontend URL printed by Vite in your terminal, typically:

`http://localhost:5173`

Keep the backend and frontend terminals running while using the application.

## 🔍 How It Works

1. **Input:** The user enters symptoms and current medications.
2. **Emergency Screening:** Predefined emergency warning signs are checked first.
3. **Triage:** The system applies conservative urgency classification rules.
4. **Agent Reasoning:** The AI agent selects approved tools based on the assessment context.
5. **Medication Check:** Entered medication pairs are compared against the available dataset.
6. **Information Retrieval:** The agent can search for relevant information from selected health sources.
7. **Observation and Recovery:** Tool results and errors are recorded, with recovery attempts when appropriate.
8. **Results:** The interface displays the assessment, medication lookup results, medical information, and agent execution trace.

## 🛡️ Safety & Limitations

MEDIAGENT has important limitations:

- It does not provide a confirmed medical diagnosis.
- Its medication interaction results depend on the available dataset and may be incomplete.
- A missing interaction result does not establish that a medication combination is safe.
- Search results may not apply to an individual's medical history or circumstances.
- Triage classifications are based on prototype rules and must not be treated as validated clinical assessments.
- AI-generated content can be incomplete or incorrect.
- Tool recovery improves application resilience but does not guarantee medical accuracy.

**For severe or potentially life-threatening symptoms, seek emergency medical care immediately. Do not delay care to use this application.**

Do not start, stop, or change prescribed medication based solely on MEDIAGENT's output. Consult a qualified healthcare professional or pharmacist.

## 🔐 Privacy & Security

- Keep API credentials in environment variables.
- Do not commit `.env` files or other secrets.
- Avoid entering real patient-identifiable information into this prototype.
- Review the privacy practices and terms of any external AI or search service before use.
- Do not use this prototype to store or process sensitive patient data in production.

## 🧪 Testing

The development workflow has included checks for:

- Emergency symptom handling
- Empty symptom input
- Medication-pair lookup
- Duplicate medication handling
- Insufficient medication inputs
- Rejection of unapproved tools
- Simulated medical search failures
- Agent execution trace generation

These checks demonstrate prototype behavior; they do not constitute clinical validation, comprehensive security testing, or production certification.

## 🗺️ Future Improvements

Potential future development includes:

- Broader and more reliable medication interaction data
- Improved source attribution and evidence retrieval
- More comprehensive automated tests
- Better handling of conflicting or incomplete information
- Clinician review workflows
- Privacy and security improvements
- Evaluation against clinically reviewed test cases

## 👨‍💻 Author

**RAMKISHORMB**

GitHub: [@RAMKISHORMB](https://github.com/RAMKISHORMB)

## 📄 License

No license has been specified yet. Unless a license is added to the repository, do not assume that others have permission to reuse, modify, or redistribute the project.

---

**MEDIAGENT — Exploring safer, tool-assisted healthcare decision support.**

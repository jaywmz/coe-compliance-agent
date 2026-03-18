# 🛡️ Pipeline Governance Compliance Agent

**A GenAI-powered proof-of-concept that reads inline Azure DevOps pipeline YAML, identifies governance violations, and auto-generates a compliant CI/CD template hierarchy — automating what took 8 months to do manually.**

> CSC3101 Capstone Project Extension — SIT-University of Glasgow  
> Jiang Weimin (2301083) | Central Provident Fund Board (CPFB)

🔗 **Live Demo:** [coe-compliance-agent.streamlit.app](https://coe-compliance-agent.streamlit.app)

---

## Capstone Context

This PoC extends the **"Centralised CI/CD CoE Template Framework for DevSecOps Governance at CPFB"** capstone project. Over an 8-month industry placement, the capstone delivered a centralised, parameterised YAML template framework on Azure DevOps (GCC 2.0) that:

- Migrated ~55 application repositories from fragmented inline pipeline configurations to a reusable 5-layer template hierarchy (Pipelines → Stages → Jobs → Tasks → Scripts)
- Integrated 4 security tools: **SonarQube**, **Mend CLI** (SCA, SAST, Container Scanning), **BuildKit**, and **GitVersion**
- Achieved **30–87% configuration reduction** across all tools
- Established a **default-secure governance model** (`enableFailPolicy = true` by default)

### Problem Statements Addressed

| # | Sub-Problem | What This PoC Demonstrates |
|---|---|---|
| SP1 | **Configuration Duplication** across ~55 repos | The agent reproduces the same 30–87% reduction achieved manually — proving the governance rules are machine-enforceable |
| SP2 | **Absence of Governance** for pipeline organisation, naming, documentation | The agent generates compliant templates, scripts, and 9-section READMEs following the exact CoE documentation standard |
| SP3 | **Incomplete Security Integration** — SAST and container scanning were absent | The agent handles all 4 tool types (SonarQube, Mend SCA, Mend SAST, Container) and can generalise to unknown tools (e.g., Fortify) |

This PoC validates the **Chapter 6.5 future work recommendation**: *"AIOps / Agentic AI — AI agent reads repo pipelines, auto-generates CoE-compliant templates following governance standards."*

---

## What It Does

The agent takes raw inline Azure DevOps pipeline YAML (the "before" state) and produces:

```
INPUT                          PROCESS                              OUTPUT
─────                          ───────                              ──────
Inline pipeline YAML    →   1. Tool Detection (LLM call #1)    →   Compliance report (violations + severity)
(e.g., 104-line              2. Hierarchy Generation (LLM #2)       Consuming pipeline YAML (the template reference)
 Mend SCA config)            3. Self-Validation (LLM #3)            Full 5-layer template hierarchy:
                             4. Self-Correction (if needed)           Stage → Job → Orchestrator Task → Scripts
                                                                    9-section README per template
                                                                    Configuration reduction percentage
```

### Example: Mend SCA Migration

**Before (104 lines inline):**
- Hardcoded credentials in YAML variables
- Manual WhiteSource Unified Agent download + config file
- Inline report parsing, artifact staging, policy enforcement
- No SBOM generation, no reachability analysis

**After (17 lines template reference):**
- Credentials from Key Vault via variable groups
- Single template call to `mend_sca_orchestrator_task.yaml`
- Automatic PDF report, SBOM (CycloneDX/SPDX), reachability analysis
- Three-step deferred enforcement: scan → publish → check

**Result: 83% configuration reduction (DS-01)**

---

## How It Is Agentic

This is not a single LLM prompt-and-response. The agent demonstrates autonomous decision-making through a multi-step execution loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTIC EXECUTION LOOP                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: TOOL DETECTION (LLM Call #1)                       │
│  ├── Agent autonomously classifies the input YAML            │
│  ├── Decides: Mend SCA? SAST? Container? SonarQube? Other?  │
│  └── Selects tool-specific parameter set (no cross-mixing)   │
│                                                              │
│  Step 2: HIERARCHY GENERATION (LLM Call #2)                  │
│  ├── Generates full 5-layer hierarchy + scripts + READMEs    │
│  └── Applies governance rules, data masking, naming conventions│
│                                                              │
│  Step 3: SELF-VALIDATION (LLM Call #3)                       │
│  ├── Second LLM call audits the generated output             │
│  ├── Checks 9 governance criteria:                           │
│  │   ├── compliant_yaml populated?                           │
│  │   ├── All hierarchy levels present?                       │
│  │   ├── Scripts use correct structure?                      │
│  │   ├── No sensitive data leaks?                            │
│  │   ├── READMEs complete?                                   │
│  │   ├── No cross-tool parameter contamination?              │
│  │   └── Reduction calculated correctly?                     │
│  └── Returns pass/fail + specific issues                     │
│                                                              │
│  Step 4: SELF-CORRECTION (conditional, up to 2 retries)      │
│  ├── If validation fails: feeds issues back to generator     │
│  ├── Agent regenerates with fix instructions                 │
│  └── Re-validates until pass or max retries                  │
│                                                              │
│  Step 5: MULTI-FILE ANALYSIS (optional)                      │
│  ├── Splits input by '---' separator                         │
│  ├── Auto-detects tool for each block independently          │
│  └── Processes each with full agentic loop                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

The **Agent Trace** tab in the UI shows the full execution trace: which tool was detected, how many attempts were needed, what validation issues were found and corrected.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    USER (Browser)                         │
│          Streamlit UI (app.py)                           │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │ Input Panel  │  │ Output Panel                     │  │
│  │ - Paste YAML │  │ - Violations    - Template Files │  │
│  │ - Examples   │  │ - Consuming     - READMEs        │  │
│  │ - Multi-file │  │   Pipeline      - Agent Trace    │  │
│  └──────┬──────┘  └──────────────────▲───────────────┘  │
│         │                            │                   │
└─────────┼────────────────────────────┼───────────────────┘
          │                            │
          ▼                            │
┌──────────────────────────────────────┴───────────────────┐
│                 AGENT CORE (agent.py)                     │
│                                                           │
│  detect_tool()          → LLM Call #1 (classification)    │
│  analyse_pipeline()     → LLM Call #2 (generation)        │
│  _validate_output()     → LLM Call #3 (validation)        │
│  [retry if failed]      → LLM Call #4 (self-correction)   │
│  analyse_multiple()     → orchestrates multi-file mode    │
│                                                           │
│  System Prompt: 8 governance rules, tool-specific params, │
│  script structure standards, data masking rules,          │
│  README format (9 sections), naming conventions           │
│                                                           │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              AZURE OPENAI (GPT-4o)                        │
│              Sweden Central region                         │
│              Standard S0 tier                              │
│              ~$0.025 per analysis call                     │
└──────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **LLM** | Azure OpenAI GPT-4o | YAML analysis, hierarchy generation, validation |
| **Backend** | Python 3.12 | Agent core, API orchestration |
| **Frontend** | Streamlit | Interactive web UI for demo |
| **Hosting** | Streamlit Community Cloud | Free deployment with GitHub integration |
| **Secrets** | Streamlit Secrets + python-dotenv | API key management (cloud + local) |
| **CI/CD Platform** (capstone) | Azure DevOps (GCC 2.0) | Where the actual CoE templates run |
| **Security Tools** (capstone) | SonarQube, Mend CLI, BuildKit, GitVersion | What the templates integrate |

---

## Project Files

```
coe-compliance-agent/
├── agent.py            # Agent core — system prompt, agentic loop, tool detection,
│                       #   self-validation, multi-file analysis
├── app.py              # Streamlit UI — input panel, results tabs (violations,
│                       #   consuming pipeline, hierarchy, READMEs, agent trace)
├── requirements.txt    # Python dependencies
├── test_connection.py  # Azure OpenAI connection test (development only)
├── .env                # Local secrets (not committed — see .gitignore)
├── .gitignore          # Excludes .env, venv/, __pycache__/
└── README.md           # This file
```

### `agent.py` — Agent Core

The brain of the system. Contains:

- **`get_secret()`** — reads from Streamlit secrets (cloud) or `.env` (local), enabling the same code to run in both environments
- **`SYSTEM_PROMPT`** — ~250 lines encoding all 8 CoE governance rules, tool-specific parameter sets, script structure standards, naming conventions, data masking rules, README format, and output JSON schema
- **`detect_tool()`** — fast LLM call that classifies input YAML into one of: Mend SCA, Mend SAST, Container Scanning, SonarQube, Fortify, or Unknown
- **`analyse_pipeline()`** — the main agentic loop: detect → generate → validate → correct (up to 2 retries)
- **`_validate_output()`** — second LLM call that audits the generated output against 9 governance checks
- **`analyse_multiple()`** — splits multi-file input and processes each independently

### `app.py` — Streamlit UI

The presentation layer. Features:

- **Sidebar:** example loader (4 pre-built inline YAMLs), multi-file toggle, hierarchy diagram
- **Input panel:** YAML text area with syntax highlighting
- **Output tabs:**
  - 🚨 **Violations** — governance violations with severity badges (CRITICAL/HIGH/MEDIUM/LOW)
  - ✅ **Consuming Pipeline** — the template reference YAML that replaces the inline config
  - 📦 **Template Hierarchy** — full 5-layer output: Stage → Job → Task → Scripts, with call chain arrows
  - 📖 **READMEs** — 9-section documentation per template (Overview, Prerequisites, Parameters, Flow, Output, Variables, Secrets, Usage, Error Handling)
  - 🤖 **Agent Trace** — agentic execution log showing tool detection, validation attempts, self-correction history
  - 🔧 **Raw JSON** — complete agent response for debugging

---

## CoE Governance Rules (Encoded in System Prompt)

| # | Rule | What It Enforces |
|---|---|---|
| 1 | Template Distribution | All scanning via shared `resources: repositories` — no inline configs |
| 2 | Parameter Naming | Standardised names (`userKey`, `email`, `apiKey`, `enableFailPolicy`, etc.) |
| 3 | Template Hierarchy | 5-layer: Pipelines → Stages → Jobs → Tasks → Scripts |
| 4 | Script Architecture | Three-step deferred enforcement: scan → publish → check. Exit code 9 = policy violation |
| 5 | Default-Secure | `enableFailPolicy: true` by default — must explicitly opt out |
| 6 | Credential Management | All secrets from Azure Key Vault via Library variable groups |
| 7 | Documentation Standard | 9-section README per template with parameter tables and flow diagrams |
| 8 | Artefact Publishing | SCA: PDF + SBOM + reachability. SAST: JSON + HTML. Container: JSON + SARIF + SPDX + CycloneDX |

---

## Dependencies

```
openai          # Azure OpenAI Python SDK
streamlit       # Web UI framework
pyyaml          # YAML parsing (for future enhancements)
python-dotenv   # Local .env file loading
```

Install locally:
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

---

## Setup

### 1. Azure OpenAI Resource

- Create an Azure OpenAI resource (Standard S0)
- Deploy GPT-4o model
- Note your endpoint URL and API key

### 2. Local Development

Create a `.env` file:
```properties
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

Run:
```bash
streamlit run app.py
```

### 3. Streamlit Cloud Deployment

1. Push code to GitHub (private repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as main file
4. Add secrets in Settings → Secrets (TOML format):
```toml
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY = "your-api-key"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
```

---

## Cost

| Component | Cost |
|---|---|
| Azure OpenAI GPT-4o | ~$0.025 per analysis (2K input + 1K output tokens) |
| Streamlit Community Cloud | Free |
| 200 test/demo calls | ~$5 |
| **Total PoC budget** | **< $10 out of $100 student credits** |

---

## Future Work

This PoC is Phase 1 of the agentic AI vision. The roadmap:

| Phase | Capability | Status |
|---|---|---|
| Phase 1 (current) | GenAI compliance analysis with self-validation | ✅ Complete |
| Phase 2 | Azure DevOps API integration — agent reads repos directly | Planned |
| Phase 3 | Autonomous PR generation — agent creates PRs with compliant YAML | Planned |
| Phase 4 | Continuous monitoring — agent runs on every PR as a pipeline extension | Planned |

---

## Acknowledgements

- **Mr. Soh Lam Soon** — Industry Supervisor, CPFB
- **A/Prof. Bogdan Cautis** — Academic Supervisor, University of Glasgow
- **CPFB Cloud Services & Support Team** — Template testing and adoption feedback

---

## License

This project is part of the CSC3101 Capstone Project for academic purposes. Not licensed for commercial use.
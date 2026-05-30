# ComplianceGuard AI

> **Autonomous AI agent for continuous security and compliance monitoring.**
> Powered by LLM reasoning, Open Policy Agent (OPA), and ArmorIQ policy enforcement.

---

## 📖 Overview

**ComplianceGuard AI** is a state-of-the-art security compliance platform. It runs a continuous `scan ➔ enforce ➔ report` loop orchestrated by an autonomous AI agent, leveraging Open Policy Agent (OPA) for structured checks, and the ArmorIQ SDK to intercept and validate all agent actions. Every scan, violation, and agent decision is cryptographically audited and visualized in real-time.

```
                  ┌──────────────────────────────┐
                  │      ComplianceGuard AI      │
                  │   scan ➔ enforce ➔ report    │
                  └──────────────┬───────────────┘
                                 ▼
                     Autonomous LLM Scanning
                                 ▼
                 ArmorIQ SDK Intercept & Enforce
                                 ▼
                    Structured PDF/JSON Reports
```

---

## ✨ Features

- **Autonomous LLM Scanning**: Scans repository contents (source files, Dockerfiles, and dependencies) using custom tool-calling agents.
- **ArmorIQ Interception & Policy Gate**: Intercepts every tool call, verifies agent intent, logs tamper-proof cryptographic metadata, and enforces strict boundary policies.
- **Open Policy Agent (OPA)**: Runs lightning-fast compliance evaluations using Rego policy files (covering container security, cryptographic strength, dependencies, access control, etc.).
- **Real-Time WebSocket Updates**: Broadcasts progress, tools called, decisions, and discovered violations directly to the React dashboard.
- **CI/CD Integration**: Automates compliance checks as pull request gates to fail builds when `HIGH` severity violations are detected.
- **Model Context Protocol (MCP)**: Integrates seamlessly as an MCP server, sharing tools with external AI clients (like Claude Desktop).

---

## 🏗️ System Architecture

ComplianceGuard AI follows a modular architecture that separates client layers, orchestration gateways, autonomous agent runtimes, policy engines, and audit logs.

### Component Architecture

The following diagram illustrates how the frontend components, API endpoints, agent loop, OPA engine, and database communicate with each other and the ArmorIQ SDK.

```mermaid
graph TB
    %% Client Tier
    subgraph Client_Tier ["Client & CI/CD Tier"]
        UI["React Dashboard (Frontend)"]
        CLI["Typer CLI"]
        CICD["CI/CD Runner (GitHub Actions)"]
        MCP_Client["MCP Client (e.g., Claude Desktop)"]
    end

    %% API Tier
    subgraph API_Tier ["FastAPI Gateway & API Tier"]
        Gateway["FastAPI App (main.py)"]
        REST["REST Endpoints (/api/scan, /api/report, /api/violations, /api/audit)"]
        WS["WebSocket (/ws/scan-status)"]
        MCP_Server["MCP Server (mcp_server.py)"]
    end

    %% Agent Tier
    subgraph Agent_Tier ["Autonomous Agent Tier"]
        Agent["Autonomous LLM Scan Agent"]
        Claw["ArmorClaw Proxy Interceptor"]
        Tools["Agent Tools (read_file, parse_dependency, check_crypto, run_opa_query)"]
    end

    %% Policy & Audit Tier
    subgraph Policy_Tier ["Security & Policy Enforcement"]
        ArmorIQ["ArmorIQ Client / SDK"]
        OPARunner["OPA Runner (evaluator)"]
        RegoPolicies["Rego Policies (.rego)"]
        ViolEngine["Violation Engine (Scoring)"]
    end

    %% Data Tier
    subgraph Data_Tier ["Persistence Layer"]
        DB[("PostgreSQL Database")]
    end

    %% Connections
    UI -- "HTTP REST & WebSockets" --> Gateway
    CLI -- "Direct/CLI API" --> REST
    CICD -- "HTTP POST" --> REST
    MCP_Client -- "JSON-RPC (STDIN/STDOUT)" --> MCP_Server

    Gateway --> REST
    Gateway --> WS
    Gateway --> MCP_Server

    REST -- "Background Tasks" --> Agent
    MCP_Server -- "Executes" --> Agent

    Agent -- "1. Decides to call tool" --> Claw
    Claw -- "2. Policy check & logging" --> ArmorIQ
    Claw -- "3. If allowed, execute" --> Tools

    Tools -- "OPA query tool calls" --> OPARunner
    OPARunner -- "Evaluates against" --> RegoPolicies
    OPARunner -- "Validates via" --> ArmorIQ

    Tools -- "Evaluates severity" --> ViolEngine
    
    Agent -- "Pushes live state updates" --> WS
    Agent -- "Writes scan runs & findings" --> DB
    ArmorIQ -- "Logs tamper-proof cryptographically signed events" --> DB
```

### Scan Flow & Interception Lifecycle

Every scan runs asynchronously, utilizing a secure interception pattern to prevent unapproved agent tool executions. Here is the step-by-step lifecyle of a compliance scan:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / CI Pipeline
    participant UI as React UI / WebSocket Client
    participant API as FastAPI Backend
    participant Agent as LLM Scan Agent
    participant Claw as ArmorClaw Proxy
    participant AIQ as ArmorIQ SDK
    participant Tools as Agent Tools
    participant OPA as OPARunner / OPA Rules
    participant DB as PostgreSQL DB

    User->>API: POST /api/scan (Trigger Scan)
    API->>DB: Create ScanRun (PENDING)
    API-->>User: 202 Accepted (scan_id)
    UI->>API: Connect to /ws/scan-status?scan_id=uuid

    Note over API, Agent: Spawn async background task for scan

    API->>Agent: Run Scan (repo_path, service_name)
    Agent->>API: Broadcast: SCAN_STARTED
    API-->>UI: WS Event (SCAN_STARTED)
    
    loop For each source file, dependency manifest, Dockerfile
        Agent->>Claw: Invoke Tool (e.g. read_file)
        Claw->>AIQ: Verify Intent & Tool Policy Check
        alt Policy Blocked (e.g. write_file)
            AIQ-->>Claw: Decision: BLOCK
            Claw-->>Agent: Error (Tool blocked by Policy)
            Agent->>API: Broadcast: TOOL_CALLED (Decision: BLOCK)
            API-->>UI: WS Event (TOOL_CALLED - Blocked)
            AIQ->>DB: Log Blocked AuditEvent (signed)
        else Policy Allowed (e.g. read_file)
            AIQ-->>Claw: Decision: ALLOW
            Claw->>Tools: Execute read_file
            Tools-->>Claw: File Contents
            Claw-->>Agent: File Contents
            Agent->>API: Broadcast: TOOL_CALLED (Decision: ALLOW)
            API-->>UI: WS Event (TOOL_CALLED - Allowed)
            AIQ->>DB: Log Allowed AuditEvent (signed)
        end
        
        Note over Agent, OPA: Scanning for violations
        Agent->>Claw: Invoke Tool: run_opa_query
        Claw->>AIQ: Policy Check
        AIQ-->>Claw: ALLOW
        Claw->>Tools: Execute run_opa_query
        Tools->>OPA: Evaluate rules (cryptographic.rego, etc.)
        OPA-->>Tools: Rego decision & messages
        Tools-->>Claw: Violations list
        Claw-->>Agent: Violations list
        
        alt Violations Found
            Agent->>API: Broadcast: VIOLATION_FOUND
            API-->>UI: WS Event (VIOLATION_FOUND)
            Agent->>DB: Write Violation to Database
        end
    end

    Agent->>API: Scan Complete
    API->>DB: Update ScanRun status to COMPLETED
    Agent->>API: Broadcast: SCAN_COMPLETED
    API-->>UI: WS Event (SCAN_COMPLETED)
```

---

## 🛠️ Tech Stack

### Backend
- **Core Framework**: FastAPI, Pydantic v2, Pydantic Settings
- **ORM & DB**: SQLAlchemy 2.0 (Asyncio), Alembic, PostgreSQL (`asyncpg`)
- **Security & Policies**: ArmorIQ SDK & ArmorClaw, Open Policy Agent (Rego rules)
- **Agent Orchestration**: MCP Python SDK, Typer (CLI)

### Frontend
- **Framework**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS
- **Icons & Visualization**: Lucide React, Recharts

### Infrastructure
- **Containerization**: Docker, Docker Compose

---

## 📁 Repository Structure

```
compliance-ai/
├── README.md                           # Main Documentation
├── docker-compose.yml                  # Local development compose setup
├── .env.example                        # Environment variables template
├── backend/                            # Python FastAPI Backend
│   ├── main.py                         # Application Entrypoint
│   ├── settings.py                     # App Config & Environment loader
│   ├── armoriq_client.py               # ArmorIQ Initialization Client
│   ├── armoriq_shims.py                # Interception wrappers for agent tools
│   ├── cli.py                          # Typer command-line tool
│   ├── mcp_server.py                   # Model Context Protocol server
│   ├── api/                            # API routes (REST and WebSockets)
│   │   ├── scan.py                     # Scan run triggers and polling
│   │   ├── report.py                   # Report generators (PDF/JSON)
│   │   ├── violations.py               # Violations retrieval
│   │   ├── audit.py                    # Cryptographic audit log retrieval
│   │   └── ws.py                       # WebSocket broadcaster
│   ├── agent/                          # Autonomous Scan Agent
│   │   ├── scan_agent.py               # ArmorClaw agent definition
│   │   ├── tools/                      # Scan agent tools
│   │   └── prompts/                    # Agent System & Scan Prompts
│   ├── engine/                         # Evaluation & Scoring
│   │   ├── violation_engine.py         # Severity classifier
│   │   ├── report_generator.py         # Compliance Report generation
│   │   └── audit_logger.py             # ArmorIQ Event persistence
│   ├── db/                             # Database Models and Session
│   └── policies/                       # OPA Rego Policies & Runner
│       ├── opa_runner.py               # OPA execution layer
│       └── *.rego                      # Rego files (crypto, container, etc.)
├── frontend/                           # React + Vite Frontend
│   ├── src/
│   │   ├── App.tsx                     # Main dashboard page
│   │   ├── components/                 # UI components (graphs, tables)
│   │   ├── hooks/                      # Custom React hooks (WS, Fetch)
│   │   └── api/                        # HTTP client
└── ci/                                 # CI/CD pipelines
    ├── github-action.yml               # GitHub Actions workflow definition
    └── scan_trigger.sh                 # Trigger automation script
```

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose
- ArmorIQ API Key
- Python 3.12+ (if running CLI / MCP server locally)

### Quick Start (Docker)

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your `ARMORIQ_API_KEY`:
   ```bash
   cp .env.example .env
   ```
3. Start the entire system:
   ```bash
   docker-compose up --build
   ```
4. Access the web dashboard at `http://localhost:5173` and backend API documentation at `http://localhost:8000/docs`.

### Local Setup (Development)

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 💡 Usage

### 1. Web Dashboard
Open `http://localhost:5173` to interact with the visual dashboard. Trigger scans by providing a directory path, watch the real-time progress bar, view detailed violations grouped by severity, and inspect tamper-proof audit trails.

### 2. Typer CLI
You can execute compliance scans directly from your terminal:
```bash
# Activate backend virtual environment first
python -m backend.cli scan "MyService" "/path/to/repo"

# List previous scan results
python -m backend.cli list-scans
```

### 3. Model Context Protocol (MCP) Server
Integrate compliance tools with LLMs (e.g. Claude Desktop):
```bash
python -m backend.mcp_server
```

#### Configure Claude Desktop
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "compliance-guard": {
      "command": "python",
      "args": ["-m", "backend.mcp_server"],
      "env": {
        "ARMORIQ_API_KEY": "your_armoriq_api_key_here"
      }
    }
  }
}
```

### 4. API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/scan` | Trigger a new compliance scan asynchronously |
| `GET` | `/api/scan/{scan_id}` | Retrieve scan progress and overall metadata |
| `GET` | `/api/violations` | Retrieve list of violations (filter by scan, severity) |
| `GET` | `/api/report/{scan_id}` | Retrieve structured JSON compliance report |
| `GET` | `/api/audit/{scan_id}` | Retrieve cryptographic audit logs from ArmorIQ |
| `WS` | `/ws/scan-status` | Subscribe to WebSocket event logs |

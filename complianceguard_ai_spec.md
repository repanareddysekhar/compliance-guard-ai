# ComplianceGuard AI — Technical Specification
> **Version:** 2.0 | **Track:** ArmorIQ · AI Agent for the Real World  
> **Team:** The Stacktracers — Reddy Sekhar · Yogarathnam S  
> **Team Code:** `team-B1A342C54DB3`

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [ArmorIQ SDK Integration (Core)](#3-armoriq-sdk-integration-core)
4. [System Architecture](#4-system-architecture)
5. [Repository & Project Structure](#5-repository--project-structure)
6. [Data Models](#6-data-models)
7. [Backend — FastAPI Service](#7-backend--fastapi-service)
8. [AI Agent Layer](#8-ai-agent-layer)
9. [Violation Engine](#9-violation-engine)
10. [Frontend — React Dashboard](#10-frontend--react-dashboard)
11. [Database Schema (PostgreSQL)](#11-database-schema-postgresql)
12. [CI/CD Integration](#12-cicd-integration)
13. [Environment Variables & Config](#13-environment-variables--config)
14. [Docker Setup](#14-docker-setup)
15. [Build Order for AI Tools](#15-build-order-for-ai-tools)
16. [Acceptance Criteria](#16-acceptance-criteria)

---

## 1. Project Overview

**ComplianceGuard AI** is an autonomous AI agent that continuously monitors software services for security and compliance violations. It runs a `scan → enforce → report` loop powered by LLM reasoning, ArmorIQ's policy enforcement SDK, and OPA (Open Policy Agent).

### Core Value Proposition
| Problem | ComplianceGuard AI's Answer |
|---|---|
| Manual security audits are slow and brittle | Autonomous LLM agent replaces manual review |
| Violations are caught post-deployment | Policy gate blocks violations before production |
| No unified cross-service enforcement | One agent, one ArmorIQ policy engine, all services |
| No audit trail | Every action cryptographically logged via ArmorIQ |

### Key Metrics (Target)
- **10×** faster than manual audits  
- **~95%** of violations detected in dev, not prod  
- **100%** policy enforcement coverage

---

## 2. Goals & Non-Goals

### In Scope (MVP — 48 hrs)
- Scan a directory of services (source code, `Dockerfile`, `requirements.txt`, config files)
- Detect violation categories: cryptographic, dependency, container, access control, header hygiene
- Route every agent tool call through ArmorIQ SDK proxy
- Score and classify violations by severity (HIGH / MED / LOW)
- Auto-generate structured remediation reports
- Cryptographic audit log via ArmorIQ
- React dashboard showing live scan state, violation log, and report download
- CI/CD trigger via HTTP endpoint (GitHub Actions compatible)

### Out of Scope (Post-MVP)
- Multi-tenant SaaS billing
- SAML/SSO authentication
- Custom policy authoring UI
- Auto-apply code fixes (read-only remediation reports only in MVP)

---

## 3. ArmorIQ SDK Integration (Core)

> **ArmorIQ SDK is the central integration.** Every agent tool call MUST pass through it. No direct LLM tool execution without ArmorIQ proxy interception.

### 3.1 SDK Initialization

```python
# backend/armoriq_client.py
from armoriq import ArmorIQClient, PolicyConfig

armoriq = ArmorIQClient(
    api_key=settings.ARMORIQ_API_KEY,
    policy_config=PolicyConfig(
        enforcement_mode="blocking",       # block, not just warn
        audit_log_enabled=True,
        cryptographic_audit=True,          # tamper-proof log
        intent_verification=True,          # verify agent intent before tool exec
    )
)
```

### 3.2 ArmorClaw Agent Wrapping

ArmorClaw is ArmorIQ's agent wrapper. Every tool the LLM calls is intercepted:

```python
# backend/agent/scan_agent.py
from armoriq.armorclaw import ArmorClaw, ToolCallPolicy

claw = ArmorClaw(
    client=armoriq,
    agent_name="ComplianceGuard-Scanner",
    tool_policy=ToolCallPolicy(
        allowed_tools=["read_file", "parse_dependency", "check_crypto", "run_opa_query"],
        blocked_tools=["execute_shell", "write_file", "network_request"],  # hard block
        require_intent_match=True,
    )
)
```

### 3.3 Policy Gate Flow

```
Agent decides to call tool
        │
        ▼
ArmorClaw intercepts call
        │
        ├─ Intent verification ──► FAIL ──► BLOCKED (logged)
        │
        ├─ Policy match check ───► FAIL ──► BLOCKED (logged)
        │
        └─ PASS ─────────────────────────► Tool executes (logged)
```

### 3.4 Audit Log Entry (per tool call)

```json
{
  "event_id": "uuid-v4",
  "timestamp": "ISO8601",
  "agent": "ComplianceGuard-Scanner",
  "tool_called": "check_crypto",
  "intent": "Check MD5 usage in AuthService",
  "policy_decision": "ALLOW | BLOCK",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "signature": "armoriq-sig:..."
}
```

### 3.5 OPA Integration via ArmorIQ

```python
# backend/policies/opa_runner.py
from armoriq.opa import OPARunner

opa = OPARunner(
    client=armoriq,
    policy_bundle_path="./policies/",     # local .rego files
    decision_log=True
)

result = await opa.evaluate(
    policy="compliance/cryptographic",
    input={"algorithm": "MD5", "context": "password_hash"}
)
# result.allowed → bool
# result.violations → list[Violation]
```

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ComplianceGuard AI                        │
│                                                             │
│  ┌──────────────┐    ┌─────────────────────────────────┐   │
│  │   React UI   │◄───│        FastAPI Backend           │   │
│  │  Dashboard   │    │  /api/scan  /api/report          │   │
│  └──────────────┘    └────────────┬────────────────────┘   │
│                                   │                         │
│                      ┌────────────▼────────────────────┐   │
│                      │      AI Scan Agent               │   │
│                      │  (LLM via ArmorIQ SDK)           │   │
│                      │  Orchestrated by ArmorClaw       │   │
│                      └────────────┬────────────────────┘   │
│                                   │                         │
│              ┌────────────────────┼──────────────────┐      │
│              ▼                    ▼                   ▼      │
│    ┌─────────────────┐  ┌──────────────────┐  ┌──────────┐ │
│    │  ArmorIQ Proxy  │  │  OPA Engine      │  │ Violation│ │
│    │  Intent verify  │  │  Policy eval     │  │  Engine  │ │
│    │  Policy gate    │  │  .rego rules     │  │ Scoring  │ │
│    │  Audit log      │  └──────────────────┘  └──────────┘ │
│    └─────────────────┘                                      │
│                                   │                         │
│                      ┌────────────▼────────────────────┐   │
│                      │       PostgreSQL                 │   │
│                      │  audit_logs | violations         │   │
│                      │  scan_runs  | policies           │   │
│                      └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Trigger** — HTTP POST `/api/scan` with `{ repo_path, service_name }` or CI/CD webhook
2. **Agent Init** — ArmorClaw wraps LLM agent; policy context loaded
3. **Scan Phase** — Agent calls allowed tools (read_file, parse_dependency, check_crypto, run_opa_query). Each call intercepted by ArmorIQ.
4. **Enforce Phase** — OPA evaluates each finding against policy bundles. ArmorIQ logs decision.
5. **Score Phase** — Violation Engine scores and classifies findings.
6. **Report Phase** — Structured report generated; audit log finalized with cryptographic signature.
7. **Push to UI** — WebSocket event pushed to dashboard; PostgreSQL updated.

---

## 5. Repository & Project Structure

```
complianceguard-ai/
├── README.md
├── docker-compose.yml
├── .env.example
│
├── backend/                          # Python FastAPI
│   ├── main.py                       # FastAPI app entrypoint
│   ├── settings.py                   # Pydantic settings (env vars)
│   ├── armoriq_client.py             # ArmorIQ SDK singleton
│   │
│   ├── api/
│   │   ├── scan.py                   # POST /api/scan
│   │   ├── report.py                 # GET /api/report/{scan_id}
│   │   ├── violations.py             # GET /api/violations
│   │   ├── audit.py                  # GET /api/audit/{scan_id}
│   │   └── ws.py                     # WebSocket /ws/scan-status
│   │
│   ├── agent/
│   │   ├── scan_agent.py             # ArmorClaw agent definition
│   │   ├── tools/
│   │   │   ├── file_reader.py        # read_file tool
│   │   │   ├── dependency_parser.py  # parse_dependency tool
│   │   │   ├── crypto_checker.py     # check_crypto tool
│   │   │   └── opa_query.py          # run_opa_query tool
│   │   └── prompts/
│   │       ├── system_prompt.txt
│   │       └── scan_prompt.txt
│   │
│   ├── engine/
│   │   ├── violation_engine.py       # Severity scoring + classification
│   │   ├── report_generator.py       # Structured report builder
│   │   └── audit_logger.py           # Wraps ArmorIQ audit API
│   │
│   ├── db/
│   │   ├── models.py                 # SQLAlchemy models
│   │   ├── database.py               # Async DB session
│   │   └── migrations/               # Alembic migrations
│   │
│   └── policies/                     # OPA .rego policy files
│       ├── cryptographic.rego
│       ├── dependency.rego
│       ├── container.rego
│       └── access_control.rego
│
├── frontend/                         # React + TypeScript
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── Dashboard.tsx         # Main layout
│       │   ├── ScanTrigger.tsx       # Trigger scan form
│       │   ├── ViolationLog.tsx      # Violation table with badges
│       │   ├── AuditTrail.tsx        # Cryptographic audit events
│       │   ├── StatsBar.tsx          # Services/violations/fixed counts
│       │   ├── ReportViewer.tsx      # Structured report panel
│       │   └── ScanStatus.tsx        # Live WebSocket scan progress
│       ├── hooks/
│       │   ├── useScanWebSocket.ts   # WebSocket hook
│       │   └── useViolations.ts      # Data fetching hook
│       ├── api/
│       │   └── client.ts             # Axios API client
│       └── types/
│           └── index.ts              # TypeScript interfaces
│
└── ci/
    ├── github-action.yml             # GitHub Actions workflow
    └── scan_trigger.sh               # Shell script to call /api/scan
```

---

## 6. Data Models

### TypeScript Interfaces (Frontend & API Contract)

```typescript
// frontend/src/types/index.ts

export type Severity = "HIGH" | "MED" | "LOW";
export type ViolationStatus = "BLOCKED" | "FLAGGED" | "REPORTED" | "AUTO_FIXED";
export type PolicyDecision = "ALLOW" | "BLOCK";
export type ScanStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface ScanRun {
  id: string;                    // UUID
  service_name: string;
  repo_path: string;
  status: ScanStatus;
  started_at: string;            // ISO8601
  completed_at?: string;
  services_scanned: number;
  violations_found: number;
  auto_fixed: number;
}

export interface Violation {
  id: string;
  scan_run_id: string;
  service: string;
  severity: Severity;
  status: ViolationStatus;
  category: "CRYPTOGRAPHIC" | "DEPENDENCY" | "CONTAINER" | "ACCESS_CONTROL" | "HEADER";
  description: string;
  file_path?: string;
  line_number?: number;
  remediation: string;           // Step-by-step fix recommendation
  opa_policy_ref: string;        // e.g. "compliance/cryptographic"
  detected_at: string;
}

export interface AuditEvent {
  event_id: string;
  scan_run_id: string;
  timestamp: string;
  agent: string;
  tool_called: string;
  intent: string;
  policy_decision: PolicyDecision;
  input_hash: string;
  output_hash: string;
  signature: string;             // ArmorIQ cryptographic signature
}

export interface Report {
  scan_run_id: string;
  generated_at: string;
  summary: {
    total_services: number;
    total_violations: number;
    by_severity: Record<Severity, number>;
    by_category: Record<string, number>;
  };
  violations: Violation[];
  audit_events: AuditEvent[];
  compliance_score: number;      // 0–100
}
```

---

## 7. Backend — FastAPI Service

### 7.1 `main.py`

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import scan, report, violations, audit, ws

app = FastAPI(title="ComplianceGuard AI", version="2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(scan.router,       prefix="/api")
app.include_router(report.router,     prefix="/api")
app.include_router(violations.router, prefix="/api")
app.include_router(audit.router,      prefix="/api")
app.include_router(ws.router)
```

### 7.2 API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/scan` | Trigger a scan run | API key header |
| `GET` | `/api/scan/{scan_id}` | Get scan run status | API key header |
| `GET` | `/api/violations?scan_id=&severity=&status=` | List violations | API key header |
| `GET` | `/api/report/{scan_id}` | Get full structured report | API key header |
| `GET` | `/api/audit/{scan_id}` | Get cryptographic audit log | API key header |
| `WS` | `/ws/scan-status` | Live scan progress stream | — |

### 7.3 POST `/api/scan` — Request & Response

**Request:**
```json
{
  "service_name": "AuthService",
  "repo_path": "/path/to/repo",
  "scan_depth": "full",
  "standards": ["FIPS-140-3", "CIS-Docker", "OWASP-Dependency"]
}
```

**Response (202 Accepted):**
```json
{
  "scan_id": "uuid-v4",
  "status": "PENDING",
  "message": "Scan queued. Connect to /ws/scan-status for live updates."
}
```

### 7.4 WebSocket Events (`/ws/scan-status`)

```json
// Sent by server as scan progresses:
{ "type": "SCAN_STARTED",     "scan_id": "...", "service": "AuthService" }
{ "type": "TOOL_CALLED",      "tool": "check_crypto", "intent": "...", "decision": "ALLOW" }
{ "type": "VIOLATION_FOUND",  "violation": { ...Violation } }
{ "type": "SCAN_COMPLETED",   "scan_id": "...", "summary": { ... } }
{ "type": "SCAN_FAILED",      "scan_id": "...", "error": "..." }
```

---

## 8. AI Agent Layer

### 8.1 System Prompt

```
# backend/agent/prompts/system_prompt.txt

You are ComplianceGuard AI, an autonomous security compliance agent.
Your job is to scan software services for violations of security policies.

You have access to the following tools ONLY:
- read_file(path): Read a source file, Dockerfile, or config
- parse_dependency(manifest_path): Parse requirements.txt, package.json, pom.xml
- check_crypto(code_snippet): Detect non-compliant cryptographic usage
- run_opa_query(policy, input): Evaluate a policy against an input

Rules:
1. Call tools one at a time. State your intent before each call.
2. Never attempt to modify files, execute shell commands, or make network calls.
3. When you find a violation, record it with: service, file_path, line_number, category, severity, and a step-by-step remediation.
4. After scanning all files, generate a final compliance summary.
5. Be exhaustive — check every file, dependency, and config.
```

### 8.2 Agent Orchestrator

```python
# backend/agent/scan_agent.py
from armoriq.armorclaw import ArmorClaw
from armoriq_client import armoriq
from .tools import file_reader, dependency_parser, crypto_checker, opa_query

async def run_scan(scan_run_id: str, repo_path: str, service_name: str, standards: list[str]):
    claw = ArmorClaw(
        client=armoriq,
        agent_name="ComplianceGuard-Scanner",
        tool_policy=ToolCallPolicy(
            allowed_tools=["read_file", "parse_dependency", "check_crypto", "run_opa_query"],
            blocked_tools=["execute_shell", "write_file", "network_request"],
            require_intent_match=True,
        )
    )

    tools = [
        file_reader.tool,
        dependency_parser.tool,
        crypto_checker.tool,
        opa_query.tool,
    ]

    scan_prompt = build_scan_prompt(repo_path, service_name, standards)

    async for event in claw.run_async(
        prompt=scan_prompt,
        tools=tools,
        system=SYSTEM_PROMPT,
        on_tool_call=lambda e: handle_tool_event(scan_run_id, e),
        on_violation=lambda v: handle_violation(scan_run_id, v),
    ):
        await broadcast_ws_event(scan_run_id, event)
```

### 8.3 Tool Definitions

Each tool follows this pattern (example: `check_crypto`):

```python
# backend/agent/tools/crypto_checker.py
from armoriq.armorclaw import Tool

BANNED_ALGORITHMS = ["MD5", "SHA1", "DES", "3DES", "RC4"]
FIPS_APPROVED = ["SHA-256", "SHA-384", "SHA-512", "AES-256", "RSA-2048+", "ECDSA-P256+"]

def check_crypto_impl(code_snippet: str) -> dict:
    found_violations = []
    for algo in BANNED_ALGORITHMS:
        if algo.lower() in code_snippet.lower():
            found_violations.append({
                "algorithm": algo,
                "compliant": False,
                "reason": f"{algo} is not FIPS 140-3 approved",
                "suggested": "Use SHA-256 or AES-256-GCM"
            })
    return {"violations": found_violations, "is_compliant": len(found_violations) == 0}

tool = Tool(
    name="check_crypto",
    description="Check a code snippet for non-compliant cryptographic algorithm usage",
    func=check_crypto_impl,
    parameters={
        "code_snippet": {"type": "string", "description": "Source code to analyze"}
    }
)
```

---

## 9. Violation Engine

### 9.1 Severity Scoring Logic

```python
# backend/engine/violation_engine.py

SEVERITY_RULES = {
    "CRYPTOGRAPHIC": {
        "MD5":        "HIGH",    # Direct FIPS violation
        "SHA1":       "HIGH",
        "DES":        "HIGH",
        "RC4":        "HIGH",
        "hardcoded_key": "HIGH",
    },
    "DEPENDENCY": {
        "critical_cve": "HIGH",
        "high_cve":     "MED",
        "medium_cve":   "LOW",
        "outdated":     "LOW",
    },
    "CONTAINER": {
        "root_user":        "HIGH",   # Privileged container
        "no_healthcheck":   "MED",
        "latest_tag":       "LOW",
        "expose_all_ports": "MED",
    },
    "ACCESS_CONTROL": {
        "no_auth_middleware": "HIGH",
        "wildcard_cors":      "MED",
        "debug_mode_on":      "MED",
    },
    "HEADER": {
        "missing_hsts":     "MED",
        "missing_csp":      "MED",
        "missing_x_frame":  "LOW",
    }
}

def score_violation(category: str, finding: str) -> tuple[Severity, ViolationStatus]:
    severity = SEVERITY_RULES.get(category, {}).get(finding, "LOW")
    status = "BLOCKED" if severity == "HIGH" else "FLAGGED" if severity == "MED" else "REPORTED"
    return severity, status
```

### 9.2 OPA Policy Files (`.rego`)

```rego
# backend/policies/cryptographic.rego
package compliance.cryptographic

default allow = false

banned_algorithms := {"MD5", "SHA1", "DES", "3DES", "RC4"}

allow {
    not input.algorithm in banned_algorithms
}

violation[msg] {
    input.algorithm in banned_algorithms
    msg := sprintf("Non-FIPS algorithm detected: %s. Use SHA-256 or AES-256-GCM instead.", [input.algorithm])
}
```

```rego
# backend/policies/container.rego
package compliance.container

default allow = false

allow {
    input.user != "root"
    input.has_healthcheck == true
    input.tag != "latest"
}

violation[msg] {
    input.user == "root"
    msg := "Container running as root. Use a non-root user (USER appuser)."
}

violation[msg] {
    input.tag == "latest"
    msg := "Using 'latest' Docker tag. Pin to a specific version for reproducibility."
}
```

---

## 10. Frontend — React Dashboard

### 10.1 Component Hierarchy

```
App
└── Dashboard
    ├── StatsBar               ← Services / Violations / Auto-Fixed counters
    ├── ScanTrigger            ← Form: service name + repo path + Scan button
    ├── ScanStatus             ← Live WebSocket progress bar + event feed
    ├── ViolationLog           ← Table: severity badge | description | status badge | service
    ├── AuditTrail             ← Collapsible: ArmorIQ cryptographic events
    └── ReportViewer           ← Compliance score ring + download JSON/PDF
```

### 10.2 Key Component: `ViolationLog.tsx`

```tsx
// Violation row display contract
interface ViolationRowProps {
  violation: Violation;
}

const SEVERITY_COLORS = {
  HIGH: "bg-red-100 text-red-700 border-red-300",
  MED:  "bg-amber-100 text-amber-700 border-amber-300",
  LOW:  "bg-blue-100 text-blue-700 border-blue-300",
};

const STATUS_COLORS = {
  BLOCKED:    "bg-red-600 text-white",
  FLAGGED:    "bg-amber-500 text-white",
  REPORTED:   "bg-gray-500 text-white",
  AUTO_FIXED: "bg-green-600 text-white",
};
```

### 10.3 Key Component: `ScanTrigger.tsx`

```tsx
// Calls POST /api/scan; initiates WebSocket connection on success
const handleScan = async () => {
  const res = await api.post("/api/scan", { service_name, repo_path, standards });
  const { scan_id } = res.data;
  connectWebSocket(scan_id);   // hooks into useScanWebSocket
};
```

### 10.4 WebSocket Hook

```typescript
// frontend/src/hooks/useScanWebSocket.ts
export function useScanWebSocket(scanId: string | null) {
  const [events, setEvents] = useState<WsEvent[]>([]);
  const [status, setStatus] = useState<ScanStatus>("PENDING");

  useEffect(() => {
    if (!scanId) return;
    const ws = new WebSocket(`ws://localhost:8000/ws/scan-status?scan_id=${scanId}`);
    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as WsEvent;
      setEvents(prev => [...prev, event]);
      if (event.type === "SCAN_COMPLETED") setStatus("COMPLETED");
      if (event.type === "SCAN_FAILED") setStatus("FAILED");
    };
    return () => ws.close();
  }, [scanId]);

  return { events, status };
}
```

---

## 11. Database Schema (PostgreSQL)

```sql
-- Run via Alembic migration

CREATE TABLE scan_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name    TEXT NOT NULL,
    repo_path       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',   -- PENDING|RUNNING|COMPLETED|FAILED
    standards       TEXT[],
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    services_scanned INT DEFAULT 0,
    violations_found INT DEFAULT 0,
    auto_fixed      INT DEFAULT 0,
    compliance_score NUMERIC(5,2)
);

CREATE TABLE violations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_run_id     UUID REFERENCES scan_runs(id) ON DELETE CASCADE,
    service         TEXT NOT NULL,
    severity        TEXT NOT NULL,        -- HIGH|MED|LOW
    status          TEXT NOT NULL,        -- BLOCKED|FLAGGED|REPORTED|AUTO_FIXED
    category        TEXT NOT NULL,        -- CRYPTOGRAPHIC|DEPENDENCY|CONTAINER|ACCESS_CONTROL|HEADER
    description     TEXT NOT NULL,
    file_path       TEXT,
    line_number     INT,
    remediation     TEXT NOT NULL,
    opa_policy_ref  TEXT,
    detected_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_run_id     UUID REFERENCES scan_runs(id) ON DELETE CASCADE,
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    agent           TEXT NOT NULL,
    tool_called     TEXT NOT NULL,
    intent          TEXT,
    policy_decision TEXT NOT NULL,        -- ALLOW|BLOCK
    input_hash      TEXT,
    output_hash     TEXT,
    signature       TEXT                  -- ArmorIQ cryptographic signature
);

CREATE INDEX idx_violations_scan_run ON violations(scan_run_id);
CREATE INDEX idx_violations_severity ON violations(severity);
CREATE INDEX idx_audit_scan_run      ON audit_events(scan_run_id);
```

---

## 12. CI/CD Integration

### 12.1 GitHub Actions Workflow

```yaml
# ci/github-action.yml
name: ComplianceGuard AI Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  compliance-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trigger ComplianceGuard Scan
        run: |
          RESPONSE=$(curl -s -X POST "${{ secrets.COMPLIANCEGUARD_URL }}/api/scan" \
            -H "X-API-Key: ${{ secrets.COMPLIANCEGUARD_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "service_name": "${{ github.repository }}",
              "repo_path": ".",
              "standards": ["FIPS-140-3", "CIS-Docker", "OWASP-Dependency"]
            }')
          echo "SCAN_ID=$(echo $RESPONSE | jq -r .scan_id)" >> $GITHUB_ENV

      - name: Wait for Scan + Check Results
        run: |
          # Poll until COMPLETED or FAILED
          for i in {1..30}; do
            STATUS=$(curl -s "${{ secrets.COMPLIANCEGUARD_URL }}/api/scan/$SCAN_ID" \
              -H "X-API-Key: ${{ secrets.COMPLIANCEGUARD_API_KEY }}" | jq -r .status)
            echo "Status: $STATUS"
            if [ "$STATUS" = "COMPLETED" ]; then break; fi
            if [ "$STATUS" = "FAILED" ]; then exit 1; fi
            sleep 10
          done

      - name: Fail on HIGH violations
        run: |
          HIGH_COUNT=$(curl -s "${{ secrets.COMPLIANCEGUARD_URL }}/api/violations?scan_id=$SCAN_ID&severity=HIGH" \
            -H "X-API-Key: ${{ secrets.COMPLIANCEGUARD_API_KEY }}" | jq '.total')
          echo "HIGH violations: $HIGH_COUNT"
          if [ "$HIGH_COUNT" -gt "0" ]; then
            echo "::error::$HIGH_COUNT HIGH severity violations found. Fix before merging."
            exit 1
          fi
```

---

## 13. Environment Variables & Config

```bash
# .env.example — copy to .env and fill in values

# ArmorIQ SDK (REQUIRED)
ARMORIQ_API_KEY=your_armoriq_api_key_here
ARMORIQ_ENFORCEMENT_MODE=blocking          # blocking | warning | audit_only
ARMORIQ_CRYPTOGRAPHIC_AUDIT=true

# LLM Provider (used via ArmorIQ SDK)
LLM_MODEL=claude-sonnet-4-20250514         # or gpt-4o, etc.
LLM_MAX_TOKENS=4096

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/complianceguard

# API
COMPLIANCEGUARD_API_KEY=your_internal_api_key_here
CORS_ORIGINS=http://localhost:5173

# OPA
OPA_POLICY_PATH=./policies/

# Feature Flags
ENABLE_AUTO_FIX=false                      # MVP: false. Post-MVP: true
ENABLE_MULTI_TENANT=false
```

---

## 14. Docker Setup

```yaml
# docker-compose.yml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ARMORIQ_API_KEY=${ARMORIQ_API_KEY}
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/complianceguard
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    volumes:
      - ./frontend:/app

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: complianceguard
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```text
# backend/requirements.txt
fastapi>=0.111
uvicorn[standard]>=0.29
sqlalchemy[asyncio]>=2.0
asyncpg
alembic
pydantic>=2.0
pydantic-settings
armoriq-sdk              # ArmorIQ official SDK — check latest on PyPI
python-dotenv
websockets
httpx
```

---

## 15. Build Order for AI Tools

> Use this sequence with Claude, Cursor, Codex, or any AI assistant to build the project incrementally. Each step is independently testable.

### Phase 1 — Foundation (30 min)
```
STEP 1: Scaffold project structure
  - Create all directories and empty __init__.py / index.ts files as per section 5
  - Copy .env.example → .env (fill in ARMORIQ_API_KEY)

STEP 2: Database layer
  - Implement db/models.py (SQLAlchemy async models from section 11)
  - Implement db/database.py (async session factory)
  - Run Alembic init + first migration

STEP 3: Settings
  - Implement settings.py using pydantic-settings
  - All env vars from section 13 as typed fields
```

### Phase 2 — ArmorIQ Core (45 min)
```
STEP 4: ArmorIQ client
  - Implement armoriq_client.py (section 3.1)
  - Implement ArmorClaw setup (section 3.2)
  - Verify SDK connection with a health check

STEP 5: OPA policies
  - Write all four .rego files (section 9.2 + dependency.rego + access_control.rego)
  - Implement backend/engine/violation_engine.py (section 9.1)
  - Implement backend/policies/opa_runner.py (section 3.5)

STEP 6: Agent tools
  - Implement each tool in backend/agent/tools/ (section 8.3)
  - Each tool must return a typed dict matching the TypeScript interface
  - Unit test each tool independently
```

### Phase 3 — Agent + Engine (45 min)
```
STEP 7: System prompt & scan prompt
  - Write prompts/system_prompt.txt (section 8.1)
  - Write prompts/scan_prompt.txt (build_scan_prompt function)

STEP 8: Agent orchestrator
  - Implement agent/scan_agent.py (section 8.2)
  - Wire ArmorClaw + tools + prompts
  - Test a single scan run against a sample repo directory

STEP 9: Report + Audit
  - Implement engine/report_generator.py (builds Report object from section 6)
  - Implement engine/audit_logger.py (wraps ArmorIQ audit API → writes to audit_events table)
```

### Phase 4 — API Layer (30 min)
```
STEP 10: FastAPI routes
  - Implement all routes from section 7.2
  - POST /api/scan → enqueue scan_agent.run_scan as background task
  - GET routes → query PostgreSQL

STEP 11: WebSocket
  - Implement ws.py
  - broadcast_ws_event function that pushes events from section 7.4
  - Test with wscat: wscat -c ws://localhost:8000/ws/scan-status

STEP 12: Docker
  - Implement docker-compose.yml + Dockerfile (section 14)
  - docker compose up → verify all services start clean
```

### Phase 5 — Frontend (60 min)
```
STEP 13: API client + types
  - Implement frontend/src/types/index.ts (section 6)
  - Implement frontend/src/api/client.ts (Axios with base URL from env)

STEP 14: WebSocket hook + data hook
  - Implement useScanWebSocket.ts (section 10.4)
  - Implement useViolations.ts

STEP 15: Components (build in this order)
  1. StatsBar.tsx     — simple counter cards
  2. ViolationLog.tsx — table with severity/status badges (section 10.2)
  3. ScanTrigger.tsx  — form + POST handler (section 10.3)
  4. ScanStatus.tsx   — WebSocket feed + progress
  5. AuditTrail.tsx   — collapsible event list
  6. ReportViewer.tsx — compliance score ring + download button
  7. Dashboard.tsx    — layout combining all above

STEP 16: End-to-end test
  - Start docker compose
  - Trigger scan via UI
  - Verify violations appear in log
  - Verify audit trail is populated
  - Download report
```

### Phase 6 — CI/CD (15 min)
```
STEP 17: GitHub Action
  - Copy ci/github-action.yml (section 12.1)
  - Add secrets to GitHub repo settings
  - Push a test commit with a known MD5 usage → verify pipeline fails on HIGH violation
```

---

## 16. Acceptance Criteria

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 1 | Scan completes for a sample repo | `POST /api/scan` returns 202, scan reaches COMPLETED status |
| 2 | MD5 usage is detected as HIGH | Violations list contains `category: CRYPTOGRAPHIC, severity: HIGH` |
| 3 | `root` Dockerfile user detected | Violations list contains `category: CONTAINER, severity: HIGH` |
| 4 | Every tool call goes through ArmorIQ | Audit trail has an event for each tool call with ArmorIQ signature |
| 5 | HIGH violations are BLOCKED | Status field on HIGH violations is `BLOCKED` |
| 6 | Report download works | `GET /api/report/{scan_id}` returns valid JSON with all fields |
| 7 | Dashboard shows live updates | WebSocket events appear in UI during active scan |
| 8 | CI/CD pipeline fails on HIGH | GitHub Action exits non-zero when HIGH violations exist |
| 9 | Cryptographic audit log intact | Each audit_event row has non-null `signature` field |
| 10 | OPA policies evaluated correctly | `run_opa_query` tool correctly allows/blocks based on .rego rules |

---

*Spec version 2.0 — ComplianceGuard AI — The Stacktracers*

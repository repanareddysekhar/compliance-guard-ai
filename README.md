# ComplianceGuard AI

Autonomous AI agent for continuous security and compliance monitoring.

## Features
- **Autonomous Scanning**: LLM-powered agent scans source code, Dockerfiles, and dependencies.
- **ArmorIQ Integration**: Every agent action is proxied through ArmorIQ for policy enforcement and cryptographic auditing.
- **OPA Policies**: Uses Open Policy Agent for structured compliance checks.
- **Real-time Dashboard**: Monitor scans and violations in real-time via WebSockets.
- **CI/CD Ready**: Easy integration with GitHub Actions to block non-compliant code.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL), ArmorIQ SDK, OPA, Typer (CLI), MCP Python SDK.
- **Frontend**: React, TypeScript, Tailwind CSS, Lucide React.
- **Infrastructure**: Docker, Docker Compose.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- ArmorIQ API Key

### Installation
1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your `ARMORIQ_API_KEY`.
3. Start the services:
   ```bash
   docker-compose up
   ```

## Usage

### Web Dashboard
Open `http://localhost:5173` to view the real-time compliance dashboard.

### CLI Terminal
Run scans directly from your terminal:
```bash
# Install dependencies first
pip install -r backend/requirements.txt

# Run a scan
python -m backend.cli scan "MyService" "/path/to/repo"

# List previous scans
python -m backend.cli list-scans
```

### MCP (Model Context Protocol)
Integrate ComplianceGuard AI with AI models (like Claude) using MCP:
```bash
# Start the MCP server
python -m backend.mcp_server
```
You can configure this in your Claude Desktop config or any MCP-compatible client.

### API
Trigger scans via HTTP:
```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "MyService",
    "repo_path": "/app/sample-repo"
  }'
```

## Project Structure
- `backend/`: FastAPI service and AI agent.
- `frontend/`: React dashboard.
- `backend/policies/`: OPA `.rego` files.
- `ci/`: CI/CD configuration.

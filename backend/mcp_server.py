import asyncio
import uuid
from typing import List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from backend.agent.scan_agent import run_scan
from backend.db.database import async_session
from backend.db.models import ScanRun, Violation
from sqlalchemy import select

# Initialize MCP Server
app = Server("complianceguard-ai")

@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools for ComplianceGuard AI"""
    return [
        types.Tool(
            name="run_compliance_scan",
            description="Run a security and compliance scan on a repository or service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "The name of the service being scanned"},
                    "repo_path": {"type": "string", "description": "The absolute path to the repository on disk"},
                    "standards": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of standards to check (e.g., FIPS-140-3, CIS-Docker)"
                    }
                },
                "required": ["service_name", "repo_path"]
            }
        ),
        types.Tool(
            name="get_scan_results",
            description="Fetch results and violations for a specific scan ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_id": {"type": "string", "description": "The UUID of the scan run"}
                },
                "required": ["scan_id"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests from the AI model"""
    if name == "run_compliance_scan":
        if not arguments:
            return [types.TextContent(type="text", text="Error: Missing arguments")]
        
        service_name = arguments.get("service_name")
        repo_path = arguments.get("repo_path")
        standards = arguments.get("standards", ["FIPS-140-3", "CIS-Docker", "OWASP-Dependency"])
        
        scan_id = uuid.uuid4()
        
        # We run the scan asynchronously and return the scan_id
        # In a real MCP scenario, we might want to wait or stream, but for now, we'll return the ID
        asyncio.create_task(run_scan(str(scan_id), repo_path, service_name, standards))
        
        return [types.TextContent(
            type="text", 
            text=f"Compliance scan started for {service_name}. Scan ID: {scan_id}. You can check the results using get_scan_results tool once it completes."
        )]

    elif name == "get_scan_results":
        if not arguments or "scan_id" not in arguments:
            return [types.TextContent(type="text", text="Error: Missing scan_id")]
        
        scan_id_str = arguments["scan_id"]
        try:
            scan_id = uuid.UUID(scan_id_str)
        except ValueError:
            return [types.TextContent(type="text", text="Error: Invalid scan_id format")]

        async with async_session() as session:
            v_query = select(Violation).where(Violation.scan_run_id == scan_id)
            v_result = await session.execute(v_query)
            violations = v_result.scalars().all()
            
            s_query = select(ScanRun).where(ScanRun.id == scan_id)
            s_result = await session.execute(s_query)
            scan_run = s_result.scalar_one_or_none()

        if not scan_run:
            return [types.TextContent(type="text", text=f"Scan ID {scan_id_str} not found.")]

        result_text = f"Scan Status: {scan_run.status}\n"
        result_text += f"Violations Found: {len(violations)}\n\n"
        
        for v in violations:
            result_text += f"[{v.severity}] {v.category}: {v.description}\n"
            result_text += f"  File: {v.file_path}:{v.line_number}\n"
            result_text += f"  Remediation: {v.remediation}\n\n"

        return [types.TextContent(type="text", text=result_text)]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="complianceguard-ai",
                server_version="1.0.0",
                capabilities=app.get_capabilities()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

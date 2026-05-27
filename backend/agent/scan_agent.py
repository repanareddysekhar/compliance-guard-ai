from backend.armoriq_shims import ArmorClaw, ToolCallPolicy
from backend.armoriq_client import armoriq
from backend.agent.tools import file_reader, dependency_parser, crypto_checker, opa_query
from backend.settings import settings
import os

# Load system prompt
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()

def build_scan_prompt(repo_path: str, service_name: str, standards: list[str]) -> str:
    return f"""
    Start a compliance scan for the service '{service_name}' located at '{repo_path}'.
    Check against the following standards: {', '.join(standards)}.
    
    1. List the files in the directory.
    2. Scan each file for security and compliance issues.
    3. Check dependencies for known vulnerabilities or banned packages.
    4. Check for insecure cryptographic practices.
    5. Evaluate all findings against the relevant OPA policies.
    """

async def run_scan(scan_run_id: str, repo_path: str, service_name: str, standards: list[str], 
                   on_tool_call=None, on_violation=None, on_event=None):
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
        on_tool_call=on_tool_call,
        on_violation=on_violation,
    ):
        if on_event:
            await on_event(event)

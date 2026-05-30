import inspect
import json
import logging
import time
from typing import Any, Awaitable, Callable

from armoriq_sdk.models import ToolCall
from armoriq_sdk.session import SessionOptions

from backend.agent.llm_client import AgentLLMClient
from backend.armoriq_shims import Tool, ToolCallPolicy
from backend.settings import settings

logger = logging.getLogger(__name__)


def _is_tool_allowed(tool_name: str, policy: ToolCallPolicy) -> tuple[bool, str]:
    if tool_name in policy.blocked_tools:
        return False, f"Tool '{tool_name}' is blocked by policy"
    if policy.allowed_tools and tool_name not in policy.allowed_tools:
        return False, f"Tool '{tool_name}' is not in the allowed tool list"
    return True, "ALLOW"


async def _execute_tool(tool: Tool, tool_input: dict[str, Any]) -> Any:
    result = tool.func(**tool_input)
    if inspect.isawaitable(result):
        result = await result
    return result


def _serialize_tool_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, default=str)


class ArmorClaw:
    """LLM-orchestrated scan agent with ArmorIQ intent verification on tool calls."""

    def __init__(self, client, agent_name: str, tool_policy: ToolCallPolicy):
        self.client = client
        self.agent_name = agent_name
        self.tool_policy = tool_policy

    async def run_async(
        self,
        scan_run_id: str,
        prompt: str,
        tools: list[Tool],
        system: str,
        on_tool_call: Callable[[dict[str, Any]], Awaitable[None] | None] | None = None,
        on_violation: Callable[[dict[str, Any]], Awaitable[None] | None] | None = None,
        on_tool_result: Callable[[str, dict[str, Any], Any], Awaitable[None] | None] | None = None,
    ):
        llm = AgentLLMClient()
        llm.add_user_message(prompt)

        tool_map = {tool.name: tool for tool in tools}
        session = self.client.start_session(
            SessionOptions(
                llm=settings.LLM_MODEL,
                default_mcp_name="ComplianceGuard",
                mode=settings.ARMORIQ_MODE,
            )
        )

        yield {"type": "SCAN_STARTED", "service": self.agent_name, "scan_id": scan_run_id}

        for turn in range(1, settings.LLM_MAX_TURNS + 1):
            turn_result = await llm.run_turn(system, tools)

            if not turn_result.tool_uses:
                if turn_result.text_blocks:
                    yield {
                        "type": "AGENT_SUMMARY",
                        "scan_id": scan_run_id,
                        "summary": turn_result.text_blocks[-1],
                    }
                break

            tool_results: list[dict[str, Any]] = []
            plan_calls = [
                ToolCall(name=block.name, args=block.input)
                for block in turn_result.tool_uses
            ]

            try:
                session.start_plan(plan_calls, goal=f"Compliance scan turn {turn}")
            except Exception as exc:
                logger.warning("ArmorIQ plan capture failed, continuing with local tool policy: %s", exc)

            for block in turn_result.tool_uses:
                tool_name = block.name
                tool_input = block.input
                intent = f"{tool_name}({json.dumps(tool_input, default=str)[:180]})"

                allowed, decision = _is_tool_allowed(tool_name, self.tool_policy)
                if allowed:
                    try:
                        enforce_result = session.check(tool_name, tool_input)
                        if not enforce_result.allowed:
                            allowed = False
                            decision = enforce_result.reason or enforce_result.action.upper()
                    except Exception as exc:
                        logger.warning("ArmorIQ enforce failed for %s: %s", tool_name, exc)

                tool_event = {
                    "type": "TOOL_CALLED",
                    "scan_id": scan_run_id,
                    "tool": tool_name,
                    "intent": intent,
                    "decision": "ALLOW" if allowed else "BLOCK",
                }
                if on_tool_call:
                    maybe = on_tool_call(tool_event)
                    if inspect.isawaitable(maybe):
                        await maybe
                yield tool_event

                if not allowed:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool call blocked by policy: {decision}",
                        "is_error": True,
                    })
                    continue

                started = time.perf_counter()
                try:
                    tool = tool_map[tool_name]
                    result = await _execute_tool(tool, tool_input)
                    session.report(tool_name, tool_input, result)

                    if on_tool_result:
                        maybe = on_tool_result(tool_name, tool_input, result)
                        if inspect.isawaitable(maybe):
                            await maybe

                    if on_violation and tool_name == "check_crypto" and isinstance(result, dict):
                        for violation in result.get("violations", []):
                            payload = {
                                **violation,
                                "file_path": violation.get("file_path") or tool_input.get("file_path"),
                                "category": "CRYPTOGRAPHIC",
                                "source_tool": tool_name,
                            }
                            maybe = on_violation(payload)
                            if inspect.isawaitable(maybe):
                                await maybe
                            yield {
                                "type": "VIOLATION_FOUND",
                                "scan_id": scan_run_id,
                                "violation": payload,
                            }

                    if on_violation and tool_name == "run_opa_query" and isinstance(result, dict):
                        if result.get("allowed") is False:
                            input_data = tool_input.get("input_data", {})
                            payload = {
                                "finding": input_data.get("algorithm", "policy_violation"),
                                "description": "; ".join(result.get("violations", [])) or "OPA policy violation",
                                "remediation": "Replace with FIPS 140-3 approved algorithms.",
                                "file_path": input_data.get("file_path"),
                                "line_number": input_data.get("line_number"),
                                "category": "CRYPTOGRAPHIC",
                                "source_tool": tool_name,
                            }
                            maybe = on_violation(payload)
                            if inspect.isawaitable(maybe):
                                await maybe
                            yield {
                                "type": "VIOLATION_FOUND",
                                "scan_id": scan_run_id,
                                "violation": payload,
                            }

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": _serialize_tool_result(result),
                    })
                except Exception as exc:
                    duration_ms = int((time.perf_counter() - started) * 1000)
                    session.report(tool_name, tool_input, {"error": str(exc)})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool execution failed: {exc}",
                        "is_error": True,
                    })
                    logger.exception("Tool %s failed after %sms", tool_name, duration_ms)

            llm.record_tool_results(turn_result, tool_results)

            if turn_result.stop_reason == "end_turn":
                break
        else:
            yield {
                "type": "AGENT_SUMMARY",
                "scan_id": scan_run_id,
                "summary": "Scan stopped after reaching the maximum number of LLM turns.",
            }

        yield {"type": "SCAN_COMPLETED", "scan_id": scan_run_id}

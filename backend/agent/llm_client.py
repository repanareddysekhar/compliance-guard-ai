import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from backend.armoriq_shims import Tool
from backend.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMTurnResult:
    tool_uses: list[ToolUseBlock] = field(default_factory=list)
    text_blocks: list[str] = field(default_factory=list)
    stop_reason: str = "end_turn"
    raw_assistant_message: dict[str, Any] | None = None
    raw_assistant_content: list[Any] | None = None


def _tool_to_openai_schema(tool: Tool) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param_name, param_def in tool.parameters.items():
        properties[param_name] = {
            "type": param_def.get("type", "string"),
            "description": param_def.get("description", ""),
        }
        if param_def.get("required", True):
            required.append(param_name)

    parameters: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        parameters["required"] = required

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters,
        },
    }


def _tool_to_anthropic_schema(tool: Tool) -> dict[str, Any]:
    openai_schema = _tool_to_openai_schema(tool)["function"]
    return {
        "name": openai_schema["name"],
        "description": openai_schema["description"],
        "input_schema": openai_schema["parameters"],
    }


def _parse_tool_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


class AgentLLMClient:
    """Provider-agnostic tool-calling client. Defaults to local Ollama for POC use."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.messages: list[dict[str, Any]] = []
        self._anthropic_client = None

        if self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
            import anthropic

            self._anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        elif self.provider != "ollama":
            raise RuntimeError(
                f"Unsupported LLM_PROVIDER '{settings.LLM_PROVIDER}'. Use ollama, openai, or anthropic."
            )

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    async def run_turn(self, system: str, tools: list[Tool]) -> LLMTurnResult:
        if self.provider == "anthropic":
            return await self._run_anthropic_turn(system, tools)
        return await self._run_openai_compatible_turn(system, tools)

    def record_tool_results(self, turn: LLMTurnResult, results: list[dict[str, Any]]) -> None:
        if self.provider == "anthropic":
            if turn.raw_assistant_content is not None:
                self.messages.append({"role": "assistant", "content": turn.raw_assistant_content})
            self.messages.append({"role": "user", "content": results})
            return

        if turn.raw_assistant_message is not None:
            self.messages.append(turn.raw_assistant_message)

        for item in results:
            self.messages.append({
                "role": "tool",
                "tool_call_id": item["tool_use_id"],
                "content": item["content"],
            })

    async def _run_openai_compatible_turn(self, system: str, tools: list[Tool]) -> LLMTurnResult:
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "system", "content": system}, *self.messages],
            "tools": [_tool_to_openai_schema(tool) for tool in tools],
            "stream": False,
        }

        headers = {"Content-Type": "application/json"}
        if self.provider == "openai":
            headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"

        url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code >= 400:
                detail = response.text
                try:
                    detail = response.json().get("error", {}).get("message", detail)
                except Exception:
                    pass
                if response.status_code == 404 and "not found" in detail.lower():
                    raise RuntimeError(
                        f"Ollama model '{settings.LLM_MODEL}' not found. "
                        f"Run: ollama pull {settings.LLM_MODEL}"
                    ) from None
                if "does not support tools" in detail.lower():
                    raise RuntimeError(
                        f"Model '{settings.LLM_MODEL}' does not support tool calling. "
                        "Use a tool-capable model such as llama3.2:3b or llama3.1."
                    ) from None
                response.raise_for_status()

            data = response.json()

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}

        tool_uses: list[ToolUseBlock] = []
        for idx, call in enumerate(message.get("tool_calls") or []):
            function = call.get("function") or {}
            tool_uses.append(ToolUseBlock(
                id=call.get("id") or f"call_{idx}",
                name=function.get("name") or "",
                input=_parse_tool_arguments(function.get("arguments")),
            ))

        text = message.get("content")
        text_blocks = [text] if isinstance(text, str) and text.strip() else []

        return LLMTurnResult(
            tool_uses=tool_uses,
            text_blocks=text_blocks,
            stop_reason="tool_calls" if tool_uses else "end_turn",
            raw_assistant_message=message,
        )

    async def _run_anthropic_turn(self, system: str, tools: list[Tool]) -> LLMTurnResult:
        response = await self._anthropic_client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            system=system,
            tools=[_tool_to_anthropic_schema(tool) for tool in tools],
            messages=self.messages,
        )

        tool_uses = [
            ToolUseBlock(
                id=block.id,
                name=block.name,
                input=block.input if isinstance(block.input, dict) else {},
            )
            for block in response.content
            if block.type == "tool_use"
        ]
        text_blocks = [
            block.text for block in response.content
            if block.type == "text" and block.text
        ]

        return LLMTurnResult(
            tool_uses=tool_uses,
            text_blocks=text_blocks,
            stop_reason=response.stop_reason or "end_turn",
            raw_assistant_content=response.content,
        )

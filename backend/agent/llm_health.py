"""Ollama / LLM connectivity checks."""

from __future__ import annotations

import httpx

from backend.settings import settings


class LLMHealthError(RuntimeError):
    pass


def _ollama_root_url() -> str:
    base = settings.LLM_BASE_URL.rstrip("/")
    if base.endswith("/v1"):
        return base[:-3]
    return base


async def check_llm_health() -> dict:
    if settings.LLM_PROVIDER.lower() != "ollama":
        return {"provider": settings.LLM_PROVIDER, "status": "skipped"}

    root = _ollama_root_url()
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            tags_response = await client.get(f"{root}/api/tags")
            tags_response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMHealthError(
                f"Cannot reach Ollama at {root}. Start Ollama or run `docker compose up ollama`."
            ) from exc

        models = [item.get("name") for item in tags_response.json().get("models", [])]
        model = settings.LLM_MODEL
        model_present = any(
            name == model or name.split(":")[0] == model.split(":")[0]
            for name in models
        )
        if not model_present:
            raise LLMHealthError(
                f"Ollama model '{model}' is not installed. Run: ollama pull {model}"
            )

        probe = await client.post(
            f"{root}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "stream": False,
            },
        )
        if probe.status_code == 404:
            detail = probe.json().get("error", {}).get("message", probe.text)
            raise LLMHealthError(
                f"Ollama model '{model}' is unavailable: {detail}. Run: ollama pull {model}"
            )
        probe.raise_for_status()

    return {
        "provider": "ollama",
        "status": "ok",
        "base_url": settings.LLM_BASE_URL,
        "model": settings.LLM_MODEL,
        "installed_models": models,
    }

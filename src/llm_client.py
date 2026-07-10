from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from .env_loader import load_env

load_env()


class LLMConfigError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


def _extract_json_object(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise LLMResponseError("LLM did not return a JSON object.") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"LLM returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMResponseError("LLM JSON response must be an object.")
    return data


def call_chat_json(prompt: str) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        raise LLMConfigError("Missing OPENAI_API_KEY. Set it in .env before running python -m src.")
    if not model:
        raise LLMConfigError("Missing OPENAI_MODEL. Set it in .env before running python -m src.")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你只输出一个合法 JSON 对象，不输出 Markdown、解释或代码块。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        _chat_completions_url(base_url),
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMResponseError(f"LLM HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMResponseError(f"LLM request failed: {exc.reason}") from exc

    try:
        response_data = json.loads(raw)
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise LLMResponseError(f"Unexpected LLM response shape: {raw[:500]}") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMResponseError("LLM returned empty content.")
    return _extract_json_object(content.strip())

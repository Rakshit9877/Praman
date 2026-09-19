"""ai_core/llm.py — Unified async LLM client.

Supports:
  * Anthropic (messages API, base64 images, forced structured output via tool-use)
  * Gemini    (google-genai, response_schema)

Usage:
    from ai_core.llm import LLM
    from my_schemas import MyModel

    llm = LLM()
    result: MyModel = await llm.json_call(
        system="...", user_text="...", images=[...], schema=MyModel,
        prompt_version="v1", sample_idx=0,
    )
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import time
from typing import Any, Type, TypeVar

import tenacity
from pydantic import BaseModel, ValidationError

from ai_core.cache import cache_get, cache_set, compute_input_hash, _make_key
from ai_core.config import settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Global concurrency limiter — prevents hammering the API with too many parallel calls.
_SEMAPHORE = asyncio.Semaphore(4)

_TIMEOUT = 60.0  # seconds per call


# ---------------------------------------------------------------------------
# Retry predicate helpers
# ---------------------------------------------------------------------------

def _is_retryable(exc: BaseException) -> bool:
    """Return True for rate-limit / server errors that warrant a retry."""
    msg = str(exc).lower()
    return any(k in msg for k in ("429", "529", "500", "502", "503", "overloaded", "rate limit"))


# ---------------------------------------------------------------------------
# Anthropic backend
# ---------------------------------------------------------------------------

async def _anthropic_call(
    *,
    system: str,
    user_text: str,
    images: list[bytes] | None,
    schema: type[BaseModel],
    model: str,
    temperature: float | None,
) -> dict[str, Any]:
    """Single attempt via Anthropic messages API with forced tool call."""
    import anthropic  # lazy import — not needed in mock mode

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build content blocks
    content: list[dict] = []
    if images:
        for img_bytes in images:
            b64 = base64.standard_b64encode(img_bytes).decode()
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
    content.append({"type": "text", "text": user_text})

    # Forced tool call for structured output
    tool_name = "structured_output"
    tool_def = {
        "name": tool_name,
        "description": "Return the extracted data as structured JSON matching the schema exactly.",
        "input_schema": schema.model_json_schema(),
    }

    kwargs: dict[str, Any] = dict(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": content}],
        tools=[tool_def],
        tool_choice={"type": "tool", "name": tool_name},
    )
    if temperature is not None:
        kwargs["temperature"] = temperature

    async def _attempt(**kw: Any) -> dict[str, Any]:
        resp = await asyncio.wait_for(client.messages.create(**kw), timeout=_TIMEOUT)
        # Extract the tool-use block
        for block in resp.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input  # type: ignore[return-value]
        raise ValueError("Anthropic returned no tool_use block")

    try:
        return await _attempt(**kwargs)
    except Exception as e:
        if "temperature" in str(e).lower() and temperature is not None:
            log.warning("Provider rejected temperature; retrying without it.")
            kw2 = {k: v for k, v in kwargs.items() if k != "temperature"}
            return await _attempt(**kw2)
        raise


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------

async def _gemini_call(
    *,
    system: str,
    user_text: str,
    images: list[bytes] | None,
    schema: type[BaseModel],
    model: str,
    temperature: float | None,
) -> dict[str, Any]:
    """Single attempt via google-genai SDK."""
    import google.genai as genai  # lazy import
    from google.genai import types as gtypes

    client = genai.Client(api_key=settings.gemini_api_key)

    parts: list[Any] = []
    if images:
        for img_bytes in images:
            parts.append(gtypes.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
    parts.append(gtypes.Part.from_text(text=user_text))

    config_kwargs: dict[str, Any] = {
        "response_mime_type": "application/json",
        "response_schema": schema,
        "system_instruction": system,
    }
    if temperature is not None:
        config_kwargs["temperature"] = temperature

    def _run() -> dict[str, Any]:
        resp = client.models.generate_content(
            model=model,
            contents=[gtypes.Content(role="user", parts=parts)],
            config=gtypes.GenerateContentConfig(**config_kwargs),
        )
        return json.loads(resp.text)

    try:
        return await asyncio.wait_for(asyncio.to_thread(_run), timeout=_TIMEOUT)
    except Exception as e:
        if "temperature" in str(e).lower() and temperature is not None:
            log.warning("Provider rejected temperature; retrying without it.")
            config_kwargs.pop("temperature", None)

            def _run2() -> dict[str, Any]:
                resp = client.models.generate_content(
                    model=model,
                    contents=[gtypes.Content(role="user", parts=parts)],
                    config=gtypes.GenerateContentConfig(**config_kwargs),
                )
                return json.loads(resp.text)

            return await asyncio.wait_for(asyncio.to_thread(_run2), timeout=_TIMEOUT)
        raise


# ---------------------------------------------------------------------------
# Main LLM class
# ---------------------------------------------------------------------------

class LLM:
    """Async LLM client with caching, structured output, and retry logic."""

    def __init__(self) -> None:
        self.provider = settings.llm_provider

    async def json_call(
        self,
        *,
        system: str,
        user_text: str,
        images: list[bytes] | None = None,
        schema: type[T],
        model: str | None = None,
        temperature: float | None = 0.7,
        prompt_version: str = "v1",
        sample_idx: int = 0,
        extra: str = "",
    ) -> T:
        """Call the LLM and return a validated pydantic model instance.

        Caches every call by content hash.  Retries on validation errors (up to 2
        extra attempts, feeding the error back to the model) and on 429/5xx errors.
        """
        effective_model = model or settings.vision_model

        # Build cache key
        image_hash = (
            compute_input_hash(*images) if images else compute_input_hash("")
        )
        key = _make_key(
            provider=self.provider,
            model=effective_model,
            prompt_version=prompt_version,
            sample_idx=sample_idx,
            input_hash=compute_input_hash(image_hash, system, user_text),
            extra=extra,
        )

        cached = cache_get(key)
        if cached is not None:
            return schema.model_validate(cached)

        async with _SEMAPHORE:
            result = await self._call_with_retry(
                system=system,
                user_text=user_text,
                images=images,
                schema=schema,
                model=effective_model,
                temperature=temperature,
                key=key,
            )
        cache_set(key, result.model_dump(mode="json"))
        return result

    @tenacity.retry(
        retry=tenacity.retry_if_exception(_is_retryable),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
        stop=tenacity.stop_after_attempt(4),
        reraise=True,
    )
    async def _call_with_retry(
        self,
        *,
        system: str,
        user_text: str,
        images: list[bytes] | None,
        schema: type[T],
        model: str,
        temperature: float | None,
        key: str,
    ) -> T:
        """Inner call; tenacity handles rate-limit/5xx retries."""
        t0 = time.perf_counter()

        raw: dict[str, Any] | None = None
        last_exc: Exception | None = None

        for attempt in range(3):  # up to 2 validation-error retries
            corrected_system = system
            if last_exc is not None and attempt > 0:
                corrected_system = (
                    system
                    + f"\n\nYour previous response caused a validation error:\n{last_exc}\n"
                    "Please fix the JSON and try again."
                )

            if self.provider == "anthropic":
                raw = await _anthropic_call(
                    system=corrected_system,
                    user_text=user_text,
                    images=images,
                    schema=schema,
                    model=model,
                    temperature=temperature,
                )
            else:
                raw = await _gemini_call(
                    system=corrected_system,
                    user_text=user_text,
                    images=images,
                    schema=schema,
                    model=model,
                    temperature=temperature,
                )

            try:
                validated = schema.model_validate(raw)
                elapsed = time.perf_counter() - t0
                # Best-effort token logging (Anthropic returns usage in the response object,
                # but we don't capture it here to keep the interface clean).
                log.info(
                    "llm_call provider=%s model=%s schema=%s elapsed=%.2fs attempt=%d",
                    self.provider, model, schema.__name__, elapsed, attempt,
                )
                return validated
            except ValidationError as exc:
                last_exc = exc
                log.warning(
                    "ValidationError on attempt %d for %s: %s", attempt, schema.__name__, exc
                )

        # All attempts exhausted
        raise ValueError(
            f"LLM returned invalid {schema.__name__} after 3 attempts. Last error: {last_exc}"
        )

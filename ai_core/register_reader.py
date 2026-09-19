"""ai_core/register_reader.py — STUB (agent RA owns this file).

Do not implement logic here.  This stub exists so imports don't crash with
AttributeError; they will still get a clear NotImplementedError.
"""
from __future__ import annotations
from typing import Callable, Optional


async def read_register(
    image_path: str,
    *,
    target_name: str | None = None,
    progress: Optional[Callable[[str, float], None]] = None,
    n_samples: int | None = None,
):
    raise NotImplementedError("register_reader not merged yet (agent RA)")

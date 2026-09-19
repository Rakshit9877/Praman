"""ai_core/image_prep.py — Pre-process a register photo for LLM vision calls.

Exports:
    PreparedImage  — namedtuple-like dataclass
    prepare(image_path) -> PreparedImage
    save_prepared(prepared, dir) -> Path
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps


# Longest-side limit for the preprocessed image sent to the LLM.
_MAX_SIDE = 1600
_JPEG_QUALITY = 85


@dataclass(frozen=True)
class PreparedImage:
    """Preprocessed image ready for an LLM vision call."""

    bytes_jpeg: bytes          # re-encoded JPEG
    width: int                 # pixel width of preprocessed image
    height: int                # pixel height of preprocessed image
    image_id: str              # sha256(original_bytes)[:16]


def prepare(image_path: str) -> PreparedImage:
    """Load, auto-orient, resize, and re-encode a photo.

    Steps:
    1. Read original bytes; compute image_id from their SHA-256.
    2. Decode with Pillow; apply EXIF transpose (auto-orient).
    3. Convert to RGB (handles RGBA, P, L modes).
    4. Resize so the longest side is at most _MAX_SIDE, preserving aspect ratio.
    5. Re-encode as JPEG quality _JPEG_QUALITY.
    """
    path = Path(image_path)
    original_bytes = path.read_bytes()

    # image_id is derived from the ORIGINAL bytes so it is stable across re-runs.
    image_id = hashlib.sha256(original_bytes).hexdigest()[:16]

    img = Image.open(path)
    img = ImageOps.exif_transpose(img)   # correct camera rotation
    img = img.convert("RGB")

    # Downscale if necessary (never upscale)
    w, h = img.size
    if max(w, h) > _MAX_SIDE:
        scale = _MAX_SIDE / max(w, h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

    w_out, h_out = img.size

    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    jpeg_bytes = buf.getvalue()

    return PreparedImage(
        bytes_jpeg=jpeg_bytes,
        width=w_out,
        height=h_out,
        image_id=image_id,
    )


def save_prepared(prepared: PreparedImage, directory: str | Path) -> Path:
    """Save the preprocessed JPEG to *directory* and return the path."""
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prepared.image_id}.jpg"
    out_path.write_bytes(prepared.bytes_jpeg)
    return out_path

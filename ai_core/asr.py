"""ai_core/asr.py — Audio transcription (Hindi / Hinglish).

Public API
----------
    transcribe(audio_path, *, backend=None) -> (transcript_text, backend_name)

Backends (selected by `backend` param or settings.ASR_BACKEND):
  "whisper"  — faster-whisper WhisperModel, language="hi"
  "gemini"   — Gemini API (optional; raises NotImplementedError if unsupported)
  "mock"     — reads <audio_path>.txt sidecar or returns a fixed demo transcript

Transcripts are cached by audio-file content sha256 via ai_core.cache.
"""
from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ai_core.cache import cache_get, cache_set, compute_input_hash
from ai_core.config import settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixed demo transcript (mock fallback when no sidecar .txt exists)
# ---------------------------------------------------------------------------
_MOCK_DEMO_TRANSCRIPT = (
    "मेरा नाम राकेश है। मैं राजमिस्त्री का काम करता हूँ, करीब दस साल से।"
)

# ---------------------------------------------------------------------------
# Module-level Whisper model cache (load once, reuse across calls)
# ---------------------------------------------------------------------------
_whisper_model: Any = None  # faster_whisper.WhisperModel or None


def _get_whisper_model():
    """Lazily load WhisperModel once and cache it at module level."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel  # type: ignore[import]
        log.info("Loading Whisper model '%s' (int8) — first call only …", settings.whisper_model)
        _whisper_model = WhisperModel(settings.whisper_model, compute_type="int8")
        log.info("Whisper model loaded.")
    return _whisper_model


# ---------------------------------------------------------------------------
# ffmpeg conversion helper
# ---------------------------------------------------------------------------

def _to_16k_wav(audio_path: str) -> str:
    """Convert any audio file to a 16 kHz mono WAV in a temp dir.

    Returns the path to the new WAV file (caller must clean up if needed).
    Raises RuntimeError if ffmpeg is not available.
    """
    # Check ffmpeg availability
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "ffmpeg is required for audio conversion but was not found. "
            "Install it with: brew install ffmpeg  (macOS) or apt install ffmpeg (Linux)."
        ) from exc

    suffix = ".wav"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()
    out_path = tmp.name

    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ar", "16000",   # 16 kHz
        "-ac", "1",       # mono
        "-f", "wav",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")
        raise RuntimeError(f"ffmpeg conversion failed:\n{stderr}")
    return out_path


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _audio_sha256(audio_path: str) -> str:
    """Return sha256 hex of the raw audio file bytes."""
    h = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_key(audio_sha: str, backend: str) -> str:
    """Build a cache key for the ASR result."""
    from ai_core.cache import _make_key
    return _make_key(
        provider="asr",
        model=backend,
        prompt_version="asr_v1",
        sample_idx=0,
        input_hash=compute_input_hash(audio_sha),
        extra="",
    )


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

def _transcribe_whisper(audio_path: str) -> str:
    """Transcribe using faster-whisper with Hindi language settings."""
    model = _get_whisper_model()

    # Convert to 16 kHz mono WAV (works for any input format)
    wav_path = _to_16k_wav(audio_path)
    try:
        segments, _info = model.transcribe(
            wav_path,
            language="hi",
            vad_filter=True,
            beam_size=5,
            initial_prompt=(
                "राजमिस्त्री, ठेकेदार, साइट, मिस्त्री, सरिया, बढ़ई, "
                "गुड़गाँव, नोएडा, मोहाली, चंडीगढ़"
            ),
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass
    return text


def _transcribe_gemini(audio_path: str) -> str:
    """Transcribe using the Gemini API (audio input).

    Raises NotImplementedError if the google-genai SDK does not support audio
    file transcription in the version installed.
    """
    if not settings.gemini_api_key:
        raise NotImplementedError(
            "Gemini ASR backend requires GEMINI_API_KEY to be set."
        )
    try:
        import google.genai as genai  # type: ignore[import]
        from google.genai import types as gtypes  # type: ignore[import]
    except ImportError as exc:
        raise NotImplementedError(
            "google-genai package is not installed. "
            "Install it with: pip install google-genai"
        ) from exc

    # Read audio bytes and determine MIME type
    ext = Path(audio_path).suffix.lower()
    mime_map = {
        ".m4a": "audio/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".ogg": "audio/ogg",
    }
    mime_type = mime_map.get(ext, "audio/mp4")

    audio_bytes = Path(audio_path).read_bytes()

    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        audio_part = gtypes.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        text_part = gtypes.Part.from_text(
            text="Transcribe this audio exactly as spoken in Hindi (Devanagari script). "
                 "Return only the transcript, nothing else."
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[gtypes.Content(role="user", parts=[audio_part, text_part])],
        )
        return (response.text or "").strip()
    except Exception as exc:
        raise NotImplementedError(
            f"Gemini audio transcription failed: {exc}. "
            "This may be unsupported in the current google-genai version."
        ) from exc


def _transcribe_mock(audio_path: str) -> str:
    """Return transcript from a sidecar .txt file or the fixed demo string."""
    sidecar = Path(str(audio_path) + ".txt")
    if sidecar.exists():
        text = sidecar.read_text(encoding="utf-8").strip()
        log.debug("mock ASR: using sidecar file %s", sidecar)
        return text
    log.debug("mock ASR: no sidecar found, returning fixed demo transcript")
    return _MOCK_DEMO_TRANSCRIPT


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def transcribe(audio_path: str, *, backend: str | None = None) -> tuple[str, str]:
    """Transcribe an audio file and return (transcript_text, backend_name).

    Args:
        audio_path: Path to the audio file (m4a / mp3 / wav / webm / …).
        backend:    Override the backend to use. If None, uses settings.ASR_BACKEND.

    Returns:
        A tuple of (transcript_text, backend_name) where backend_name is the
        string identifier of the backend that was used ("whisper"|"gemini"|"mock").

    Raises:
        FileNotFoundError: If audio_path does not exist (except mock backend).
        RuntimeError: If ffmpeg is missing (whisper backend).
        NotImplementedError: If gemini backend is not supported.
    """
    effective_backend = backend or settings.asr_backend

    # Check file existence for non-mock backends
    if effective_backend != "mock" and not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Try the disk cache first (keyed by content sha256)
    audio_sha = _audio_sha256(audio_path) if Path(audio_path).exists() else "mock"
    key = _cache_key(audio_sha, effective_backend)

    cached = cache_get(key)
    if cached is not None:
        log.debug("ASR cache hit for %s (backend=%s)", audio_path, effective_backend)
        return cached["transcript"], cached["backend"]

    # --- Run the chosen backend ---
    log.info("ASR transcribing %s with backend=%s", audio_path, effective_backend)

    if effective_backend == "whisper":
        text = _transcribe_whisper(audio_path)
    elif effective_backend == "gemini":
        text = _transcribe_gemini(audio_path)
    elif effective_backend == "mock":
        text = _transcribe_mock(audio_path)
    else:
        raise ValueError(
            f"Unknown ASR backend: {effective_backend!r}. "
            "Valid options: 'whisper', 'gemini', 'mock'."
        )

    log.info("ASR result (%s): %r", effective_backend, text[:80])

    # Store in cache
    cache_set(key, {"transcript": text, "backend": effective_backend})

    return text, effective_backend

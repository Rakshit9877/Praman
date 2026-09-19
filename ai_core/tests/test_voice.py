"""ai_core/tests/test_voice.py — Unit tests for the voice pipeline.

Runs without network access. Marked tests that need real APIs are
decorated with @pytest.mark.live and excluded by the CI / definition-of-done
command:  pytest -q -m "not live" ai_core/tests/test_voice.py
"""
from __future__ import annotations

import asyncio
import os
import struct
import tempfile
import wave
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tone_wav(path: str, duration_s: float = 1.0, sample_rate: int = 16000) -> None:
    """Write a 1-second mono PCM 16-bit WAV with a 440 Hz tone (no external deps)."""
    import math

    n_samples = int(sample_rate * duration_s)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            # 440 Hz sine wave, amplitude ~50% of 16-bit max
            sample_val = int(16383 * math.sin(2 * math.pi * 440 * i / sample_rate))
            wf.writeframes(struct.pack("<h", sample_val))


def _write_silent_wav(path: str, duration_s: float = 1.0, sample_rate: int = 16000) -> None:
    """Write a 1-second silent mono PCM 16-bit WAV."""
    n_samples = int(sample_rate * duration_s)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)


# ---------------------------------------------------------------------------
# Tests for asr._to_16k_wav (ffmpeg path)
# ---------------------------------------------------------------------------

class TestFfmpegConversion:
    """Test that _to_16k_wav doesn't crash on a valid WAV input file."""

    def test_silent_wav_conversion_passes(self, tmp_path):
        """A WAV that ffmpeg can already read should convert without error."""
        pytest.importorskip("ai_core.asr")
        from ai_core import asr

        # Build a silent WAV in the temp dir
        input_wav = str(tmp_path / "silent.wav")
        _write_silent_wav(input_wav)

        # If ffmpeg is not installed, skip gracefully
        try:
            out = asr._to_16k_wav(input_wav)
        except RuntimeError as exc:
            if "ffmpeg is required" in str(exc):
                pytest.skip("ffmpeg not installed — skipping ffmpeg conversion test")
            raise

        assert Path(out).exists(), "Output WAV file should exist"
        assert Path(out).stat().st_size > 0, "Output WAV should not be empty"
        # Clean up
        os.unlink(out)

    def test_tone_wav_conversion_passes(self, tmp_path):
        """A 1-second tone WAV should survive the ffmpeg round-trip."""
        from ai_core import asr

        input_wav = str(tmp_path / "tone.wav")
        _write_tone_wav(input_wav)

        try:
            out = asr._to_16k_wav(input_wav)
        except RuntimeError as exc:
            if "ffmpeg is required" in str(exc):
                pytest.skip("ffmpeg not installed — skipping tone conversion test")
            raise

        assert Path(out).exists()
        os.unlink(out)


# ---------------------------------------------------------------------------
# Tests for asr.transcribe — mock backend
# ---------------------------------------------------------------------------

class TestMockBackend:
    """Tests for the 'mock' ASR backend."""

    def test_mock_returns_demo_transcript_without_sidecar(self, tmp_path):
        """When no .txt sidecar exists, mock returns the fixed demo string."""
        from ai_core import asr

        # Create a dummy audio file (content irrelevant for mock)
        audio = tmp_path / "test.m4a"
        audio.write_bytes(b"\x00" * 16)

        text, backend = asr.transcribe(str(audio), backend="mock")

        assert backend == "mock"
        assert "राकेश" in text, f"Expected demo transcript, got: {text!r}"

    def test_mock_returns_sidecar_content_when_present(self, tmp_path):
        """When a .txt sidecar exists, mock returns its content."""
        from ai_core import asr

        audio = tmp_path / "test.m4a"
        audio.write_bytes(b"\x00" * 16)

        sidecar = tmp_path / "test.m4a.txt"
        expected = "Mera naam Ravi hai. Main electrician hoon, teen saal se."
        sidecar.write_text(expected, encoding="utf-8")

        # Force a cache miss so we hit the actual sidecar-reading logic.
        with patch("ai_core.asr.cache_get", return_value=None), \
             patch("ai_core.asr.cache_set"):
            text, backend = asr.transcribe(str(audio), backend="mock")

        assert backend == "mock"
        assert text == expected

    def test_mock_cache_is_used_on_second_call(self, tmp_path):
        """Second call with same content should hit the cache."""
        from ai_core import asr

        audio = tmp_path / "test.m4a"
        audio.write_bytes(b"\xAB\xCD" * 8)

        # First call — populates cache
        with patch("ai_core.asr.cache_get", return_value=None) as mock_cget, \
             patch("ai_core.asr.cache_set") as mock_cset:
            text1, _ = asr.transcribe(str(audio), backend="mock")
            assert mock_cset.called, "cache_set should be called after first transcription"

        # Simulate a pre-populated cache hit on the second call.
        cached_value = {"transcript": text1, "backend": "mock"}
        with patch("ai_core.asr.cache_get", return_value=cached_value) as mock_cget2:
            text2, backend2 = asr.transcribe(str(audio), backend="mock")
            assert mock_cget2.called, "cache_get should be called on second call"

        assert text1 == text2
        assert backend2 == "mock"


# ---------------------------------------------------------------------------
# Tests for process_voice — transcript_override path
# Fixture to override AI_MODE for tests that exercise the real pipeline path
import pytest

@pytest.fixture(autouse=False)
def real_mode(monkeypatch):
    """Force ai_mode=real so process_voice exercises the non-mock path."""
    from ai_core import config as cfg_mod
    monkeypatch.setattr(cfg_mod.settings, "ai_mode", "real")
    yield

# ---------------------------------------------------------------------------

class TestProcessVoiceOverride:
    """Tests for process_voice using transcript_override (skips ASR)."""

    def _make_llm_mock(self, result_dict: dict) -> Any:
        """Build a mock LLM that returns canned data for json_call."""
        from ai_core.voice import _LLMVoiceOutput

        llm_output = _LLMVoiceOutput(**result_dict)

        mock_llm = MagicMock()
        mock_llm.json_call = AsyncMock(return_value=llm_output)
        return mock_llm

    @pytest.mark.asyncio
    async def test_transcript_override_skips_asr(self, real_mode):
        """When transcript_override is given, no ASR module should be called."""
        from ai_core import voice
        from contracts.schemas import VoiceClaim

        transcript = "Mera naam Imran hai, carpenter hoon, paanch saal se."

        with patch("ai_core.voice.LLM") as mock_llm_class:
            mock_llm_class.return_value = self._make_llm_mock({
                "name": "Imran",
                "trade": "carpenter",
                "years_experience": 5.0,
                "sites": [],
                "confidence": 0.75,
            })

            with patch("ai_core.asr.transcribe") as mock_transcribe:
                claim = await voice.process_voice(
                    transcript_override=transcript,
                )
                # ASR must NOT have been called
                mock_transcribe.assert_not_called()

        assert isinstance(claim, VoiceClaim)
        assert claim.transcript == transcript
        assert claim.asr_backend == "override"
        assert claim.language == "hi"
        assert len(claim.claim_id) == 12

    @pytest.mark.asyncio
    async def test_schema_valid_voice_claim_returned(self, real_mode):
        """process_voice must return a schema-valid VoiceClaim."""
        from ai_core import voice
        from contracts.schemas import Trade, VoiceClaim

        with patch("ai_core.voice.LLM") as mock_llm_class:
            mock_llm_class.return_value = self._make_llm_mock({
                "name": "राकेश",
                "trade": "mason",
                "years_experience": 10.0,
                "sites": [
                    {
                        "site_name": "DLF Site",
                        "city": "Gurugram",
                        "employer_name": "Sunil",
                        "approx_from_year": 2018,
                        "approx_to_year": 2022,
                    }
                ],
                "confidence": 1.0,
            })

            claim = await voice.process_voice(
                transcript_override="मेरा नाम राकेश है, राजमिस्त्री हूँ, दस साल से।"
            )

        # Pydantic validation — will raise if schema is violated
        validated = VoiceClaim.model_validate(claim.model_dump(mode="json"))
        assert validated.trade == Trade.mason
        assert validated.years_experience == 10.0
        assert validated.name == "राकेश"
        assert len(validated.sites) == 1
        assert validated.sites[0].city == "Gurugram"
        assert validated.confidence > 0.0

    @pytest.mark.asyncio
    async def test_confidence_heuristic_all_fields(self, real_mode):
        """Confidence = 1.0 when all four key fields are present."""
        from ai_core import voice

        with patch("ai_core.voice.LLM") as mock_llm_class:
            mock_llm_class.return_value = self._make_llm_mock({
                "name": "Suresh",
                "trade": "bar_bender",
                "years_experience": 7.5,
                "sites": [{"site_name": None, "city": "Noida", "employer_name": None}],
                "confidence": 1.0,
            })
            claim = await voice.process_voice(transcript_override="test")

        assert claim.confidence == 1.0

    @pytest.mark.asyncio
    async def test_confidence_heuristic_partial_fields(self, real_mode):
        """Confidence = 0.25 when only trade is extracted."""
        from ai_core import voice

        with patch("ai_core.voice.LLM") as mock_llm_class:
            mock_llm_class.return_value = self._make_llm_mock({
                "name": None,
                "trade": "painter",
                "years_experience": None,
                "sites": [],
                "confidence": 0.0,
            })
            claim = await voice.process_voice(transcript_override="Main painter hoon.")

        assert claim.confidence == 0.25

    @pytest.mark.asyncio
    async def test_no_audio_and_no_override_raises(self, real_mode):
        """Calling process_voice with neither path nor override should raise ValueError."""
        from ai_core import voice

        with pytest.raises(ValueError, match="audio_path or transcript_override"):
            await voice.process_voice()

    @pytest.mark.asyncio
    async def test_progress_callback_called(self, real_mode):
        """The progress callback should be invoked at key pipeline stages."""
        from ai_core import voice

        stages_seen = []

        def _progress(stage: str, frac: float) -> None:
            stages_seen.append((stage, frac))

        with patch("ai_core.voice.LLM") as mock_llm_class:
            mock_llm_class.return_value = self._make_llm_mock({
                "name": "Test",
                "trade": "plumber",
                "years_experience": 3.0,
                "sites": [{"city": "Delhi"}],
                "confidence": 1.0,
            })
            await voice.process_voice(
                transcript_override="Test transcript",
                progress=_progress,
            )

        stage_names = [s for s, _ in stages_seen]
        assert "extracting claims" in stage_names
        assert "done" in stage_names


# ---------------------------------------------------------------------------
# Table-driven extraction test (stubbed LLM, tests trade mapping)
# ---------------------------------------------------------------------------

class TestTradeMapping:
    """Verify that the LLM output is correctly assembled into VoiceClaim."""

    CASES = [
        # (trade_value, expected_Trade)
        ("mason",        "mason"),
        ("carpenter",    "carpenter"),
        ("bar_bender",   "bar_bender"),
        ("plumber",      "plumber"),
        ("electrician",  "electrician"),
        ("painter",      "painter"),
        ("welder",       "welder"),
        ("tiler",        "tiler"),
        ("helper",       "helper"),
        ("other",        "other"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("trade_str,expected", CASES)
    async def test_trade_round_trips(self, trade_str, expected, real_mode):
        """Each valid Trade enum value must round-trip through VoiceClaim."""
        from ai_core import voice
        from contracts.schemas import Trade

        with patch("ai_core.voice.LLM") as mock_llm_class:
            mock_llm = MagicMock()
            from ai_core.voice import _LLMVoiceOutput
            mock_llm.json_call = AsyncMock(
                return_value=_LLMVoiceOutput(trade=Trade(trade_str))
            )
            mock_llm_class.return_value = mock_llm

            claim = await voice.process_voice(transcript_override="dummy")

        assert claim.trade == Trade(expected)


# ---------------------------------------------------------------------------
# Live tests (excluded from CI by -m "not live")
# ---------------------------------------------------------------------------

@pytest.mark.live
def test_live_whisper_on_voice_files():
    """Run the full pipeline on real audio files if they exist.

    Requires: faster-whisper installed, WHISPER_MODEL downloadable,
    data/voice/*.m4a or *.wav present.
    """
    import json
    import glob

    audio_files = glob.glob("data/voice/*.m4a") + glob.glob("data/voice/*.wav")
    if not audio_files:
        pytest.skip("No audio files in data/voice/ — skipping live test")

    import asyncio
    from ai_core import asr

    for audio_path in audio_files[:2]:  # limit to first 2 files
        text, backend = asr.transcribe(audio_path, backend="whisper")
        assert isinstance(text, str)
        assert len(text) > 0, f"Empty transcript for {audio_path}"
        print(f"\n[live] {Path(audio_path).name} → {text[:80]!r}")

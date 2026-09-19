"""ai_core/tests/test_scaffold.py — Unit tests for R0 scaffold (no network).

Covers:
  * cache hit / miss / replay-only behaviour
  * mock functions return schema-valid objects for every api.py signature
  * api.py dispatches to mock.py when AI_MODE=mock
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Ensure AI_MODE=mock for all tests in this module
# ---------------------------------------------------------------------------
os.environ.setdefault("AI_MODE", "mock")
os.environ.setdefault("AI_CACHE", "on")


# ===========================================================================
# Cache tests
# ===========================================================================

class TestCache:
    """Cache hit / miss / replay-only behaviour (no LLM calls)."""

    def _fresh_settings(self, mode: str, tmp_dir: str):
        """Return a patched settings object for the given cache mode."""
        import importlib
        import ai_core.cache as cache_mod
        return cache_mod

    def test_cache_miss_returns_none(self, tmp_path):
        """A key that was never written returns None in 'on' mode."""
        with patch("ai_core.cache.settings") as mock_settings:
            mock_settings.ai_cache = "on"
            mock_settings.cache_dir = str(tmp_path)
            from ai_core.cache import cache_get
            assert cache_get("nonexistent_key_abc123") is None

    def test_cache_set_then_get(self, tmp_path):
        """Writing then reading returns the same value."""
        with patch("ai_core.cache.settings") as mock_settings:
            mock_settings.ai_cache = "on"
            mock_settings.cache_dir = str(tmp_path)
            from ai_core.cache import cache_get, cache_set
            payload = {"answer": 42, "nested": {"x": "y"}}
            cache_set("mykey", payload)
            result = cache_get("mykey")
            assert result == payload

    def test_cache_off_never_reads_or_writes(self, tmp_path):
        """In 'off' mode, cache_get always returns None and cache_set is a no-op."""
        with patch("ai_core.cache.settings") as mock_settings:
            mock_settings.ai_cache = "off"
            mock_settings.cache_dir = str(tmp_path)
            from ai_core.cache import cache_get, cache_set
            cache_set("somekey", {"data": 1})
            assert cache_get("somekey") is None
            # No files should be written
            assert list(tmp_path.iterdir()) == []

    def test_replay_only_hit(self, tmp_path):
        """In replay-only mode, a pre-existing key can be read."""
        key = "replay_test_key"
        cache_file = tmp_path / f"{key}.json"
        cache_file.write_text(json.dumps({"ok": True}), encoding="utf-8")

        with patch("ai_core.cache.settings") as mock_settings:
            mock_settings.ai_cache = "replay-only"
            mock_settings.cache_dir = str(tmp_path)
            from ai_core.cache import cache_get
            result = cache_get(key)
            assert result == {"ok": True}

    def test_replay_only_miss_raises(self, tmp_path):
        """In replay-only mode, a missing key raises CacheMiss."""
        from ai_core.cache import CacheMiss
        with patch("ai_core.cache.settings") as mock_settings:
            mock_settings.ai_cache = "replay-only"
            mock_settings.cache_dir = str(tmp_path)
            from ai_core.cache import cache_get
            with pytest.raises(CacheMiss):
                cache_get("definitely_not_here")

    def test_replay_only_does_not_write(self, tmp_path):
        """In replay-only mode, cache_set is a no-op."""
        with patch("ai_core.cache.settings") as mock_settings:
            mock_settings.ai_cache = "replay-only"
            mock_settings.cache_dir = str(tmp_path)
            from ai_core.cache import cache_set
            cache_set("somekey", {"data": 1})
            assert list(tmp_path.iterdir()) == []

    def test_make_key_is_deterministic(self):
        """Same inputs always produce the same cache key."""
        from ai_core.cache import _make_key
        k1 = _make_key("anthropic", "claude-3", "v1", 0, "abc", "")
        k2 = _make_key("anthropic", "claude-3", "v1", 0, "abc", "")
        assert k1 == k2

    def test_make_key_differs_on_model(self):
        """Different model → different key."""
        from ai_core.cache import _make_key
        k1 = _make_key("anthropic", "claude-3", "v1", 0, "abc", "")
        k2 = _make_key("anthropic", "claude-4", "v1", 0, "abc", "")
        assert k1 != k2

    def test_compute_input_hash_bytes(self):
        """compute_input_hash returns a hex string from bytes."""
        from ai_core.cache import compute_input_hash
        h = compute_input_hash(b"hello", b"world")
        assert isinstance(h, str) and len(h) == 64


# ===========================================================================
# Mock function tests — schema validity
# ===========================================================================

class TestMockSchemaValidity:
    """Mock functions must return schema-valid objects."""

    @pytest.mark.asyncio
    async def test_mock_read_register_returns_valid_schema(self, tmp_path):
        """mock_read_register returns a valid RegisterExtraction."""
        from contracts.schemas import RegisterExtraction
        from ai_core.mock import mock_read_register

        fake_img = tmp_path / "R00.jpg"
        fake_img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)  # minimal JPEG header

        result = await mock_read_register(str(fake_img))
        assert isinstance(result, RegisterExtraction)
        assert result.extraction_id
        assert result.n_samples >= 1
        assert len(result.rows) >= 1

    @pytest.mark.asyncio
    async def test_mock_process_voice_returns_valid_schema(self):
        """mock_process_voice returns a valid VoiceClaim."""
        from contracts.schemas import VoiceClaim
        from ai_core.mock import mock_process_voice

        result = await mock_process_voice(audio_path=None, transcript_override="test")
        assert isinstance(result, VoiceClaim)
        assert result.claim_id
        assert 0.0 <= result.confidence <= 1.0

    def test_mock_build_work_record_returns_valid_schema(self, tmp_path):
        """mock_build_work_record returns a valid WorkRecord."""
        from contracts.schemas import (
            ConfirmRegisterIn, Origin, WorkRecord,
            RegisterExtraction, RegisterHeader, ReadField,
        )
        from ai_core.mock import mock_build_work_record, mock_read_register

        # Build a minimal extraction synchronously via inline helper
        from ai_core.mock import _minimal_register_extraction
        extraction = RegisterExtraction.model_validate(
            _minimal_register_extraction("fake.jpg")
        )
        confirm = ConfirmRegisterIn(
            worker_id="w-test-1",
            target_row_index=0,
            corrections=[],
        )
        result = mock_build_work_record(extraction, confirm, worker_id="w-test-1")
        assert isinstance(result, WorkRecord)
        assert result.worker_id == "w-test-1"
        assert result.days_worked >= 0

    def test_mock_reconcile_returns_valid_schema(self):
        """mock_reconcile returns a valid ReconciliationReport."""
        from contracts.schemas import ReconciliationReport
        from ai_core.mock import mock_reconcile

        result = mock_reconcile(None, [])
        assert isinstance(result, ReconciliationReport)
        assert result.verified_days >= 0
        assert result.verified_sites >= 0

    def test_mock_score_passport_returns_valid_schema(self):
        """mock_score_passport returns a (TrustResult, dict[str, WageBand]) tuple."""
        from contracts.schemas import ReconciliationReport, TrustResult, WageBand
        from ai_core.mock import mock_reconcile, mock_score_passport

        report = mock_reconcile(None, [])
        trust, bands = mock_score_passport(None, [], report)

        assert isinstance(trust, TrustResult)
        assert 0 <= trust.score <= 100
        assert trust.level in ("low", "medium", "high")

        for area in ("A", "B", "C"):
            assert area in bands
            assert isinstance(bands[area], WageBand)


# ===========================================================================
# api.py dispatch tests
# ===========================================================================

class TestApiDispatch:
    """api.py must dispatch to mock.py when AI_MODE=mock."""

    @pytest.mark.asyncio
    async def test_api_read_register_dispatches_to_mock(self, tmp_path, monkeypatch):
        """api.read_register → mock_read_register in mock mode."""
        monkeypatch.setenv("AI_MODE", "mock")
        # Reload settings so monkeypatch takes effect
        import importlib
        import ai_core.config as cfg
        importlib.reload(cfg)
        # Reload api to pick up the new settings
        import ai_core.api as api_mod
        importlib.reload(api_mod)

        fake_img = tmp_path / "R00.jpg"
        fake_img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)

        from contracts.schemas import RegisterExtraction
        result = await api_mod.read_register(str(fake_img))
        assert isinstance(result, RegisterExtraction)

    @pytest.mark.asyncio
    async def test_api_process_voice_dispatches_to_mock(self, monkeypatch):
        """api.process_voice → mock_process_voice in mock mode."""
        monkeypatch.setenv("AI_MODE", "mock")
        import importlib
        import ai_core.config as cfg
        importlib.reload(cfg)
        import ai_core.api as api_mod
        importlib.reload(api_mod)

        from contracts.schemas import VoiceClaim
        result = await api_mod.process_voice(transcript_override="test")
        assert isinstance(result, VoiceClaim)

    def test_api_reconcile_dispatches_to_mock(self, monkeypatch):
        """api.reconcile → mock_reconcile in mock mode."""
        monkeypatch.setenv("AI_MODE", "mock")
        import importlib
        import ai_core.config as cfg
        importlib.reload(cfg)
        import ai_core.api as api_mod
        importlib.reload(api_mod)

        from contracts.schemas import ReconciliationReport
        result = api_mod.reconcile(None, [])
        assert isinstance(result, ReconciliationReport)

    def test_api_score_passport_dispatches_to_mock(self, monkeypatch):
        """api.score_passport → mock_score_passport in mock mode."""
        monkeypatch.setenv("AI_MODE", "mock")
        import importlib
        import ai_core.config as cfg
        importlib.reload(cfg)
        import ai_core.api as api_mod
        importlib.reload(api_mod)

        from contracts.schemas import ReconciliationReport, TrustResult, WageBand
        from ai_core.mock import mock_reconcile
        report = mock_reconcile(None, [])

        trust, bands = api_mod.score_passport(None, [], report)
        assert isinstance(trust, TrustResult)
        assert set(bands.keys()) == {"A", "B", "C"}

    def test_api_build_work_record_dispatches_to_mock(self, monkeypatch):
        """api.build_work_record → mock_build_work_record in mock mode."""
        monkeypatch.setenv("AI_MODE", "mock")
        import importlib
        import ai_core.config as cfg
        importlib.reload(cfg)
        import ai_core.api as api_mod
        importlib.reload(api_mod)

        from contracts.schemas import ConfirmRegisterIn, RegisterExtraction, WorkRecord
        from ai_core.mock import _minimal_register_extraction
        extraction = RegisterExtraction.model_validate(_minimal_register_extraction("x.jpg"))
        confirm = ConfirmRegisterIn(worker_id="w-1", target_row_index=0)

        result = api_mod.build_work_record(extraction, confirm, worker_id="w-1")
        assert isinstance(result, WorkRecord)


# ===========================================================================
# Config tests
# ===========================================================================

class TestConfig:
    def test_settings_loads_without_error(self):
        """Settings singleton is importable and has expected attributes."""
        from ai_core.config import settings
        assert settings.ai_mode in ("mock", "real")
        assert settings.ai_cache in ("on", "off", "replay-only")
        assert settings.readers >= 1

    def test_get_rules_returns_dict(self):
        """get_rules() returns a dict with expected keys."""
        from ai_core.config import get_rules
        rules = get_rules()
        assert isinstance(rules, dict)
        assert "skilled_trades" in rules
        assert "skill_thresholds" in rules

    def test_get_wage_table_returns_dict(self):
        """get_wage_table() returns a dict with areas A/B/C."""
        from ai_core.config import get_wage_table
        table = get_wage_table()
        assert isinstance(table, dict)
        assert "areas" in table
        assert set(table["areas"].keys()) >= {"A", "B", "C"}

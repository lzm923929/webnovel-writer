#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from data_modules.error_catalog import classify_issue, format_author_error, load_catalog


def test_error_catalog_loads_known_entries_and_fallback():
    entries, fallback = load_catalog()

    codes = {entry.code for entry in entries}
    assert "mainline_ready=false" in codes
    assert "projection pending" in codes
    assert fallback.matched is False
    assert fallback.severity == "must_handle"


def test_error_catalog_classifies_schema_error_by_code():
    result = classify_issue(
        {
            "code": "artifact.schema_error",
            "message": "field required: accepted_events",
        }
    )

    assert result.code == "artifact.schema_error"
    assert result.severity == "must_handle"
    assert result.auto_handle is False
    assert "中间结果格式不完整" in format_author_error(result)


def test_error_catalog_distinguishes_projection_pending_from_failed():
    pending = classify_issue(
        {
            "code": "projection_status_missing",
            "message": "projection pending: vector is missing",
        }
    )
    failed = classify_issue(
        {
            "code": "projection_failure",
            "message": "projection failed: vector timeout",
        }
    )

    assert pending.code == "projection pending"
    assert pending.severity == "needs_confirmation"
    assert failed.code == "projection failed"
    assert failed.severity == "must_handle"


def test_error_catalog_classifies_rag_fallback_as_auto_handled():
    result = classify_issue("RAG fallback used because vector search timed out")

    assert result.code == "rag degraded"
    assert result.severity == "auto_handled"
    assert result.auto_handle is True


def test_error_catalog_unknown_error_honestly_falls_back():
    result = classify_issue({"code": "new.runtime.error", "message": "unexpected traceback"})

    assert result.matched is False
    assert result.code == "unknown"
    assert "/webnovel-doctor" in result.next_action

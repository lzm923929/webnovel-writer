#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


EXTRACTION_FIELDS = (
    "accepted_events",
    "state_deltas",
    "entity_deltas",
    "entities_appeared",
    "scenes",
    "chapter_meta",
    "dominant_strand",
    "summary_text",
)


def extraction_result_from_commit(commit_payload: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical extraction artifact from a commit.

    New commits store the extraction snapshot under ``extraction_result``.
    Older commits stored these fields at top level, so this helper keeps
    projections readable without preserving two write shapes. If the
    canonical nested artifact exists, it is the only source of truth.
    """
    nested = commit_payload.get("extraction_result")
    if isinstance(nested, dict):
        return dict(nested)

    result: dict[str, Any] = {}
    for field in EXTRACTION_FIELDS:
        if field in commit_payload:
            result[field] = commit_payload.get(field)
    return result


def extraction_list(commit_payload: dict[str, Any], field: str) -> list[Any]:
    value = extraction_result_from_commit(commit_payload).get(field)
    return value if isinstance(value, list) else []


def extraction_dict(commit_payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = extraction_result_from_commit(commit_payload).get(field)
    return value if isinstance(value, dict) else {}


def extraction_text(commit_payload: dict[str, Any], field: str) -> str:
    value = extraction_result_from_commit(commit_payload).get(field)
    return str(value or "").strip()

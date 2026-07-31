#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.commit_artifacts import (
    extraction_list,
    extraction_result_from_commit,
    extraction_text,
)


def test_extraction_result_prefers_canonical_nested_payload():
    payload = {
        "extraction_result": {
            "accepted_events": [{"event_id": "nested"}],
            "summary_text": "nested summary",
        },
        "accepted_events": [{"event_id": "legacy"}],
        "summary_text": "legacy summary",
    }

    extraction = extraction_result_from_commit(payload)

    assert extraction["accepted_events"] == [{"event_id": "nested"}]
    assert extraction["summary_text"] == "nested summary"
    assert extraction_list(payload, "accepted_events") == [{"event_id": "nested"}]
    assert extraction_text(payload, "summary_text") == "nested summary"


def test_extraction_result_keeps_read_compatibility_for_legacy_commit_payload():
    payload = {
        "accepted_events": [{"event_id": "legacy"}],
        "summary_text": "legacy summary",
    }

    extraction = extraction_result_from_commit(payload)

    assert extraction["accepted_events"] == [{"event_id": "legacy"}]
    assert extraction["summary_text"] == "legacy summary"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

from .test_project_phase import _make_contracts, _make_init_ready


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_on_path()

from data_modules.project_status import (  # noqa: E402
    SCHEMA_VERSION,
    build_project_status,
    format_project_status,
)


def test_project_status_json_shape(tmp_path):
    _make_init_ready(tmp_path)
    _make_contracts(tmp_path, chapter=1)

    report = build_project_status(tmp_path)

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["project"] == "测试书"
    assert report["phase"] == "chapter_contract_ready"
    assert report["target_chapter"] == 1
    assert report["next_action"] == "run /webnovel-write 1"


def test_project_status_summary_is_short_and_machine_source_is_json(tmp_path):
    _make_init_ready(tmp_path)
    report = build_project_status(tmp_path)

    summary = format_project_status(report, "summary")
    payload = json.loads(format_project_status(report, "json"))

    assert "phase: init_ready" in summary
    assert payload["schema_version"] == SCHEMA_VERSION


def test_project_status_handles_no_project():
    report = build_project_status(None)

    assert report["phase"] == "no_project"
    assert report["blocking"]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_on_path()

from data_modules.project_phase import (  # noqa: E402
    INIT_REQUIRED_DIRS,
    INIT_REQUIRED_FILES,
    PHASE_CHAPTER_CONTRACT_READY,
    PHASE_DRAFT_IN_PROGRESS,
    PHASE_INIT_READY,
    PHASE_INIT_SCAFFOLDED,
    PHASE_PROJECTION_FAILED,
    PHASE_READY_TO_COMMIT,
    COMMIT_ARTIFACT_FILES,
    resolve_project_phase,
)
from data_modules.projection_log import append_projection_run  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _make_init_ready(project_root: Path) -> None:
    for rel in INIT_REQUIRED_DIRS:
        (project_root / rel).mkdir(parents=True, exist_ok=True)
    for rel in INIT_REQUIRED_FILES:
        path = project_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".json"):
            _write_json(
                path,
                {
                    "project_info": {"title": "测试书", "genre": "玄幻"},
                    "progress": {"current_chapter": 0},
                },
            )
        else:
            path.write_text("placeholder\n", encoding="utf-8")


def _make_contracts(project_root: Path, chapter: int = 1) -> None:
    _write_json(project_root / ".story-system" / "MASTER_SETTING.json", {"meta": {"contract_type": "MASTER_SETTING"}})
    _write_json(project_root / ".story-system" / "volumes" / "volume_001.json", {"meta": {"volume": 1}})
    _write_json(project_root / ".story-system" / "chapters" / f"chapter_{chapter:03d}.json", {"meta": {"chapter": chapter}})
    _write_json(
        project_root / ".story-system" / "reviews" / f"chapter_{chapter:03d}.review.json",
        {"meta": {"chapter": chapter}},
    )


def test_project_phase_reports_init_scaffolded_when_core_files_missing(tmp_path):
    _write_json(tmp_path / ".webnovel" / "state.json", {"project_info": {}, "progress": {}})

    snapshot = resolve_project_phase(tmp_path)

    assert snapshot.phase == PHASE_INIT_SCAFFOLDED
    assert "大纲/总纲.md" in snapshot.missing_init_files
    assert snapshot.blocking


def test_project_phase_reports_init_ready_after_init_scaffold(tmp_path):
    _make_init_ready(tmp_path)

    snapshot = resolve_project_phase(tmp_path)

    assert snapshot.phase == PHASE_INIT_READY
    assert snapshot.target_chapter == 1
    assert snapshot.blocking == ()


def test_project_phase_detects_chapter_contract_ready(tmp_path):
    _make_init_ready(tmp_path)
    _make_contracts(tmp_path, chapter=1)

    snapshot = resolve_project_phase(tmp_path)

    assert snapshot.phase == PHASE_CHAPTER_CONTRACT_READY
    assert snapshot.missing_contract_files == ()


def test_project_phase_detects_draft_and_ready_to_commit(tmp_path):
    _make_init_ready(tmp_path)
    _make_contracts(tmp_path, chapter=1)
    (tmp_path / "正文" / "第0001章.md").write_text("正文草稿\n", encoding="utf-8")

    draft_snapshot = resolve_project_phase(tmp_path)
    assert draft_snapshot.phase == PHASE_DRAFT_IN_PROGRESS

    for rel in COMMIT_ARTIFACT_FILES:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    ready_snapshot = resolve_project_phase(tmp_path)
    assert ready_snapshot.phase == PHASE_READY_TO_COMMIT


def test_project_phase_detects_projection_failed(tmp_path):
    _make_init_ready(tmp_path)
    _write_json(
        tmp_path / ".story-system" / "commits" / "chapter_001.commit.json",
        {
            "meta": {"chapter": 1, "status": "accepted"},
            "projection_status": {"state": "done", "index": "failed:locked"},
        },
    )

    snapshot = resolve_project_phase(tmp_path)

    assert snapshot.phase == PHASE_PROJECTION_FAILED
    assert "latest_commit_projection_failed" in snapshot.blocking


def test_project_phase_prefers_projection_log_over_commit_status(tmp_path):
    _make_init_ready(tmp_path)
    commit_path = tmp_path / ".story-system" / "commits" / "chapter_001.commit.json"
    commit_payload = {
        "meta": {"chapter": 1, "status": "accepted"},
        "projection_status": {"state": "done", "index": "done", "vector": "done"},
    }
    _write_json(commit_path, commit_payload)
    append_projection_run(
        tmp_path,
        commit_payload,
        {"vector": {"status": "failed:timeout", "error": "timeout"}},
        commit_path=commit_path,
    )

    snapshot = resolve_project_phase(tmp_path)

    assert snapshot.phase == PHASE_PROJECTION_FAILED
    assert snapshot.latest_commit is not None
    assert snapshot.latest_commit.projection_source == "projection_log"
    assert snapshot.latest_commit.projection_status["vector"] == "failed:timeout"


def test_project_phase_treats_projection_log_pending_as_blocking(tmp_path):
    _make_init_ready(tmp_path)
    commit_path = tmp_path / ".story-system" / "commits" / "chapter_001.commit.json"
    commit_payload = {
        "meta": {"chapter": 1, "status": "accepted"},
        "projection_status": {"state": "done"},
    }
    _write_json(commit_path, commit_payload)
    append_projection_run(
        tmp_path,
        commit_payload,
        {"state": {"status": "pending"}},
        commit_path=commit_path,
    )

    snapshot = resolve_project_phase(tmp_path)

    assert snapshot.phase == PHASE_PROJECTION_FAILED
    assert "latest_commit_projection_incomplete" in snapshot.blocking

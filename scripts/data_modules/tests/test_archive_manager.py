#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pytest


def _load_archive_module():
    import sys

    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    import archive_manager

    return archive_manager


@pytest.fixture
def archive_env(tmp_path):
    webnovel = tmp_path / ".webnovel"
    webnovel.mkdir(parents=True, exist_ok=True)
    state_path = webnovel / "state.json"
    state_path.write_text(
        '{"progress":{"current_chapter":10},"plot_threads":{},"review_checkpoints":[]}',
        encoding="utf-8",
    )
    return tmp_path


def test_archive_remove_from_state_missing_sections(archive_env):
    module = _load_archive_module()
    manager = module.ArchiveManager(project_root=archive_env)

    state = {
        "progress": {"current_chapter": 50},
    }

    updated = manager.remove_from_state(state, inactive_chars=[], resolved_threads=[], old_reviews=[])
    assert updated.get("progress", {}).get("current_chapter") == 50


def test_archive_check_trigger_conditions_edges(archive_env):
    module = _load_archive_module()
    manager = module.ArchiveManager(project_root=archive_env)

    manager.config["chapter_trigger"] = 10
    manager.config["file_size_trigger_mb"] = 9999.0

    trigger = manager.check_trigger_conditions({"progress": {"current_chapter": 20}})
    assert trigger["chapter_trigger"] is True
    assert trigger["should_archive"] is True


def test_archive_identify_old_reviews_handles_mixed_formats(archive_env):
    module = _load_archive_module()
    manager = module.ArchiveManager(project_root=archive_env)
    manager.config["review_old_threshold"] = 5

    state = {
        "progress": {"current_chapter": 30},
        "review_checkpoints": [
            {"chapters": "20-22", "report": "r1.md"},
            {"chapter_range": [10, 12], "date": "2026-01-01"},
            {"report": "Review_Ch5-6.md"},
        ],
    }

    results = manager.identify_old_reviews(state)
    assert len(results) == 3
    assert all(row["chapters_since_review"] >= 5 for row in results)


def test_save_archive_uses_atomic_write_json(archive_env, monkeypatch):
    module = _load_archive_module()
    manager = module.ArchiveManager(project_root=archive_env)
    calls = []

    def fake_atomic_write_json(path, data, *, use_lock=True, backup=True, indent=2):
        calls.append((path, data, use_lock, backup, indent))
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(module, "atomic_write_json", fake_atomic_write_json)

    manager.save_archive(manager.characters_archive, [{"name": "李雪"}])

    assert calls == [(manager.characters_archive, [{"name": "李雪"}], True, True, 2)]


def test_restore_character_keeps_archive_when_sqlite_restore_fails(archive_env, monkeypatch):
    module = _load_archive_module()
    manager = module.ArchiveManager(project_root=archive_env)
    archived = [
        {
            "id": "li_xue",
            "name": "李雪",
            "tier": "支线",
            "archived_at": "2026-06-10T00:00:00",
        }
    ]
    manager.characters_archive.write_text(json.dumps(archived, ensure_ascii=False), encoding="utf-8")
    before = manager.characters_archive.read_text(encoding="utf-8")

    def fail_restore(*args, **kwargs):
        raise RuntimeError("sqlite down")

    monkeypatch.setattr(manager._index_manager, "update_entity_field", fail_restore)

    assert manager.restore_character("李雪") is False
    assert manager.characters_archive.read_text(encoding="utf-8") == before


def test_restore_character_deletes_archive_after_sqlite_restore_succeeds(archive_env, monkeypatch):
    module = _load_archive_module()
    manager = module.ArchiveManager(project_root=archive_env)
    archived = [
        {
            "id": "li_xue",
            "name": "李雪",
            "tier": "支线",
            "archived_at": "2026-06-10T00:00:00",
        }
    ]
    manager.characters_archive.write_text(json.dumps(archived, ensure_ascii=False), encoding="utf-8")
    calls = []

    def restore_status(entity_id, field, value):
        calls.append((entity_id, field, value))

    monkeypatch.setattr(manager._index_manager, "update_entity_field", restore_status)

    assert manager.restore_character("李雪") is True
    assert calls == [("li_xue", "status", "active")]
    assert json.loads(manager.characters_archive.read_text(encoding="utf-8")) == []


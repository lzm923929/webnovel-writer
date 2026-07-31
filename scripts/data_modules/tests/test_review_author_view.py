#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from data_modules.review_author_view import build_review_author_view, render_review_author_view


def _payload(issues, *, summary=""):
    return {
        "chapter": 1,
        "review_result": {
            "issues": issues,
            "issues_count": len(issues),
            "blocking_count": sum(1 for issue in issues if issue.get("blocking")),
            "has_blocking": any(issue.get("blocking") for issue in issues),
            "summary": summary,
        },
        "metrics": {},
    }


def test_review_author_view_marks_blocking_as_must_fix():
    view = build_review_author_view(
        _payload(
            [
                {
                    "severity": "critical",
                    "category": "timeline",
                    "location": "第2段",
                    "description": "时间线回跳",
                    "fix_hint": "补一句从深夜到清晨的过渡",
                    "blocking": True,
                },
                {
                    "severity": "medium",
                    "description": "节奏略慢",
                    "fix_hint": "压缩解释",
                },
            ]
        )
    )

    assert view.status == "must_fix"
    assert view.verdict == "⛔必须先改"
    assert len(view.actions) == 1
    assert "时间线回跳" in view.actions[0]
    assert "补一句" in view.actions[0]


def test_review_author_view_limits_actions_to_three_and_prioritizes_severity():
    issues = [
        {"severity": "low", "description": "低优先级"},
        {"severity": "medium", "description": "中优先级"},
        {"severity": "high", "description": "高优先级"},
        {"severity": "critical", "description": "严重但非阻断", "blocking": False},
    ]

    view = build_review_author_view(_payload(issues))

    assert view.status == "suggest_fix"
    assert view.verdict == "⚠️建议改"
    assert len(view.actions) == 3
    assert "严重但非阻断" in view.actions[0]
    assert "高优先级" in view.actions[1]
    assert "中优先级" in view.actions[2]


def test_review_author_view_allows_clean_chapter_to_continue():
    view = build_review_author_view(_payload([], summary="整体可继续"))

    assert view.status == "can_continue"
    assert view.verdict == "✅可以继续"
    assert view.actions == ("整体可继续",)


def test_review_author_view_render_has_author_section():
    rendered = render_review_author_view(
        _payload(
            [
                {
                    "severity": "high",
                    "location": "第5段",
                    "description": "人物动机不清",
                    "fix_hint": "补一句内心取舍",
                }
            ]
        )
    )

    assert rendered.startswith("## 作者视图")
    assert "本章结论：⚠️建议改" in rendered
    assert "人物动机不清" in rendered

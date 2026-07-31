#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "webnovel-author-error-catalog/v1"
VALID_SEVERITIES = {"auto_handled", "needs_confirmation", "must_handle"}


@dataclass(frozen=True)
class AuthorError:
    code: str
    severity: str
    title: str
    reason: str
    impact: str
    next_action: str
    command: str = ""
    auto_handle: bool = False
    matched: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "reason": self.reason,
            "impact": self.impact,
            "next_action": self.next_action,
            "command": self.command,
            "auto_handle": self.auto_handle,
            "matched": self.matched,
        }


@dataclass(frozen=True)
class ErrorCatalogEntry:
    code: str
    match_codes: tuple[str, ...]
    match_contains: tuple[str, ...]
    error: AuthorError


def default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "references" / "author_error_catalog.json"


def _coerce_error(raw: dict[str, Any], *, matched: bool = True) -> AuthorError:
    severity = str(raw.get("severity") or "must_handle")
    if severity not in VALID_SEVERITIES:
        severity = "must_handle"
    return AuthorError(
        code=str(raw.get("code") or "unknown"),
        severity=severity,
        title=str(raw.get("title") or "遇到问题"),
        reason=str(raw.get("reason") or "系统没有提供具体原因。"),
        impact=str(raw.get("impact") or "当前结果需要确认。"),
        next_action=str(raw.get("next_action") or "运行 `/webnovel-doctor` 查看详情。"),
        command=str(raw.get("command") or ""),
        auto_handle=bool(raw.get("auto_handle")),
        matched=matched,
    )


def _load_payload(path: str | Path | None = None) -> dict[str, Any]:
    catalog_path = Path(path) if path else default_catalog_path()
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def load_catalog(path: str | Path | None = None) -> tuple[list[ErrorCatalogEntry], AuthorError]:
    payload = _load_payload(path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unknown author error catalog schema: {payload.get('schema_version')}")

    entries: list[ErrorCatalogEntry] = []
    for raw in payload.get("errors") or []:
        if not isinstance(raw, dict):
            continue
        match = raw.get("match") if isinstance(raw.get("match"), dict) else {}
        match_codes = tuple(str(item).strip() for item in match.get("codes") or [] if str(item).strip())
        match_contains = tuple(str(item).strip() for item in match.get("contains") or [] if str(item).strip())
        error = _coerce_error(raw, matched=True)
        entries.append(
            ErrorCatalogEntry(
                code=error.code,
                match_codes=match_codes or (error.code,),
                match_contains=match_contains,
                error=error,
            )
        )

    fallback_raw = payload.get("fallback") if isinstance(payload.get("fallback"), dict) else {}
    fallback = _coerce_error({"code": "unknown", **fallback_raw}, matched=False)
    return entries, fallback


@lru_cache(maxsize=1)
def _default_catalog() -> tuple[list[ErrorCatalogEntry], AuthorError]:
    return load_catalog()


def _haystack_from_issue(issue: Any) -> tuple[str, str]:
    if isinstance(issue, dict):
        code = str(issue.get("code") or issue.get("id") or issue.get("type") or "").strip()
        text_parts = [
            code,
            str(issue.get("message") or ""),
            str(issue.get("reason") or ""),
            str(issue.get("impact") or ""),
            str(issue.get("repair") or ""),
            str(issue.get("actual") or ""),
        ]
        return code, "\n".join(text_parts)
    text = str(issue or "")
    return text.strip(), text


def classify_issue(
    issue: Any,
    *,
    catalog: tuple[list[ErrorCatalogEntry], AuthorError] | None = None,
) -> AuthorError:
    entries, fallback = catalog if catalog is not None else _default_catalog()
    code, text = _haystack_from_issue(issue)
    lower_text = text.lower()
    lower_code = code.lower()

    for entry in entries:
        if any(lower_code == item.lower() for item in entry.match_codes):
            return entry.error
        if any(item.lower() in lower_text for item in entry.match_contains):
            return entry.error
    return fallback


def format_author_error(error: AuthorError) -> str:
    lines = [
        f"{error.title}",
        f"- 原因：{error.reason}",
        f"- 影响：{error.impact}",
        f"- 下一步：{error.next_action}",
    ]
    if error.command:
        lines.append(f"- 可用命令：{error.command}")
    return "\n".join(lines)

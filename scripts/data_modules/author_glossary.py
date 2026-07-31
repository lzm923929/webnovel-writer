#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "webnovel-author-glossary/v1"


@dataclass(frozen=True)
class AuthorTerm:
    technical: str
    author: str
    explanation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "technical": self.technical,
            "author": self.author,
            "explanation": self.explanation,
        }


def default_glossary_path() -> Path:
    return Path(__file__).resolve().parents[2] / "references" / "author_glossary.json"


def _load_payload(path: str | Path | None = None) -> dict[str, Any]:
    glossary_path = Path(path) if path else default_glossary_path()
    return json.loads(glossary_path.read_text(encoding="utf-8"))


def load_terms(path: str | Path | None = None) -> dict[str, AuthorTerm]:
    payload = _load_payload(path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unknown author glossary schema: {payload.get('schema_version')}")
    terms: dict[str, AuthorTerm] = {}
    for raw in payload.get("terms") or []:
        if not isinstance(raw, dict):
            continue
        technical = str(raw.get("technical") or "").strip()
        author = str(raw.get("author") or "").strip()
        explanation = str(raw.get("explanation") or "").strip()
        if not technical or not author or not explanation:
            continue
        terms[technical] = AuthorTerm(
            technical=technical,
            author=author,
            explanation=explanation,
        )
    return terms


@lru_cache(maxsize=1)
def _default_terms() -> dict[str, AuthorTerm]:
    return load_terms()


def lookup(term: str, *, terms: dict[str, AuthorTerm] | None = None) -> AuthorTerm | None:
    term = str(term or "").strip()
    if not term:
        return None
    source = terms if terms is not None else _default_terms()
    if term in source:
        return source[term]
    lower_map = {key.lower(): value for key, value in source.items()}
    return lower_map.get(term.lower())


def author_label(term: str, *, terms: dict[str, AuthorTerm] | None = None) -> str:
    found = lookup(term, terms=terms)
    return found.author if found else str(term)


def explain(term: str, *, terms: dict[str, AuthorTerm] | None = None) -> str:
    found = lookup(term, terms=terms)
    if found:
        return found.explanation
    return f"{term}：系统暂未登记这个术语，先按原词显示。"

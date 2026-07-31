#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from data_modules.author_glossary import (
    author_label,
    default_glossary_path,
    explain,
    load_terms,
    lookup,
)


def test_author_glossary_loads_single_source():
    terms = load_terms()

    assert default_glossary_path().is_file()
    assert terms["projection"].author == "更新故事资料"
    assert terms["mainline_ready"].author == "这本书的档案是否就绪"
    assert terms["write-gate"].explanation


def test_author_glossary_lookup_is_case_insensitive():
    terms = load_terms()

    found = lookup("chapter_commit", terms=terms)
    assert found is not None
    assert found.author == "本章事实存档"
    assert author_label("CHAPTER_COMMIT", terms=terms) == "本章事实存档"


def test_author_glossary_unknown_term_falls_back_to_original():
    terms = load_terms()

    assert author_label("unknown_runtime_word", terms=terms) == "unknown_runtime_word"
    assert "unknown_runtime_word" in explain("unknown_runtime_word", terms=terms)

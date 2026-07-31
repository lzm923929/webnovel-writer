#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_on_path()

from run_behavior_evals import run_behavior_evals  # noqa: E402


def test_run_behavior_evals_fast_suite_passes_for_current_package():
    root = Path(__file__).resolve().parents[2]

    report = run_behavior_evals(root, suite="fast")

    assert report["ok"] is True
    assert report["total"] >= 5

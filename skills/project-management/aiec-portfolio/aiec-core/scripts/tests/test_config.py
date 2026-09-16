"""Guard-gedrag (Fable, ontwerpfase)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import config  # noqa: E402


def cfg(mode):
    c = config._merge(config.DEFAULTS, {"writes": {"mode": mode}})
    c["_path"] = "<test>"
    return c


def test_dry_run_allows_without_apply():
    config.guard(cfg("dry-run"), "confluence", "AI", apply=False)
    config.guard(cfg("dry-run"), "jira", "AI", apply=False)


def test_dry_run_refuses_apply():
    with pytest.raises(config.GuardRefused):
        config.guard(cfg("dry-run"), "confluence", "AI", apply=True)
    with pytest.raises(config.GuardRefused):
        config.guard(cfg("dry-run"), "confluence", "~vancrake", apply=True)


def test_test_mode_only_test_space():
    config.guard(cfg("test"), "confluence", "~vancrake", apply=True)
    with pytest.raises(config.GuardRefused):
        config.guard(cfg("test"), "confluence", "AI", apply=True)
    with pytest.raises(config.GuardRefused):
        config.guard(cfg("test"), "jira", "AI", apply=True)


def test_production():
    config.guard(cfg("production"), "confluence", "AI", apply=True)
    config.guard(cfg("production"), "jira", "AI", apply=True)
    config.guard(cfg("production"), "jira", "EAG", apply=True)
    with pytest.raises(config.GuardRefused):
        config.guard(cfg("production"), "jira", "POR", apply=True)
    with pytest.raises(config.GuardRefused):
        config.guard(cfg("production"), "confluence", "TD", apply=True)


def test_unknown_mode_rejected(tmp_path, monkeypatch):
    p = tmp_path / "config.toml"
    p.write_text('[writes]\nmode = "yolo"\n')
    with pytest.raises(ValueError):
        config.load(str(p))

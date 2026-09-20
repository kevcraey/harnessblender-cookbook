"""Client is alleen-lezen; writer() is de guard (Fable, ontwerpfase)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import config, http  # noqa: E402


def cfg(mode):
    c = config._merge(config.DEFAULTS, {"writes": {"mode": mode}})
    c["_path"] = "<test>"
    return c


def test_client_refuses_writes_before_any_socket():
    c = http.Client("http://127.0.0.1:9", "t")
    with pytest.raises(config.GuardRefused):
        c.post("/x", {"a": 1})
    with pytest.raises(config.GuardRefused):
        c.put("/x", {"a": 1})


def test_writer_without_apply_is_readonly(monkeypatch):
    monkeypatch.setattr(http, "token", lambda kind: "t")
    c = http.writer(cfg("dry-run"), "confluence", "AI", apply=False)
    assert c.writable is False
    with pytest.raises(config.GuardRefused):
        c.post("/x", {})


def test_writer_with_apply_respects_mode(monkeypatch):
    monkeypatch.setattr(http, "token", lambda kind: "t")
    with pytest.raises(config.GuardRefused):
        http.writer(cfg("dry-run"), "confluence", "AI", apply=True)
    with pytest.raises(config.GuardRefused):
        http.writer(cfg("test"), "jira", "AI", apply=True)
    c = http.writer(cfg("test"), "confluence", "~vancrake", apply=True)
    assert c.writable is True and c.scope == "~vancrake"
    c = http.writer(cfg("production"), "jira", "EAG", apply=True)
    assert c.writable is True

from __future__ import annotations

import importlib.util
import os
import stat
from pathlib import Path

import pytest

_HELPER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "nanou-admin-session.py"
_SPEC = importlib.util.spec_from_file_location("nanou_admin_session_helper", _HELPER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_HELPER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPER)


def test_private_socket_directory_is_created_with_owner_only_access(tmp_path, monkeypatch) -> None:
    home = tmp_path / "termux-home"
    home.mkdir(mode=0o700)
    socket_dir = home / ".local" / "run" / "nanou-cyber-admin"
    monkeypatch.setattr(_HELPER, "HOME", home)
    monkeypatch.setattr(_HELPER, "SOCKET_DIR", socket_dir)
    monkeypatch.setattr(_HELPER, "SOCKET_PATH", str(socket_dir / "bridge.sock"))

    _HELPER.prepare_socket_path()

    assert stat.S_IMODE(os.lstat(socket_dir).st_mode) == 0o700
    assert stat.S_ISDIR(os.lstat(socket_dir).st_mode)


def test_private_socket_path_refuses_symlinked_directory_without_chmodding_target(
    tmp_path, monkeypatch
) -> None:
    home = tmp_path / "termux-home"
    home.mkdir(mode=0o700)
    local = home / ".local"
    local.mkdir(mode=0o700)
    run_dir = local / "run"
    run_dir.mkdir(mode=0o700)
    target = tmp_path / "unrelated"
    target.mkdir(mode=0o755)
    socket_dir = run_dir / "nanou-cyber-admin"
    socket_dir.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(_HELPER, "HOME", home)
    monkeypatch.setattr(_HELPER, "SOCKET_DIR", socket_dir)
    monkeypatch.setattr(_HELPER, "SOCKET_PATH", str(socket_dir / "bridge.sock"))
    before_mode = stat.S_IMODE(os.lstat(target).st_mode)

    with pytest.raises(RuntimeError, match="symlink or non-directory"):
        _HELPER.prepare_socket_path()

    assert stat.S_IMODE(os.lstat(target).st_mode) == before_mode


def test_private_socket_path_refuses_to_replace_regular_file(tmp_path, monkeypatch) -> None:
    home = tmp_path / "termux-home"
    home.mkdir(mode=0o700)
    socket_dir = home / ".local" / "run" / "nanou-cyber-admin"
    monkeypatch.setattr(_HELPER, "HOME", home)
    monkeypatch.setattr(_HELPER, "SOCKET_DIR", socket_dir)
    socket_path = socket_dir / "bridge.sock"
    monkeypatch.setattr(_HELPER, "SOCKET_PATH", str(socket_path))
    _HELPER.prepare_socket_path()
    socket_path.write_text("not a socket", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Refusing to replace"):
        _HELPER.prepare_socket_path()

    assert socket_path.read_text(encoding="utf-8") == "not a socket"


def test_http_redirects_are_rejected() -> None:
    handler = _HELPER.RejectRedirects()
    request = object()
    response = object()
    assert (
        handler.redirect_request(request, response, 302, "Found", {}, "https://evil.invalid")
        is None
    )

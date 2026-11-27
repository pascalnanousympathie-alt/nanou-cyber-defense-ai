#!/usr/bin/env python3
"""Short-lived, read-only Admin bridge for Nanou Cyber Defense AI.

The pairing code is entered with getpass, exchanged over HTTPS, and never
persisted or printed. The resulting bearer token stays in memory and is
exposed only through a private 0600 Unix socket with fixed read-only actions.
"""

from __future__ import annotations

import getpass
import json
import os
import socket
import socketserver
import stat
import sys
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://nanou-cyber-defense-ai.vercel.app"
HOME = Path(os.environ.get("HOME", str(Path.home())))
SOCKET_DIR = HOME / ".local" / "run" / "nanou-cyber-admin"
SOCKET_PATH = str(SOCKET_DIR / "bridge.sock")
MAX_RESPONSE_BYTES = 1_000_000
ALLOWED_ACTIONS = {"ping", "whoami", "users", "audit"}


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class ApiError(RuntimeError):
    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.status = status


class AdminBridgeApi:
    def __init__(self) -> None:
        self.cookies = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies), RejectRedirects())
        self.csrf_token = ""
        self.bridge_token = ""

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict | None = None,
        csrf: bool = False,
        bridge_auth: bool = False,
    ) -> dict | list:
        if not path.startswith("/") or "://" in path or ".." in path:
            raise ValueError("Invalid fixed API path")
        headers = {"Accept": "application/json"}
        body = None
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if csrf:
            headers["X-CSRF-Token"] = self.csrf_token
            headers["Origin"] = BASE_URL
        if bridge_auth:
            headers["Authorization"] = f"Bearer {self.bridge_token}"
        request = Request(BASE_URL + path, data=body, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise RuntimeError("API response exceeded size limit")
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ApiError(exc.code) from None
        except (URLError, TimeoutError, OSError):
            raise RuntimeError("Cannot reach the Nanou Cyber Defense API") from None

    def _load_csrf(self) -> None:
        payload = self._request("GET", "/api/auth/csrf")
        token = payload.get("csrf_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise RuntimeError("CSRF initialization failed")
        self.csrf_token = token

    def pair(self, pairing_code: str) -> dict:
        if not pairing_code.startswith("ncd_pair_") or len(pairing_code) > 160:
            raise ValueError("Pairing code format is invalid")
        self._load_csrf()
        payload = self._request(
            "POST",
            "/api/auth/pairing/exchange",
            payload={"pairing_code": pairing_code},
            csrf=True,
        )
        token = payload.get("bridge_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token.startswith("ncd_bridge_"):
            raise RuntimeError("The server did not issue a read-only bridge token")
        self.bridge_token = token
        try:
            identity = self.me()
            if (
                identity.get("role") != "admin"
                or identity.get("is_active") is not True
                or identity.get("is_approved") is not True
            ):
                raise PermissionError("The paired account is not an active approved Admin")
        except Exception:
            self.revoke()
            raise
        return payload

    def me(self) -> dict:
        result = self._request("GET", "/api/admin/bridge/me", bridge_auth=True)
        if not isinstance(result, dict):
            raise RuntimeError("Unexpected identity response")
        return result

    def read_action(self, action: str) -> dict | list:
        if action not in ALLOWED_ACTIONS:
            raise ValueError("Allowed actions: ping, whoami, users, audit")
        if action in {"ping", "whoami"}:
            return self.me()
        if action == "users":
            result = self._request("GET", "/api/admin/bridge/users", bridge_auth=True)
            if not isinstance(result, list):
                raise RuntimeError("Unexpected users response")
            return result
        result = self._request("GET", "/api/admin/bridge/audit?limit=100", bridge_auth=True)
        if not isinstance(result, list):
            raise RuntimeError("Unexpected audit response")
        return result

    def revoke(self) -> None:
        if not self.bridge_token:
            return
        try:
            self._request(
                "POST",
                "/api/admin/bridge/revoke",
                payload={},
                csrf=True,
                bridge_auth=True,
            )
        except Exception:
            # Server-side expiry is the fallback if the phone loses connectivity.
            pass
        finally:
            self.bridge_token = ""


class Handler(socketserver.StreamRequestHandler):
    timeout = 5

    def handle(self) -> None:
        line = self.rfile.readline(4097)
        if not line or len(line) > 4096:
            return
        try:
            request = json.loads(line.decode("utf-8"))
            action = request.get("action") if isinstance(request, dict) else None
            if action not in ALLOWED_ACTIONS:
                raise ValueError("Unsupported action")
            result = self.server.api.read_action(action)
            response = {"ok": True, "result": result}
        except ApiError as exc:
            response = {"ok": False, "error": f"API_HTTP_{exc.status}"}
        except Exception:
            response = {"ok": False, "error": "ADMIN_BRIDGE_REQUEST_FAILED"}
        encoded = (json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8")
        self.wfile.write(encoded)


class Server(socketserver.UnixStreamServer):
    def __init__(self, address: str, api: AdminBridgeApi):
        self.api = api
        self.daemon_threads = True
        super().__init__(address, Handler)


def prepare_socket_path() -> None:
    private_directories = (
        HOME / ".local",
        HOME / ".local" / "run",
        SOCKET_DIR,
    )
    for directory in private_directories:
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = os.lstat(directory)
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise RuntimeError("Refusing a symlink or non-directory in the private socket path")
        if info.st_uid != os.getuid():
            raise RuntimeError("The private socket directory is not owned by this Termux user")
    os.chmod(SOCKET_DIR, 0o700)
    if not os.path.lexists(SOCKET_PATH):
        return
    mode = os.lstat(SOCKET_PATH).st_mode
    if not stat.S_ISSOCK(mode):
        raise RuntimeError("Refusing to replace a non-socket file")
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.connect(SOCKET_PATH)
    except OSError:
        os.unlink(SOCKET_PATH)
    else:
        raise RuntimeError("An Admin bridge is already running")
    finally:
        probe.close()


def main() -> int:
    print("Nanou Cyber Defense AI — read-only Admin bridge", flush=True)
    print("Mamorona pairing code ao amin'ny navigateur Admin, dia apetaho eto.", flush=True)
    pairing_code = getpass.getpass("Pairing code (hidden): ").strip()
    if not pairing_code:
        print("Pairing code is required.", file=sys.stderr)
        return 2

    api = AdminBridgeApi()
    try:
        pairing = api.pair(pairing_code)
    except ApiError as exc:
        print(
            f"Pairing HTTP {exc.status}; code mety lany daty na efa nampiasaina.",
            file=sys.stderr,
        )
        return 3
    except PermissionError:
        print("Pairing rejected: the account is not an active approved Admin.", file=sys.stderr)
        return 4
    except Exception:
        print("Pairing failed. Create a new code and try again.", file=sys.stderr)
        return 5
    finally:
        pairing_code = ""

    expires_at = pairing.get("expires_at", "unknown")
    pairing.pop("bridge_token", None)
    server = None
    try:
        prepare_socket_path()
        server = Server(SOCKET_PATH, api)
        os.chmod(SOCKET_PATH, 0o600)
    except Exception as exc:
        if server is not None:
            server.server_close()
        try:
            if stat.S_ISSOCK(os.lstat(SOCKET_PATH).st_mode):
                os.unlink(SOCKET_PATH)
        except OSError:
            pass
        api.revoke()
        print(f"Cannot create private local bridge: {exc}", file=sys.stderr)
        return 6

    print("ADMIN_BRIDGE_READY — role=admin; scope=read-only; token held in memory.", flush=True)
    print(f"Expires at: {expires_at}", flush=True)
    print("Avelao hisokatra ity Termux ity. Ctrl+C dia hanafoana ny bridge.", flush=True)
    try:
        server.serve_forever(poll_interval=1)
    except KeyboardInterrupt:
        print("\nStopping and revoking the bridge…", flush=True)
    finally:
        server.server_close()
        try:
            if stat.S_ISSOCK(os.lstat(SOCKET_PATH).st_mode):
                os.unlink(SOCKET_PATH)
        except OSError:
            pass
        api.revoke()
        print("Admin bridge stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

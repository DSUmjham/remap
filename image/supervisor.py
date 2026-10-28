#!/usr/bin/env python3
"""Serve every tools/*.py through one mcpo instance.

tools/foo.py is served at /foo (files starting with "_" are skipped). pyghidra-mcp
is added at /pyghidra while it's reachable. mcpo restarts when a tool file changes,
pyghidra comes or goes, or the panel drops /state/restart. Files with syntax errors
are logged and skipped so they don't take the other tools down.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(os.environ.get("TOOLS_DIR", "/workspace/tools"))
STATE_DIR = Path(os.environ.get("STATE_DIR", "/state"))
PYGHIDRA_HOST = os.environ.get("PYGHIDRA_HOST", "remap-pyghidra")
PYGHIDRA_PORT = int(os.environ.get("PYGHIDRA_PORT", "8000"))
RESERVED_NAMES = {"pyghidra"}  # route owned by the pyghidra-mcp container
CONFIG_PATH = Path(os.environ.get("MCPO_CONFIG", "/tmp/mcpo.json"))
PORT = int(os.environ.get("PORT", "8000"))
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "2"))

# mcp's stdio client only passes a small env allow-list to tools; add extras here.
PASSTHROUGH_ENV = ()

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

_stop = False


def log(msg: str) -> None:
    print(f"[lab] {msg}", flush=True)


def discover_tools(tools_dir: Path = TOOLS_DIR) -> tuple[dict[str, Path], list[str]]:
    """Return (valid tools by route name, human-readable problems)."""
    tools: dict[str, Path] = {}
    problems: list[str] = []
    if not tools_dir.is_dir():
        return tools, [f"tools folder not found: {tools_dir}"]
    for path in sorted(tools_dir.glob("*.py")):
        stem = path.stem
        if stem.startswith(("_", ".")):
            continue  # helper module, not served
        if stem in RESERVED_NAMES:
            problems.append(f"{path.name}: skipped, /{stem} is reserved for the pyghidra-mcp container")
            continue
        if not NAME_RE.match(stem):
            problems.append(f"{path.name}: skipped, file name must match [A-Za-z0-9_-]+")
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            problems.append(f"{path.name}: skipped, syntax error on line {exc.lineno}: {exc.msg}")
            continue
        except (OSError, UnicodeDecodeError) as exc:
            problems.append(f"{path.name}: skipped, could not read file: {exc}")
            continue
        tools[stem] = path
    return tools, problems


def pyghidra_url() -> str:
    return f"http://{PYGHIDRA_HOST}:{PYGHIDRA_PORT}/mcp"


def pyghidra_reachable(host: str | None = None, port: int | None = None) -> bool:
    """True if something is listening on the pyghidra-mcp port."""
    try:
        with socket.create_connection((host or PYGHIDRA_HOST, port or PYGHIDRA_PORT), timeout=0.5):
            return True
    except OSError:
        return False


def build_config(tools: dict[str, Path], with_pyghidra: bool = False) -> dict:
    env = {key: os.environ[key] for key in PASSTHROUGH_ENV if key in os.environ}
    env["PYTHONUNBUFFERED"] = "1"
    servers: dict[str, dict] = {
        name: {"command": sys.executable, "args": [str(path)], "env": env}
        for name, path in tools.items()
    }
    if with_pyghidra:
        # pyghidra-mcp rejects non-localhost Host headers (DNS rebinding protection).
        servers["pyghidra"] = {
            "type": "streamable-http",
            "url": pyghidra_url(),
            "headers": {"Host": f"localhost:{PYGHIDRA_PORT}"},
        }
    return {"mcpServers": servers}


def consume_restart_request(state_dir: Path | None = None) -> bool:
    """Delete <state>/restart if present. True if it was there."""
    marker = (state_dir or STATE_DIR) / "restart"
    try:
        marker.unlink()
        return True
    except OSError:
        return False


def fingerprint(
    tools_dir: Path | None = None,
    pyghidra_up: bool = False,
    state_dir: Path | None = None,
) -> str:
    """Hash of tool files (name, size, mtime), pyghidra status and the panel's generation.

    The generation changes when the panel replaces the pyghidra container. mcpo keeps
    a session to the old one, so that needs a restart even if the port never closed.
    """
    tools_dir = tools_dir or TOOLS_DIR
    h = hashlib.sha1()
    if tools_dir.is_dir():
        for path in sorted(tools_dir.glob("*.py")):
            try:
                st = path.stat()
            except OSError:
                continue
            h.update(f"{path.name}:{st.st_size}:{st.st_mtime_ns}\n".encode())
    h.update(f"pyghidra:{pyghidra_up}\n".encode())
    try:
        h.update(((state_dir or STATE_DIR) / "pyghidra.generation").read_bytes())
    except OSError:
        pass  # panel hasn't started pyghidra yet
    return h.hexdigest()


def start_mcpo() -> subprocess.Popen:
    mcpo = shutil.which("mcpo") or "mcpo"
    cmd = [mcpo, "--host", "0.0.0.0", "--port", str(PORT), "--config", str(CONFIG_PATH)]
    log(f"starting: {' '.join(cmd)}")
    return subprocess.Popen(cmd)


def stop_mcpo(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _handle_signal(_signum, _frame) -> None:
    global _stop
    _stop = True


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    proc: subprocess.Popen | None = None
    last_fp: str | None = None
    was_up = False

    while not _stop:
        if proc is not None and proc.poll() is not None:
            log(f"mcpo exited with code {proc.returncode}; restarting in 3s")
            proc = None
            last_fp = None
            time.sleep(3)
            continue

        forced = consume_restart_request()
        if forced:
            log("restart requested from the control panel")
        up = pyghidra_reachable()
        if up != was_up:
            log("pyghidra-mcp is reachable" if up else "pyghidra-mcp is no longer reachable")
            was_up = up

        fp = fingerprint(pyghidra_up=up)
        if forced or fp != last_fp:
            time.sleep(0.5)  # let an editor finish writing
            fp = fingerprint(pyghidra_up=up)
            stop_mcpo(proc)
            proc = None
            tools, problems = discover_tools()
            for problem in problems:
                log(f"WARNING: {problem}")
            if tools or up:
                CONFIG_PATH.write_text(json.dumps(build_config(tools, with_pyghidra=up), indent=2))
                routes = list(tools) + (["pyghidra"] if up else [])
                log("serving: " + ", ".join(f"/{name}" for name in routes))
                proc = start_mcpo()
            else:
                log(f"no valid tools in {TOOLS_DIR}; waiting for files")
            last_fp = fp

        time.sleep(POLL_SECONDS)

    log("shutting down")
    stop_mcpo(proc)
    return 0


if __name__ == "__main__":
    sys.exit(main())

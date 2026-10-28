"""Start, stop and inspect the pyghidra-mcp container via the Docker API.

Only the panel mounts the Docker socket; student tools run in `tools` without it.
`docker` is imported lazily so the rest of the panel doesn't need it.
"""

from __future__ import annotations

import os
from typing import Any

from . import lib

CONTAINER_NAME = "remap-pyghidra"
TOOLS_CONTAINER = "remap-tools"
LABEL = "remap.project"


def image() -> str:
    return os.environ.get("PYGHIDRA_IMAGE", "ghcr.io/clearbluejar/pyghidra-mcp:latest")


def network() -> str:
    return os.environ.get("REMAP_NETWORK", "remap_net")


def projects_volume() -> str:
    return os.environ.get("REMAP_PROJECTS_VOLUME", "remap_projects")


def client() -> Any:
    import docker  # noqa: PLC0415

    return docker.from_env()


def _find(cli: Any, name: str) -> Any | None:
    try:
        return cli.containers.get(name)
    except Exception:  # docker.errors.NotFound, or the API is unreachable
        return None


def status(cli: Any = None) -> dict:
    """{"docker": bool, "running": bool, "project": str | None, "error": str | None}"""
    try:
        cli = cli or client()
        cli.ping()
    except Exception as exc:
        return {"docker": False, "running": False, "project": None, "error": f"Docker API unavailable: {exc}"}
    box = _find(cli, CONTAINER_NAME)
    if box is None:
        return {"docker": True, "running": False, "project": None, "error": None}
    box.reload()
    return {
        "docker": True,
        "running": box.status == "running",
        "project": (box.labels or {}).get(LABEL),
        "error": None,
    }


def stop(cli: Any = None) -> None:
    cli = cli or client()
    box = _find(cli, CONTAINER_NAME)
    if box is not None:
        box.remove(force=True)
    lib.bump_generation()


def start(project: str, cli: Any = None) -> str:
    """Replace the pyghidra-mcp container with one serving `project`. Returns its short id.

    The first call pulls the image. Binaries are analyzed on startup, so big ones are slow.
    """
    binaries = lib.list_binaries(project)  # also validates the project name
    if not binaries:
        raise ValueError(f"project '{project}' has no binaries yet; upload one first")
    cmd = lib.pyghidra_command(project, binaries)

    cli = cli or client()
    old = _find(cli, CONTAINER_NAME)
    if old is not None:
        old.remove(force=True)

    box = cli.containers.run(
        image(),
        command=cmd,
        name=CONTAINER_NAME,
        detach=True,
        network=network(),
        volumes={projects_volume(): {"bind": "/projects", "mode": "rw"}},
        labels={LABEL: project, "remap.managed": "true"},
        restart_policy={"Name": "unless-stopped"},
    )
    lib.set_active_project(project)
    lib.bump_generation()
    return box.short_id


def logs(tail: int = 80, cli: Any = None, name: str = CONTAINER_NAME) -> str:
    try:
        cli = cli or client()
    except Exception as exc:
        return f"(Docker API unavailable: {exc})"
    box = _find(cli, name)
    if box is None:
        return f"({name} is not running)"
    return box.logs(tail=tail).decode("utf-8", "replace")

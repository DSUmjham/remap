"""Panel logic: tools, test calls, Ghidra projects.

No Streamlit or Docker imports, so it's all unit-tested. Config is read from the
environment on each call to keep tests simple.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")
MAX_BINARY_BYTES = 100 * 1024 * 1024
DEMO_PROJECT = "demo"


# ---------------------------------------------------------------- configuration

def tools_dir() -> Path:
    return Path(os.environ.get("TOOLS_DIR", "/workspace/tools"))


def state_dir() -> Path:
    return Path(os.environ.get("STATE_DIR", "/state"))


def projects_dir() -> Path:
    return Path(os.environ.get("PROJECTS_DIR", "/projects"))


def seed_dir() -> Path:
    return Path(os.environ.get("SEED_SAMPLES_DIR", "/opt/lab/samples"))


def tools_url() -> str:
    return os.environ.get("TOOLS_URL", "http://tools:8000").rstrip("/")


def pyghidra_host() -> str:
    return os.environ.get("PYGHIDRA_HOST", "remap-pyghidra")


# ---------------------------------------------------------------- small helpers

def valid_name(name: str) -> bool:
    """Project and tool names: letters, digits, '-' and '_', starting with a letter or digit."""
    return bool(NAME_RE.match(name or ""))


def tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_json(method: str, url: str, body: Any = None, timeout: float = 15.0) -> tuple[int, Any]:
    """One HTTP call returning (status, parsed JSON or raw text). Never raises on HTTP errors."""
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except (urllib.error.URLError, OSError) as exc:
        return 0, f"could not connect: {exc}"
    text = raw.decode("utf-8", "replace")
    try:
        return status, json.loads(text)
    except ValueError:
        return status, text


# ---------------------------------------------------------------------- tools

def syntax_error(path: Path) -> str | None:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        return f"line {exc.lineno}: {exc.msg}"
    except (OSError, UnicodeDecodeError) as exc:
        return f"cannot read file: {exc}"
    return None


def tool_rows() -> list[dict]:
    """One row per tool file: name, syntax problem (if any), and whether mcpo serves it."""
    rows = []
    folder = tools_dir()
    if not folder.is_dir():
        return rows
    for path in sorted(folder.glob("*.py")):
        if path.stem.startswith(("_", ".")):
            continue
        err = syntax_error(path)
        served = False
        if err is None:
            status, _ = http_json("GET", f"{tools_url()}/{path.stem}/openapi.json", timeout=3)
            served = status == 200
        rows.append({"tool": path.stem, "file": path.name, "syntax_error": err, "served": served})
    return rows


def request_tools_restart() -> None:
    """Drop the restart file the supervisor polls for."""
    folder = state_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "restart").write_text(str(time.time()))


def bump_generation() -> None:
    """Tell the supervisor pyghidra was replaced so it reconnects."""
    folder = state_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pyghidra.generation").write_text(str(time.time_ns()))


# ----------------------------------------------------------------- test panel

def _resolve(spec: dict, schema: dict) -> dict:
    ref = schema.get("$ref")
    if not ref or not ref.startswith("#/"):
        return schema
    node: Any = spec
    for part in ref[2:].split("/"):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, dict) else {}


_EXAMPLE_BY_TYPE = {"integer": 0, "number": 0, "string": "", "boolean": False, "array": [], "object": {}}


def example_args(schema: dict) -> dict:
    """A starting JSON object for a tool's arguments, from its input schema."""
    example = {}
    for name, prop in (schema.get("properties") or {}).items():
        if "default" in prop:
            example[name] = prop["default"]
        else:
            example[name] = _EXAMPLE_BY_TYPE.get(prop.get("type", "string"), "")
    return example


def operations(route: str) -> tuple[list[dict], str | None]:
    """Operations at /<route> from mcpo's openapi.json. Returns (ops, error).

    Each op has path, summary, description, schema and example (starter args).
    """
    status, spec = http_json("GET", f"{tools_url()}/{route}/openapi.json", timeout=5)
    if status != 200 or not isinstance(spec, dict):
        return [], f"/{route} is not being served (HTTP {status or 'no connection'})"
    ops = []
    for path, item in (spec.get("paths") or {}).items():
        post = item.get("post") if isinstance(item, dict) else None
        if not post:
            continue
        schema: dict = {}
        content = ((post.get("requestBody") or {}).get("content") or {}).get("application/json")
        if content and isinstance(content.get("schema"), dict):
            schema = _resolve(spec, content["schema"])
        ops.append(
            {
                "path": path,
                "summary": post.get("summary") or path.strip("/"),
                "description": post.get("description") or "",
                "schema": schema,
                "example": example_args(schema),
            }
        )
    return sorted(ops, key=lambda o: o["path"]), None


def call_operation(route: str, path: str, args: dict) -> tuple[int, Any]:
    """POST args to one tool, same as Open WebUI does."""
    return http_json("POST", f"{tools_url()}/{route}{path}", body=args, timeout=60)


def served_routes() -> list[str]:
    """Routes the panel can test: every served tool, plus pyghidra when it is up."""
    routes = [r["tool"] for r in tool_rows() if r["served"]]
    status, _ = http_json("GET", f"{tools_url()}/pyghidra/openapi.json", timeout=3)
    if status == 200:
        routes.append("pyghidra")
    return routes


# -------------------------------------------------------------- ghidra projects

def project_path(project: str) -> Path:
    if not valid_name(project):
        raise ValueError("project names use letters, digits, '-' and '_' (up to 40 characters)")
    return projects_dir() / project


def create_project(project: str) -> Path:
    base = project_path(project)
    for sub in ("binaries", "ghidra"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    # pyghidra-mcp may run as a different user.
    for path in (base, base / "binaries", base / "ghidra"):
        os.chmod(path, 0o777)
    return base


def list_projects() -> list[str]:
    folder = projects_dir()
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_dir() and valid_name(p.name))


def list_binaries(project: str) -> list[str]:
    folder = project_path(project) / "binaries"
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_file())


def safe_filename(name: str) -> str:
    """Reduce an uploaded file name to a safe single path component."""
    base = os.path.basename(name.replace("\\", "/"))
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).lstrip(".")
    if not base:
        raise ValueError("file name is empty after cleaning")
    return base[:100]


def save_binary(project: str, filename: str, data: bytes) -> str:
    if len(data) > MAX_BINARY_BYTES:
        raise ValueError(f"file is larger than {MAX_BINARY_BYTES // (1024 * 1024)} MB")
    create_project(project)
    name = safe_filename(filename)
    dest = project_path(project) / "binaries" / name
    dest.write_bytes(data)
    os.chmod(dest, 0o644)
    return name


def seed_demo_project() -> bool:
    """Copy the sample binaries into the demo project. True if anything was copied."""
    seeds = seed_dir()
    if not seeds.is_dir():
        return False
    create_project(DEMO_PROJECT)
    seeded = False
    for src in sorted(p for p in seeds.iterdir() if p.is_file()):
        dest = projects_dir() / DEMO_PROJECT / "binaries" / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
            os.chmod(dest, 0o644)
            seeded = True
    return seeded


def pyghidra_command(project: str, binaries: list[str]) -> list[str]:
    """pyghidra-mcp args for one project. Paths are inside the container (/projects)."""
    if not valid_name(project):
        raise ValueError("invalid project name")
    base = f"/projects/{project}"
    return [
        "-t", "streamable-http",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--project-path", f"{base}/ghidra",
        "--project-name", project,
        *[f"{base}/binaries/{name}" for name in sorted(binaries)],
    ]


def active_project() -> str | None:
    try:
        name = (state_dir() / "active_project").read_text().strip()
    except OSError:
        return None
    return name if valid_name(name) else None


def set_active_project(project: str) -> None:
    if not valid_name(project):
        raise ValueError("invalid project name")
    folder = state_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "active_project").write_text(project)


# ----------------------------------------------------------------------- model

def ollama_models(base_url: str) -> tuple[list[str] | None, str | None]:
    """(model names, error). Names is None when Ollama cannot be reached."""
    if not base_url:
        return None, "OLLAMA_BASE_URL is not set"
    status, body = http_json("GET", base_url.rstrip("/") + "/api/tags", timeout=4)
    if status != 200 or not isinstance(body, dict):
        return None, f"cannot reach {base_url} ({status or 'no connection'})"
    return sorted(m.get("name", "?") for m in body.get("models", [])), None

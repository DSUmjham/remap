# REMAP Student Guide

This guide takes you from a fresh clone to a running lab, a tested sample tool, and your first tool of your own.
It takes about 30 minutes, most of it waiting for downloads the first time.

## What You Are Running

| Part | Address | What it is for |
|------|---------|----------------|
| Control panel | http://localhost:8501 | Restart and test your tools, manage Ghidra projects |
| Tool server | http://localhost:8001/NAME/docs | Swagger page for each of your tools |
| Chat | http://localhost:3000 | Open WebUI: talk to a model that can call your tools |

Your tools are plain Python files in `workspace/tools/`. Each file becomes its own tool server.
The lab runs them in a container, so a broken tool cannot hurt your machine.

## 1. Before You start

You need:

- **Docker with Compose.** Docker Desktop (Windows, macOS, Linux) or Colima (macOS). Check with:
  ```bash
  docker compose version
  ```
- **About 15 GB of free disk** for the images and a small model.
- **Ports 3000, 8001 and 8501 free** on your machine.

> **macOS with Colima:** clone the repo somewhere inside your home folder. Colima only shares your home
> folder with Docker, so a repo in `/tmp` or on another disk will look empty to the containers.

## 2. Get the Lab

```bash
git clone https://github.com/DSUmjham/remap
cd remap
```

## 3. Run Setup

macOS or Linux:

```bash
./setup.sh
```

Windows (PowerShell):

```powershell
.\setup.ps1
```

Setup asks one question: **where the model runs.**

- If your instructor gave you a shared Ollama server, paste its URL.
- If you installed Ollama on your computer, type `host`. This is the fast option on Macs; see
  [running a model locally](local-model.md).
- Otherwise press Enter. The lab runs Ollama in Docker, which works but is slow because it cannot use the GPU.

Setup writes a `.env` file and copies the sample tool to `workspace/tools/hello.py`.
Run it only once. To start over, delete `.env` and run it again.

## 4. Start the Lab

```bash
docker compose up -d
```

The first start downloads several images, including Ghidra, and can take 5 to 15 minutes. Later starts take
seconds. The chat also downloads a small model on its first start, so give it a few extra minutes. Check that
everything is up:

```bash
docker compose ps
```

You should see `remap-tools`, `remap-panel` and `remap-webui` (plus `remap-ollama` if you pressed Enter in setup)
with status `Up`. `remap-pyghidra-pull` only downloads the Ghidra image, so `Exited (0)` is normal for it.

### Local Model Only: Download a Model

Skip this if you use a shared server. Otherwise download a model that supports tool calling.

Ollama on your computer (`host` in setup):

```bash
ollama pull qwen3:8b
```

Ollama in Docker (you pressed Enter in setup):

```bash
docker exec remap-ollama ollama pull qwen3:4b
```

[Running a model locally](local-model.md) explains which model fits your machine and the settings that
keep it responsive.

## 5. Check the Three Pages

1. **Panel:** open http://localhost:8501. The **Tools** tab should list `hello` as **served**.
2. **Swagger:** open http://localhost:8001/hello/docs. You should see one operation, `/add`.
3. **Chat:** open http://localhost:3000. The first visit asks you to create an account. This account lives
   only on your machine and the first one becomes the admin, so any name, email and password will do.

If something is missing, see [Troubleshooting](troubleshooting.md).

## 6. Test the Sample Tool

Open `workspace/tools/hello.py` in your editor. The whole tool is a few lines:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


if __name__ == "__main__":
    mcp.run()
```

Now call it three ways. Each one goes through the same tool server.

**From the panel.** Tools tab, **Test a tool**: choose server `hello` and tool `add`, set the arguments to
`{"a": 2, "b": 3}` and press **Call**. The result is `5`.

**From Swagger.** On http://localhost:8001/hello/docs, open `/add`, press **Try it out**, fill in the body,
and press **Execute**. This is the exact REST call the chat makes.

**From the chat.** Start a new chat, pick your model at the top, and turn on the `hello` tool from the tools
button in the message box. Then ask:

> Use the add tool to add 1234 and 5678.

Expand the tool call in the answer to see the arguments the model chose and the result your tool returned.

## 7. Write Your First Tool

This walkthrough builds a small word counting tool. It is a practice example and is not one of the graded exercises.

### 7.1 Create the File

Create `workspace/tools/wordcount.py`:

```python
"""Counts words and lines in a piece of text."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("wordcount")


@mcp.tool()
def count_words(text: str) -> dict:
    """Count the words and lines in `text`.

    Use this when the user asks how long a piece of text is.
    """
    return {"words": len(text.split()), "lines": len(text.splitlines())}


if __name__ == "__main__":
    mcp.run()
```

The parts that matter:

| Part | Why it matters |
|------|----------------|
| File name | `wordcount.py` is served at `/wordcount`. Use letters, digits, `-` and `_`. Names starting with `_` are helper modules, not tools. The name `pyghidra` is reserved. |
| `@mcp.tool()` | Turns the function into a tool. One file can hold several tools. |
| Type hints | Become the argument schema. The model and Swagger both read them. |
| Docstring | Is the description the model reads when deciding whether to call your tool. Write it for the model. |
| Return value | Becomes the result. A `dict` arrives as JSON, which is easy for the model to quote. |
| `mcp.run()` | Starts the tool over stdio. The lab launches the file for you; you never run it yourself. |

### 7.2 Load It

Save the file. The lab notices new and changed files within a few seconds. If the panel does not show
`wordcount` as **served**, press **Restart tools**.

### 7.3 Test It in the Panel

Tools tab, **Test a tool**: choose `wordcount` and `count_words`, set the arguments to
`{"text": "one two three"}` and press **Call**. Check the result before you go near the chat. If the tool
is wrong here, it will be wrong in the chat too, and the chat makes it harder to see why.

### 7.4 Use It in the Chat

The chat only knows the tool servers it was given on first start, so a new tool needs to be added once:

1. In Open WebUI, click your name, then **Admin Panel**, then **Settings**. Open the tab that lists
   `http://tools:8000/hello` and `http://tools:8000/pyghidra`.
2. Add a connection: type **OpenAPI**, URL `http://tools:8000/wordcount`, path `openapi.json`, auth **None**. Save.
3. In a new chat, turn on `wordcount` and ask: *How many words are in "the quick brown fox"?*

Use `tools`, not `localhost`, in that URL. The chat runs in its own container and reaches the tool server
by its container name. Use the **admin** settings: tool servers added under your own profile's
**Settings > Integrations** are called from your browser, which cannot reach `tools`.

### 7.5 When Something Goes Wrong

- **A syntax error** is shown next to the tool in the panel, and the tool is skipped until you fix it.
  Your other tools keep working.
- **An exception** while the tool runs comes back as the result. Try `raise ValueError("text is empty")`
  and see where the message appears in the panel and in the chat.
- **Debug output** must go to stderr: `print("debug", file=sys.stderr)`. A plain `print()` writes to
  stdout, which is the channel the tool uses to talk to the lab. It fills the log with JSON errors and
  can break the tool.
- **The Tools log** at the bottom of the Tools tab (or `docker logs remap-tools`) shows what the tool
  server is doing.

## 8. Ghidra in One Minute

The lab includes headless Ghidra through pyghidra-mcp, which you need for Stage 3.

1. Panel, **Ghidra** tab: create a project, upload a binary (up to 100 MB), and press **Start / apply project**.
   For Stage 3, use the binary your instructor gives you.
2. Ghidra analyzes the binary when it starts. Open the **pyghidra-mcp log** and wait until it reports the
   analysis is complete. This can take a few minutes.
3. A `pyghidra` server now appears in **Test a tool**, and in the chat after you reload the page, with
   operations such as `list_project_binaries` and `decompile_function`.

To add another binary, upload it and press **Start / apply project** again.

## 9. The Exercises

Work through them in order. Stages 1 and 2 have a `starter/` to copy into `workspace/tools/`.

1. [Stage 1: Hello, MCP tool](../exercises/01-hello/README.md): the edit, restart, test loop.
2. [Stage 2: CWE triage tool](../exercises/02-triage/README.md): flag risky patterns in decompiled C.
3. [Stage 3: Capstone](../exercises/03-capstone/README.md): chain your tool with Ghidra and measure what it adds.

## 10. Stop, Restart, Reset

| To | Run |
|----|-----|
| Stop the lab (keeps everything) | `docker compose down` |
| Start it again | `docker compose up -d` |
| Reset everything except your tool files | `docker compose down -v` |

Your tools live in `workspace/tools/` on your own disk and survive all of these. A reset with `-v` deletes your
chat account, chat history, Ghidra projects and any downloaded model.

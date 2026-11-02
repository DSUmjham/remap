# REMAP

A containerized envrionment used to write the MCP tools an LLM uses for reverse engineering. This can be run with one one Docker Compose stack and a shared Ollama server (or an optional local model) for the LLM.

| Component | Description |
|------|------------|
| Chat | Open WebUI, pre-wired to the tool servers (http://localhost:3000) |
| Tools | Your `.py` files in `workspace/tools/`, each served as a REST API by mcpo (Swagger at http://localhost:8001/NAME/docs) |
| pyghidra-mcp | Headless Ghidra from the upstream image, started by the panel for a chosen project |
| Panel | Streamlit control panel (http://localhost:8501): restart tools, test tools, pick a Ghidra project, upload binaries |

## Quick start

Requires Docker with Compose.

```bash
git clone https://github.com/DSUmjham/remap && cd remap
./setup.sh # Windows: ./setup.ps1
docker compose up -d
```

`setup.sh` asks where the model runs (Ollama in Docker, Ollama installed on your computer, or a shared
server) and creates `.env` and `workspace/tools/hello.py`. Then open the panel and the chat.

Running the model on your own computer? See [running a model locally](docs/local-model.md) for model
sizes and the settings that keep it responsive.

## Security Note

User code runs in the `tools` container, which has no Docker socket. Only the `panel` container mounts
`/var/run/docker.sock`, because it starts and stops the pyghidra-mcp container. Anyone who controls the
panel has control of the Docker host, so ports are bound to `127.0.0.1` only. Do not publish
them on a shared network.

More: [how it works](docs/architecture.md) & [troubleshooting](docs/troubleshooting.md). MIT license.

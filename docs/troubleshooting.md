# Troubleshooting

**Tool shows "not served" in the panel.** Check the tools log in the panel (Tools tab) or run
`docker logs remap-tools`. A syntax error is shown next to the tool; fix it and press Restart tools.

**"Error executing tool X" with no detail.** Version 2.x of the Python MCP SDK hides exception text from
clients. The image pins `mcp[cli]>=1.9,<2`. If you upgrade the SDK, expect to see less error detail; print
to stderr inside your tool while debugging.

**Ghidra tab says the Docker API is unavailable.** The panel needs `/var/run/docker.sock`. On Linux your
user must be able to use Docker. With Docker Desktop on Windows or macOS it works by default. Rootless
Docker uses a different socket path; edit the volume line in `docker-compose.yml`.

**pyghidra-mcp takes a long time.** The first start pulls the image and Ghidra analyzes each binary on
startup. Watch the pyghidra-mcp log on the Ghidra tab. The `pyghidra` route appears in the chat once the server listens.

**Chat does not list the tools.** Open WebUI reads `TOOL_SERVER_CONNECTIONS` only on its first start. Add
or fix servers later in Admin Settings, Tools, using `http://tools:8000/NAME` as the URL.

**Model list is empty or errors.** See the System tab. For a shared server, `OLLAMA_BASE_URL` must be reachable from
Docker containers. For the local model, run `docker exec remap-ollama ollama pull MODEL`.

**Files in `workspace/` are owned by root (Linux).** Set `LAB_UID` and `LAB_GID` in `.env` to the output of `id -u` and `id -g`.

# Running a Model Locally

REMAP works with any Ollama server. This page covers running one on your own computer and keeping it
fast enough to use.

## Install Ollama on Baremetal

Docker on macOS cannot use the GPU, so the bundled `ollama` container runs on the CPU only and is slow on
Macs. Install Ollama directly instead:

```bash
brew install ollama        # macOS; Windows and Linux installers are at https://ollama.com/download
ollama serve               # leave this running, or: brew services start ollama
```

Then answer `host` when `setup.sh` asks for the model server. That sets
`OLLAMA_BASE_URL=http://host.docker.internal:11434`, which is how the containers reach Ollama on your computer.

Already ran setup? Change the **Ollama API** URL to `http://host.docker.internal:11434` in Open WebUI under
**Admin Panel > Settings > Connections** (Open WebUI keeps the URL from its first start, so editing `.env`
is not enough).

## Pick a Model That Fits

Tool calling needs a model trained for it. Qwen3 works well. Leave room for Docker and a browser:

| Memory | Model | Size |
|--------|-------|------|
| 16 GB | `qwen3:4b` | about 2.5 GB |
| 24 GB | `qwen3:8b` (or `qwen3:4b` if it feels slow) | about 5 GB |
| 32 GB or more | `qwen3:14b` or `qwen3:30b-a3b` | about 9 to 19 GB |

```bash
ollama pull qwen3:8b
```

Generation speed depends mostly on memory bandwidth, so the same model is noticeably faster on a Pro or Max
chip than on an Air.

## Settings for Speed

REMAP's `docker-compose.yml` already turns off Open WebUI's background calls (chat titles, tags, follow-up
suggestions) and its Notes, Memories and Calendar tools. On a local model those extra calls queue up behind
your messages. The rest are per model or per chat:

- **Turn off thinking.** Qwen3 reasons at length before answering. In **Workspace > Models**, edit the
  model, open **Advanced Params** and set **Think** to **Off**. Turn it back on in a chat's controls for
  hard questions.
- **Enable only the tools you need.** Every enabled tool server adds its tool descriptions to each message
  (pyghidra has about 20). Switch tools on per chat from the message box.
- **Turn off built-in tools you do not use.** In the model's settings, under **Capabilities**, switch off
  **Builtin Tools** to drop Open WebUI's own time, file and knowledge tools from every message.
- **Warm the model up.** The first message after a model loads is slow. Send a short message before a demo,
  and start Ghidra projects ahead of time because the first analysis takes minutes.

## Troubleshooting Slowness

`ollama ps` shows the loaded model and whether it runs on the GPU. The `ollama serve` output shows each
request: `prompt eval` is the time spent reading the message (long when many tools are enabled) and `eval`
is the time spent writing the answer.

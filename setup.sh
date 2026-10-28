#!/usr/bin/env bash
# First-run setup: writes .env and creates workspace/tools with the hello tool.
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  echo ".env already exists; leaving it alone. Delete it to run setup again."
else
  read -r -p "Ollama URL (blank to run a model on this machine instead): " ollama_url
  secret="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  {
    echo "LAB_IMAGE=${LAB_IMAGE:-ghcr.io/dsumjham/remap:latest}"
    echo "LAB_UID=$(id -u)"
    echo "LAB_GID=$(id -g)"
    echo "WEBUI_SECRET_KEY=$secret"
    if [ -z "$ollama_url" ]; then
      echo "OLLAMA_BASE_URL=http://ollama:11434"
      echo "COMPOSE_PROFILES=local-model"
    else
      echo "OLLAMA_BASE_URL=$ollama_url"
    fi
  } > .env
  echo "Wrote .env"
fi

mkdir -p workspace/tools
[ -f workspace/tools/hello.py ] || cp tools/hello.py workspace/tools/hello.py
echo "Next: docker compose up -d, then open http://localhost:8501 (panel) and http://localhost:3000 (chat)."

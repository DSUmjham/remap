# syntax=docker/dockerfile:1

# build the demo binaries for the target arch
FROM python:3.12-slim AS samples
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libc6-dev \
 && rm -rf /var/lib/apt/lists/*
# samples/ is optional; the glob lets the build pass without it
COPY image/requirements.txt samples* /ctx/
RUN mkdir /out \
 && for f in /ctx/src/*.c; do \
      [ -e "$f" ] || continue; \
      gcc -O0 -g0 -fno-stack-protector -o "/out/$(basename "$f" .c)" "$f"; \
    done

# runtime image for both tools and panel
FROM python:3.12-slim

COPY image/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY image/supervisor.py /opt/lab/supervisor.py
COPY panel /opt/lab/panel
COPY --from=samples /out /opt/lab/samples

ENV TOOLS_DIR=/workspace/tools \
    STATE_DIR=/state \
    PROJECTS_DIR=/projects \
    SEED_SAMPLES_DIR=/opt/lab/samples \
    PORT=8000 \
    HOME=/tmp \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# /state is 0777 with no sticky bit: the panel (root) creates the restart file and the
# tools user deletes it. New named volumes inherit these permissions.
RUN mkdir -p /workspace/tools /state /projects \
 && chmod 0777 /state \
 && chmod 0777 /projects \
 && chmod -R a+rwX /workspace

WORKDIR /workspace

# Non-root by default. Compose runs tools as LAB_UID and panel as root (Docker socket).
USER 1000:1000

"""REMAP control panel (Streamlit). Thin UI over remap_panel.lib and remap_panel.ghidra."""

import json
import os

import streamlit as st

from remap_panel import ghidra, lib, theme

st.set_page_config(page_title="REMAP", page_icon=None, layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)
st.markdown(theme.header_html(), unsafe_allow_html=True)

if "seeded" not in st.session_state:
    try:
        lib.seed_demo_project()
    except OSError as exc:
        st.warning(f"Could not create the demo project: {exc}")
    st.session_state["seeded"] = True

tab_tools, tab_ghidra, tab_system = st.tabs(["Tools", "Ghidra", "System"])

# ------------------------------------------------------------------- Tools tab
with tab_tools:
    st.subheader("Your tools")
    st.caption("Every .py file in workspace/tools becomes one tool server. Save a file, then restart.")
    rows = lib.tool_rows()
    if not rows:
        st.info("No tools yet. Copy tools/hello.py or an exercise solution into workspace/tools.")
    for row in rows:
        c1, c2 = st.columns([1, 4])
        c1.markdown(theme.pill("served" if row["served"] else "not served", row["served"]), unsafe_allow_html=True)
        c2.write(f"**{row['tool']}** ({row['file']})")
        if row["syntax_error"]:
            c2.error(f"Syntax error, {row['syntax_error']}")

    b1, b2 = st.columns(2)
    if b1.button("Restart tools"):
        lib.request_tools_restart()
        st.success("Restart requested. Reload this page in a few seconds.")
    if b2.button("Refresh"):
        st.rerun()
    with st.expander("Tools log"):
        st.code(ghidra.logs(name=ghidra.TOOLS_CONTAINER) or "(empty)")

    st.subheader("Test a tool")
    routes = lib.served_routes()
    if not routes:
        st.info("Nothing is being served yet.")
    else:
        route = st.selectbox("Server", routes)
        ops, err = lib.operations(route)
        if err:
            st.error(err)
        elif ops:
            op = st.selectbox("Tool", ops, format_func=lambda o: o["path"].strip("/"))
            if op["description"]:
                st.caption(op["description"])
            raw = st.text_area(
                "Arguments (JSON)",
                value=json.dumps(op["example"], indent=2),
                height=160,
                key=f"args-{route}-{op['path']}",
            )
            if st.button("Call"):
                try:
                    args = json.loads(raw or "{}")
                except ValueError as exc:
                    st.error(f"Arguments are not valid JSON: {exc}")
                else:
                    code, body = lib.call_operation(route, op["path"], args)
                    (st.success if code == 200 else st.error)(f"HTTP {code}")
                    st.code(body if isinstance(body, str) else json.dumps(body, indent=2))

# ----------------------------------------------------------------- Ghidra tab
with tab_ghidra:
    st.subheader("Ghidra project")
    state = ghidra.status()
    if not state["docker"]:
        st.warning(state["error"])
    else:
        label = f"running, project {state['project']}" if state["running"] else "stopped"
        st.markdown(theme.pill(label, state["running"]), unsafe_allow_html=True)

    projects = lib.list_projects()
    new_name = st.text_input("New project name")
    if st.button("Create project"):
        try:
            lib.create_project(new_name)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    if projects:
        default = lib.active_project()
        index = projects.index(default) if default in projects else 0
        project = st.selectbox("Project", projects, index=index)
        st.write("Binaries:", ", ".join(lib.list_binaries(project)) or "none yet")

        upload = st.file_uploader("Add a binary", key=f"up-{project}")
        if upload is not None and st.button("Save binary"):
            try:
                saved = lib.save_binary(project, upload.name, upload.getvalue())
                st.success(f"Saved {saved}")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

        a, b = st.columns(2)
        if a.button("Start / apply project"):
            with st.spinner("Starting pyghidra-mcp. The first pull of the image can take several minutes."):
                try:
                    ghidra.start(project)
                    st.success("Started. Binaries are analyzed on startup; large ones take a while.")
                except Exception as exc:
                    st.error(str(exc))
        if b.button("Stop"):
            try:
                ghidra.stop()
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        with st.expander("pyghidra-mcp log"):
            st.code(ghidra.logs())
    else:
        st.info("Create a project to begin.")

# ----------------------------------------------------------------- System tab
with tab_system:
    st.subheader("Model server")
    models, err = lib.ollama_models(os.environ.get("OLLAMA_BASE_URL", ""))
    if err:
        st.error(err)
    else:
        st.success(f"Ollama reachable, {len(models)} model(s)")
        st.write(", ".join(models) or "no models pulled yet")

    st.subheader("Services")
    st.write("Tools server:", "up" if lib.http_json("GET", lib.tools_url() + "/", timeout=2)[0] else "not reachable")
    st.write("pyghidra-mcp:", "up" if lib.tcp_open(lib.pyghidra_host(), 8000) else "not running")

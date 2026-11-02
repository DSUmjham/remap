# Stage 3: Capstone Tool Chaining

Goal: have the model analyze a real binary using Ghidra's decompiler (pyghidra-mcp) and your triage tool.

1. Panel, tab **Ghidra**: create a project, upload the binary your instructor gives you, and press
   **Start / apply project**. Wait until the pyghidra-mcp log shows the analysis is complete. The `pyghidra`
   route then appears in **Tools** and, after a page reload, in the chat.
2. Add `http://tools:8000/triage` as a tool server in Open WebUI's admin settings, as you did for `hexconv`.
   In the chat, enable `pyghidra` and `triage`. Ask:

   > List the functions in the binary. Decompile each one and run triage_decompiled on the result.
   > Report each finding with its CWE, the function, and the evidence line.

3. Repeat the same prompt three times with `triage` **disabled**, then three times enabled. Fill in the table:

   | Run | Tool enabled | Findings reported | Correct | Missed | Invented | Same as previous run? |
   |-----|--------------|-------------------|---------|--------|----------|-----------------------|

   Your instructor will tell you which findings are real once you hand in the table.
4. Upload a binary of your own choosing on the **Ghidra** tab, restart the project, and repeat.

Write two paragraphs: what the tool added over the bare model (consistency, structure, evidence you can check),
and what it cannot do.

Stretch: add a rule for a weakness that is not in the list, and show a binary where it fires.

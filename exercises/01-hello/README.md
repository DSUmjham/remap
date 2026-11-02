# Stage 1: Hello, MCP Tool

Goal: learn the development loop (edit, restart, test, use in chat) with the smallest tool.

1. Open the panel at http://localhost:8501, tab **Tools**. `hello` should show as served.
2. Under **Test a tool**, choose `hello`, `add`, and press **Call** with `{"a": 2, "b": 3}`.
3. Copy `exercises/01-hello/starter/hexconv.py` to `workspace/tools/hexconv.py`.
4. Work through the TODOs in that file. After each change press **Restart tools**, then test it in the panel.
5. Add `http://tools:8000/hexconv` as a tool server in Open WebUI's admin settings (see section 7.4 of the
   [student guide](../../docs/student-guide.md)). Then open the chat at http://localhost:3000, enable the
   `hexconv` tool, and ask the model to convert a number to hex.

Questions to answer in your notes:

- What did the model see that told it when to call your tool? (Hint: the docstring.)
- What happened when you raised an error? Where did the text appear?
- The lab runs your file over **stdio**; pyghidra-mcp is reached over **streamable-http**. What is
  the practical difference for restarting and for sharing one server between many clients?

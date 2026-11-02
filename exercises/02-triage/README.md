# Stage 2: A CWE Triage Tool

Goal: write a tool that flags risky patterns in decompiled C and returns structured results.
The model is allowed to guess; your tool is not. Same input, same output, with evidence.

1. Look at `snippets/`. These are Ghidra-style decompiler output for the functions of a small sample program.
   `add_checked.c` is a control with nothing wrong, and `tricky.c` has traps (comments, strings,
   similarly named functions).
2. Copy `starter/triage.py` to `workspace/tools/triage.py` and work through TODO 1 to 9.
3. Restart tools, open the panel **Test a tool**, and paste each snippet as `code`.
   Expected: `greet` hits R1 and R2, `log_message` hits R5, `run_ping` hits R7, `alloc_table` hits R9,
   `add_checked` and `tricky` produce no false positives for R1.
4. Read your output as a reviewer would. Which findings are real? Which are noise? The tool returns
   a `limitations` list; add one item of your own.

Regex over text is a triage aid, not an analysis. It cannot see data flow, so `strcpy` into a buffer that is
large enough is still reported. Discuss what a better tool would need.

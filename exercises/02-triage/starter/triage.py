"""Stage 2: a standalone CWE triage tool for decompiled C. Work through the TODOs.

Goal: given the decompiled source of one function, return the weaknesses it matches
as structured data. Your tool will give the same findings, in the same order and the 
same structure, every time, and each finding will name the rule behind it.

Test it WITHOUT Ghidra first, using the files in exercises/02-triage/snippets/.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("triage")

RULES_VERSION = "1"
MAX_CHARS = 200_000
MAX_LINES = 5_000


@dataclass(frozen=True)
class Rule:
    id: str
    cwe: str
    title: str
    severity: str  # high, medium, low
    pattern: re.Pattern[str]
    why: str
    needs_strings: bool = False  # True if the pattern must see string contents


# Order is part of the output: findings on the same line appear in rule order.
RULES: tuple[Rule, ...] = (
    Rule("R1", "CWE-120", "Unbounded string copy", "high",
         re.compile(r"\b(strcpy|strcat|wcscpy|wcscat|stpcpy)\s*\("),
         "Copies until a NUL byte with no length limit; overflows the destination if the source is longer."),
    Rule("R2", "CWE-120", "Unbounded formatted write", "high",
         re.compile(r"\b(sprintf|vsprintf)\s*\("),
         "Writes formatted output into a buffer with no length limit. Prefer snprintf."),
    # TODO 1: add a rule for gets()                        (CWE-242, high)
    # TODO 2: add a rule for printf(variable)              (CWE-134, high)
    #         The format argument must NOT start with a quote. Check log_message.c.
    # TODO 3: add TWO rules for system()/popen():          (CWE-78)
    #         high when the argument is not a string literal, low when it is.
    #         Why report the literal case at all? Check run_ping.c and tricky.c.
    # TODO 4: add a rule for malloc/realloc whose size uses * or <<   (CWE-190, medium)
    #         Hint: a lookahead, (?=[^;]*(?:\*|<<)), looks ahead without consuming.
    # TODO 5 (your choice): one rule for a weakness not listed here. Write the CWE,
    #         the pattern and the "why", and add a snippet that triggers it.
)

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def prepare_lines(code: str) -> list[tuple[int, str, str, str]]:
    """Return (line number, original text, code-only text, code-with-strings text).

    Comments are removed so commented-out code is not flagged. String *contents*
    are blanked so a message like "never call strcpy(x)" is not flagged, while the
    quote characters stay so rules can still tell a literal from a variable.
    """
    out = []
    in_block = False
    for number, original in enumerate(code.splitlines(), start=1):
        # Remove comments, tracking /* ... */ blocks that span lines.
        kept = []
        i = 0
        in_string = False
        while i < len(original):
            two = original[i : i + 2]
            ch = original[i]
            if in_block:
                if two == "*/":
                    in_block = False
                    i += 2
                else:
                    i += 1
                continue
            if in_string:
                kept.append(ch)
                if ch == "\\" and i + 1 < len(original):
                    kept.append(original[i + 1])
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue
            if two == "/*":
                in_block = True
                i += 2
                continue
            if two == "//":
                break
            if ch == '"':
                in_string = True
            kept.append(ch)
            i += 1
        with_strings = "".join(kept)
        blanked = re.sub(r'"(?:\\.|[^"\\])*"', '""', with_strings)
        out.append((number, original, blanked, with_strings))
    return out


def triage(code: str, function_name: str = "") -> dict:
    """Provided so you can test it without MCP.

    Return a dict with: rules_version, function, lines_scanned, finding_count,
    by_severity ({"high": n, "medium": n, "low": n}), cwes (sorted list), findings,
    and limitations (a sentence saying what this tool cannot tell you).

    Each finding is: rule, cwe, title, severity, line, function, evidence (the original
    line, stripped), why.
    """
    if len(code) > MAX_CHARS or code.count("\n") > MAX_LINES:
        raise ValueError("code is too large; send one function at a time")

    # TODO 6: loop over prepare_lines(code). For each line and each rule, search the
    #         rule's pattern in the right text: the string-blanked column normally, or
    #         the with-strings column when rule.needs_strings is True. Record a finding.
    # TODO 7: build and return the summary dict described above.
    raise NotImplementedError("finish triage")


# TODO 8: expose triage() as a tool named triage_decompiled(code, function_name=""),
#         with a docstring a MODEL can act on: say what to pass in, what comes back,
#         and that the output is deterministic.

# TODO 9: add a second tool, list_rules(), returning each rule's id, cwe, title,
#         severity, pattern and why. This is what makes your tool auditable.


if __name__ == "__main__":
    mcp.run()

DSU_BLUE = "#004165"      # Pantone 302 C, "DarkBLUE"
TROJAN_BLUE = "#00A9E0"   # Pantone 2995 C, "LightBLUE"
DARK_GRAY = "#4D4F53"     # Pantone Cool Gray 11
LIGHT_GRAY = "#F4F4F4"    # hex from the manual, see above
WHITE = "#FFFFFF"

BODY_FONT = "'Roboto', 'Helvetica Neue', Arial, sans-serif"


def css() -> str:
    """Page CSS for app.py. Falls back to system fonts when offline."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family: {BODY_FONT}; }}
h1, h2, h3 {{ color: {DSU_BLUE}; }}

/* Hide Streamlit's toolbar; the banner scrolled under it. */
header[data-testid="stHeader"] {{ display: none; }}
div[data-testid="stMainBlockContainer"] {{ padding-top: 2rem; }}

.remap-header {{
  background: {DSU_BLUE};
  color: {WHITE};
  padding: 1.1rem 1.5rem 1rem 1.5rem;
  border-bottom: 5px solid {TROJAN_BLUE};
  border-radius: 4px;
  margin-bottom: 1.25rem;
}}
.remap-header .remap-title {{
  font-size: 2.1rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1.1;
}}
.remap-header .remap-sub {{
  font-size: 0.95rem;
  opacity: 0.92;
  margin-top: 0.2rem;
}}

button[data-baseweb="tab"] {{ font-family: {BODY_FONT}; font-weight: 500; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: {DSU_BLUE}; }}
div[data-baseweb="tab-highlight"] {{ background-color: {TROJAN_BLUE}; }}

.remap-pill {{
  display: inline-block; padding: 0.1rem 0.6rem; border-radius: 999px;
  font-size: 0.85rem; font-weight: 500; border: 1px solid {DARK_GRAY};
}}
.remap-pill.ok  {{ background: {DSU_BLUE}; color: {WHITE}; border-color: {DSU_BLUE}; }}
.remap-pill.off {{ background: {LIGHT_GRAY}; color: {DARK_GRAY}; }}
</style>
"""


def header_html(title: str = "REMAP", subtitle: str = "Reverse Engineering MCP Authoring Platform") -> str:
    return (
        f'<div class="remap-header"><div class="remap-title">{title}</div>'
        f'<div class="remap-sub">{subtitle}</div></div>'
    )


def pill(text: str, ok: bool) -> str:
    return f'<span class="remap-pill {"ok" if ok else "off"}">{text}</span>'

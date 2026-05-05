PAPER = "#f6f2e9"
PAPER_ALT = "#efe9dc"
CARD = "#ffffff"
BORDER = "#e3dccb"
BORDER_LIGHT = "#d5ccb5"
INK = "#1a2332"
TEXT = "#1a2332"
TEXT_MUTED = "#64748b"
TEXT_DIM = "#9ca3a7"
PRIMARY = "#1a2332"
ACCENT = "#b8860b"
SUCCESS = "#4a7c59"
WARNING = "#c08f3f"
DANGER = "#a0402e"
DANGER_DEEP = "#7a2018"

PHASE_COLOR = {
    "Pre-Planning": "#6b7b96",
    "Planning": "#4a6990",
    "Fieldwork": "#b8860b",
    "Reporting": "#4a7c59",
    "Complete": "#9ca3a7",
}

RISK_COLOR = {
    "Low": "#4a7c59",
    "Medium": "#c08f3f",
    "High": "#a0402e",
    "Critical": "#7a2018",
}

USER_COLORS = ["#1a2332", "#b8860b", "#4a7c59", "#4a6990", "#a0402e", "#6b7b96", "#c08f3f", "#2d5434"]


CSS = f"""
<style>
  .stApp {{ background: {PAPER}; }}
  .main .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }}

  [data-testid="stSidebar"] {{ background: {CARD}; border-right: 1px solid {BORDER}; }}
  [data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}

  h1, h2, h3, h4, h5 {{
    font-family: Georgia, "Times New Roman", serif !important;
    color: {INK} !important;
    letter-spacing: -0.3px;
    font-weight: 600;
  }}
  h1 {{ font-size: 1.95rem; }}
  h2 {{ font-size: 1.45rem; }}
  h3 {{ font-size: 1.15rem; }}

  body, .stMarkdown, p, span, div, label {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: {TEXT};
  }}

  .ledger-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(26,35,50,0.03);
    margin-bottom: 14px;
  }}
  .ledger-kpi {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 16px 18px;
  }}
  .ledger-kpi .kpi-label {{
    font-size: 11px; color: {TEXT_MUTED}; text-transform: uppercase;
    font-weight: 700; letter-spacing: 0.7px;
  }}
  .ledger-kpi .kpi-value {{
    font-family: Georgia, serif; font-size: 32px; font-weight: 500;
    color: {INK}; letter-spacing: -0.6px; line-height: 1.1; margin-top: 4px;
  }}
  .ledger-kpi .kpi-sub {{
    font-size: 11px; color: {TEXT_DIM}; margin-top: 4px;
  }}

  .ledger-badge {{
    display: inline-block;
    padding: 3px 9px; border-radius: 4px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; white-space: nowrap;
    margin-right: 4px; margin-bottom: 2px;
  }}

  .ledger-brand {{
    display: flex; align-items: center; gap: 10px; padding-bottom: 16px;
    border-bottom: 1px solid {BORDER}; margin-bottom: 14px;
  }}
  .ledger-brand .crest {{
    width: 38px; height: 38px; border-radius: 9px;
    background: {INK}; border: 2px solid {ACCENT};
    display: inline-flex; align-items: center; justify-content: center;
    color: {ACCENT}; font-weight: 700; font-family: Georgia, serif;
  }}
  .ledger-brand .name {{
    font-family: Georgia, serif; font-size: 16px; font-weight: 600; color: {INK};
    letter-spacing: -0.3px;
  }}
  .ledger-brand .tag {{
    font-size: 9px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 1.4px;
  }}

  .stButton > button {{
    border-radius: 7px;
    font-weight: 600;
    border: 1px solid {BORDER_LIGHT};
    transition: all .15s;
  }}
  .stButton > button[kind="primary"] {{
    background: {INK}; color: {PAPER}; border-color: {INK};
  }}
  .stButton > button[kind="primary"]:hover {{
    background: #2d3d58; border-color: #2d3d58;
  }}
  .stDownloadButton > button {{
    border-radius: 7px; font-weight: 600;
    background: {INK}; color: {PAPER}; border: 1px solid {INK};
  }}

  .stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
  .stTabs [data-baseweb="tab"] {{
    padding: 10px 18px; font-weight: 600; color: {TEXT_MUTED};
  }}
  .stTabs [aria-selected="true"] {{ color: {INK}; border-bottom: 2px solid {ACCENT}; }}

  .stTextInput input, .stNumberInput input, .stSelectbox > div > div, .stTextArea textarea {{
    border-radius: 7px;
    border: 1px solid {BORDER_LIGHT};
    background: {CARD};
  }}

  #MainMenu {{ visibility: hidden; }}
  footer {{ visibility: hidden; }}
  header {{ visibility: hidden; }}
</style>
"""


def badge_html(text: str, color: str, solid: bool = False) -> str:
    if solid:
        return (
            f'<span class="ledger-badge" style="background:{color};color:#fff;'
            f'border:1px solid {color};">{text}</span>'
        )
    return (
        f'<span class="ledger-badge" style="background:{color}14;color:{color};'
        f'border:1px solid {color}55;">{text}</span>'
    )


def kpi_html(label: str, value, sub: str = "", color: str = INK) -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="ledger-kpi">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div>'
        f"{sub_html}"
        f"</div>"
    )

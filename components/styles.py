# -*- coding: utf-8 -*-
"""
components/styles.py — Systeme visuel FloMind Tresorerie v4.1
=============================================================
Refonte CSS complete : design premium, typographie soignee,
elevation par ombres (pas par bordures), hierarchie visuelle claire.
"""
import streamlit as st

# ── Palette centrale ───────────────────────────────────────────────────────
CARD_COLORS = {
    "bleu":   "#1D4ED8",
    "vert":   "#059669",
    "violet": "#7C3AED",
    "orange": "#D97706",
    "teal":   "#0891B2",
    "rouge":  "#DC2626",
    "gris":   "#6B7280",
}

# ── CSS ────────────────────────────────────────────────────────────────────
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ═══════════════════════════════════════════════════════════════
   BASE
═══════════════════════════════════════════════════════════════ */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
}
.stApp {
    background: #F0F4F8 !important;
}
.block-container {
    padding: 1.5rem 2rem 4rem !important;
    max-width: 1520px !important;
}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] > div:first-child {
    background: #0B1929 !important;
    border-right: 1px solid rgba(255,255,255,.04) !important;
}
[data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stSidebar"] * { color: #7A92B0 !important; }

/* Navigation radio */
[data-testid="stSidebar"] .stRadio label {
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 6px 16px !important;
    border-radius: 6px !important;
    margin: 1px 8px !important;
    display: block !important;
    cursor: pointer !important;
    transition: background .12s, color .12s !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,.05) !important;
    color: #C8D8EC !important;
}
[data-testid="stSidebar"] .stRadio [aria-checked=true] + label,
[data-testid="stSidebar"] .stRadio [aria-checked=true] ~ label {
    background: rgba(59,130,246,.15) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,.06) !important;
    margin: 10px 0 !important;
}

/* Slider navigation temporelle dans sidebar */
[data-testid="stSidebar"] .stSlider > div,
[data-testid="stSidebar"] [data-testid="stSelectSlider"] { padding: 0 16px !important; }
[data-testid="stSidebar"] [data-testid="stSelectSlider"] * { color: #94A3B8 !important; }
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] { margin-top: 4px !important; }

/* Bouton sidebar */
[data-testid="stSidebar"] button {
    background: rgba(59,130,246,.12) !important;
    border: 1px solid rgba(59,130,246,.25) !important;
    color: #93C5FD !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    margin: 0 8px !important;
    padding: 6px 0 !important;
    width: calc(100% - 16px) !important;
    transition: background .15s !important;
}
[data-testid="stSidebar"] button:hover {
    background: rgba(59,130,246,.22) !important;
}

/* ═══════════════════════════════════════════════════════════════
   CONTENEURS / CARTES
═══════════════════════════════════════════════════════════════ */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow:
        0 1px 3px rgba(15,23,42,.07),
        0 1px 2px rgba(15,23,42,.04) !important;
    overflow: hidden !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow:
        0 4px 12px rgba(15,23,42,.08),
        0 2px 4px rgba(15,23,42,.05) !important;
    transition: box-shadow .2s ease !important;
}

/* ═══════════════════════════════════════════════════════════════
   KPI CARDS CUSTOM
═══════════════════════════════════════════════════════════════ */
.fm-kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 18px;
}
.fm-kpi-card {
    background: #FFFFFF;
    border-radius: 10px;
    border-top: 3px solid #1D4ED8;
    padding: 18px 20px 16px;
    min-height: 130px;
    box-shadow: 0 1px 3px rgba(15,23,42,.07), 0 1px 2px rgba(15,23,42,.04);
    position: relative;
    overflow: hidden;
}
.fm-kpi-card::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 64px; height: 64px;
    border-radius: 0 10px 0 64px;
    opacity: .04;
    background: currentColor;
}
.fm-kpi-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .09em;
    color: #64748B;
    margin-bottom: 10px;
    line-height: 1.3;
}
.fm-kpi-value {
    font-size: 24px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -.03em;
    line-height: 1;
    margin-bottom: 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    font-variant-numeric: tabular-nums;
}
.fm-kpi-delta {
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 3px;
    margin-bottom: 4px;
}
.fm-kpi-delta.pos  { color: #059669; }
.fm-kpi-delta.neg  { color: #DC2626; }
.fm-kpi-delta.neut { color: #64748B; }
.fm-kpi-ref {
    font-size: 11px;
    color: #64748B;
    line-height: 1.4;
}

/* ═══════════════════════════════════════════════════════════════
   SECTION HEADERS
═══════════════════════════════════════════════════════════════ */
.fm-section {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 16px 0 10px;
}
.fm-section-bar {
    width: 3px;
    height: 16px;
    border-radius: 2px;
    flex-shrink: 0;
}
.fm-section-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: #334155;
}

/* ═══════════════════════════════════════════════════════════════
   ALERT COUNTERS
═══════════════════════════════════════════════════════════════ */
.fm-alert-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 14px;
}
.fm-alert-box {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(15,23,42,.07);
}
.fm-alert-dot-label {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 8px;
}
.fm-alert-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.fm-alert-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .09em;
    color: #475569;
}
.fm-alert-count {
    font-size: 40px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -.04em;
    line-height: 1;
    font-variant-numeric: tabular-nums;
}

/* ═══════════════════════════════════════════════════════════════
   FEED ALERTES
═══════════════════════════════════════════════════════════════ */
.fm-alert-item {
    padding: 10px 14px 10px 16px;
    margin-bottom: 4px;
    border-radius: 6px;
    font-size: 13px;
    border-left: 3px solid transparent;
    line-height: 1.5;
    display: flex;
    align-items: baseline;
    gap: 6px;
    flex-wrap: wrap;
}
.fm-alert-crit { background: #FEF2F2; border-left-color: #EF4444; }
.fm-alert-vigi { background: #FFFBEB; border-left-color: #F59E0B; }
.fm-alert-label {
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .06em;
    flex-shrink: 0;
}
.fm-alert-crit .fm-alert-label { color: #DC2626; }
.fm-alert-vigi .fm-alert-label { color: #D97706; }
.fm-alert-site  { color: #1E293B; font-weight: 600; font-size: 13px; }
.fm-alert-msg   { color: #475569; font-size: 12px; }
.fm-alert-sep   { color: #94A3B8; font-size: 11px; }

/* ═══════════════════════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════════════════════ */
[data-baseweb="tab-list"] {
    background: #F1F5F9 !important;
    border-radius: 8px !important;
    padding: 3px !important;
    gap: 2px !important;
    border: none !important;
}
[data-baseweb="tab"] {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    border-radius: 6px !important;
    padding: 5px 14px !important;
    border: none !important;
}
[data-baseweb="tab"]:hover { background: rgba(255,255,255,.6) !important; }
[aria-selected="true"][data-baseweb="tab"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(15,23,42,.08) !important;
}

/* ═══════════════════════════════════════════════════════════════
   TABLES
═══════════════════════════════════════════════════════════════ */
div[data-testid="stDataFrame"] thead th {
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: .07em !important;
    color: #475569 !important;
    background: #F8FAFC !important;
    border-bottom: 1px solid #E2E8F0 !important;
}
div[data-testid="stDataFrame"] tbody td {
    font-size: 13px !important;
    color: #1E293B !important;
}
div[data-testid="stDataFrame"] { border-radius: 8px !important; overflow: hidden !important; }

/* ═══════════════════════════════════════════════════════════════
   METRICS STREAMLIT NATIFS
═══════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
    background: #F8FAFC !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #475569 !important;
    text-transform: uppercase !important;
    letter-spacing: .06em !important;
}
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    letter-spacing: -.02em !important;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* ═══════════════════════════════════════════════════════════════
   SELECTBOX / INPUTS
═══════════════════════════════════════════════════════════════ */
[data-baseweb="select"] {
    font-size: 13px !important;
    border-radius: 7px !important;
}
[data-baseweb="select"] > div {
    border-color: #E2E8F0 !important;
    background: #FFFFFF !important;
    border-radius: 7px !important;
}
[data-baseweb="select"] > div:hover { border-color: #93C5FD !important; }

/* ═══════════════════════════════════════════════════════════════
   EXPANDER
═══════════════════════════════════════════════════════════════ */
details > summary {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #475569 !important;
    padding: 8px 0 !important;
}
details[open] > summary { color: #1E293B !important; }

/* ═══════════════════════════════════════════════════════════════
   SUCCESS / ERROR / WARNING (incidents, alertes)
═══════════════════════════════════════════════════════════════ */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 13px !important;
    border: none !important;
}
div[data-testid="stAlert"][data-baseweb="notification"][kind="negative"] {
    background: #FFF1F1 !important;
    border-left: 3px solid #EF4444 !important;
}
div[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
    background: #FFFBEB !important;
    border-left: 3px solid #F59E0B !important;
}

/* ═══════════════════════════════════════════════════════════════
   DIVIDER
═══════════════════════════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 1px solid rgba(15,23,42,.07) !important;
    margin: 12px 0 !important;
}

/* ═══════════════════════════════════════════════════════════════
   CAPTION
═══════════════════════════════════════════════════════════════ */
.stCaption, [data-testid="stCaptionContainer"] {
    font-size: 12px !important;
    color: #64748B !important;
    line-height: 1.6 !important;
}

/* ═══════════════════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
</style>"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ── Helpers HTML ──────────────────────────────────────────────────────────────

def section(title: str, color: str = "#1D4ED8") -> None:
    st.markdown(
        f'<div class="fm-section">'
        f'<div class="fm-section-bar" style="background:{color}"></div>'
        f'<div class="fm-section-title">{title}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str = "",
             ref: str = "", color: str = "#1D4ED8",
             delta_pos: bool | None = None) -> str:
    if delta:
        if delta_pos is True:    dc, arrow = "pos",  "▲"
        elif delta_pos is False: dc, arrow = "neg",  "▼"
        else:                    dc, arrow = "neut", ""
        delta_html = f'<div class="fm-kpi-delta {dc}">{arrow} {delta}</div>'
    else:
        delta_html = ""
    ref_html = f'<div class="fm-kpi-ref">{ref}</div>' if ref else ""
    return (
        f'<div class="fm-kpi-card" style="border-top-color:{color}">'
        f'<div class="fm-kpi-label">{label}</div>'
        f'<div class="fm-kpi-value">{value}</div>'
        f'{delta_html}{ref_html}'
        f'</div>'
    )


def kpi_row(cards: list[str]) -> None:
    html = '<div class="fm-kpi-row">' + "".join(cards) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def alert_counters(rouge: int, orange: int, gris: int = 0,
                   labels: tuple = ("Critiques", "Vigilance", "Surveillance")) -> None:
    def box(count, dot_color, label):
        return (
            f'<div class="fm-alert-box">'
            f'<div class="fm-alert-dot-label">'
            f'<div class="fm-alert-dot" style="background:{dot_color}"></div>'
            f'<div class="fm-alert-tag">{label}</div>'
            f'</div>'
            f'<div class="fm-alert-count">{count}</div>'
            f'</div>'
        )
    html = (
        '<div class="fm-alert-row">'
        + box(rouge,  "#EF4444", labels[0])
        + box(orange, "#F59E0B", labels[1])
        + box(gris,   "#94A3B8", labels[2])
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def alert_item(gravite: str, type_label: str,
               site: str, message: str, valeur: str = "") -> None:
    css   = "fm-alert-crit" if gravite == "rouge" else "fm-alert-vigi"
    badge = "Critique"  if gravite == "rouge" else "Vigilance"
    val_h = (f'<span class="fm-alert-sep">·</span>'
             f'<span style="font-weight:700;color:#374151">{valeur}</span>'
             if valeur else "")
    st.markdown(
        f'<div class="fm-alert-item {css}">'
        f'<span class="fm-alert-label">{badge}</span>'
        f'<span class="fm-alert-sep">·</span>'
        f'<span style="font-size:10px;color:#94A3B8">{type_label}</span>'
        f'<span class="fm-alert-sep">·</span>'
        f'<span class="fm-alert-site">{site}</span>'
        f'<span class="fm-alert-sep">·</span>'
        f'<span class="fm-alert-msg">{message}</span>'
        f'{val_h}'
        f'</div>',
        unsafe_allow_html=True,
    )

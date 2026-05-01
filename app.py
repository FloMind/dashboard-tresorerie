# -*- coding: utf-8 -*-
"""app.py — FloMind Dashboard Tresorerie v4
Changements v4 :
    - Navigation temporelle (slider mois dans la sidebar)
    - Sous-titres de vue dynamiques (mois courant)
    - Bouton export PDF (rapport executif 3 pages)
    - KPIs enrichis : point mort tresorerie + CCR
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
st.set_page_config(
    page_title="FloMind — Tresorerie",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.styles import inject
inject()

from core.loader import build_loader
from components.kpi_cards import render_header_kpis
from components.styles import section, CARD_COLORS
from components.aide import aide_expander
from utils.auth import check_auth
from config.settings import MOIS_COURANT_LABEL

if not check_auth(): st.stop()

import views.position     as v_position
import views.flux         as v_flux
import views.bfr          as v_bfr
import views.alertes      as v_alertes
import views.previsionnel as v_previsionnel
import views.budget       as v_budget
import views.guide        as v_guide


@st.cache_resource
def get_loader():
    return build_loader()

loader = get_loader()

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    st.markdown(
        '<div style="padding:20px 16px 12px">'
        '<div style="font-size:10px;font-weight:700;color:#1D4ED8;'
        'text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px">FloMind</div>'
        '<div style="font-size:18px;font-weight:800;color:#F1F5F9;'
        'letter-spacing:-.02em;line-height:1.1">Tresorerie<br>Dashboard</div>'
        '<div style="font-size:10px;color:#475569;margin-top:6px;'
        'text-transform:uppercase;letter-spacing:.06em">CDG · DATA · IA</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Navigation avec icônes ────────────────────────────────────────────
    # CSS : masque le radio Streamlit natif et recrée des boutons nav SaaS
    st.markdown("""
    <style>
    div[data-testid="stRadio"] > label { display:none !important; }
    div[data-testid="stRadio"] > div   { gap:2px !important; }
    div[data-testid="stRadio"] > div > label {
        display:flex !important; align-items:center !important;
        padding:8px 12px !important; border-radius:6px !important;
        cursor:pointer !important; transition:background .15s !important;
        font-size:13px !important; color:#94A3B8 !important;
        font-weight:500 !important;
    }
    div[data-testid="stRadio"] > div > label:hover {
        background:rgba(255,255,255,0.06) !important; color:#E2E8F0 !important;
    }
    div[data-testid="stRadio"] > div > label[data-baseweb="radio"] > div:first-child {
        display:none !important;
    }
    input[type="radio"]:checked + div + div + label,
    div[data-testid="stRadio"] > div > label:has(input:checked) {
        background:rgba(29,78,216,0.18) !important;
        color:#93C5FD !important; font-weight:600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    NAV_ITEMS = [
        "Tour de controle",
        "Flux de tresorerie",
        "BFR",
        "Alertes reseau",
        "Budget & Pilotage",
        "Previsionnel",
        "Guide d'utilisation",
    ]

    # Labels = valeurs directes (plus d'icône préfixée)
    nav_labels = NAV_ITEMS
    nav_values = NAV_ITEMS

    # Garder la vue sélectionnée en session_state
    if "vue_sel" not in st.session_state:
        st.session_state["vue_sel"] = nav_labels[0]

    vue_label = st.radio(
        "Navigation",
        nav_labels,
        index=nav_labels.index(st.session_state.get("vue_sel", nav_labels[0])),
        label_visibility="collapsed",
        key="nav_radio",
    )
    # Stocker pour persistence entre reruns
    st.session_state["vue_sel"] = vue_label
    # Extraire la valeur propre (sans icône) pour le routing
    vue = next((v for v in nav_values if vue_label.endswith(v)), nav_values[0])

    st.divider()

    # ── Navigation temporelle ─────────────────────────────────────────────
    st.markdown(
        '<div style="padding:0 16px;font-size:10px;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.08em;color:#475569;'
        'margin-bottom:6px">Periode d\'analyse</div>',
        unsafe_allow_html=True,
    )
    mois_dispo = loader.mois_reels_disponibles
    mois_def   = MOIS_COURANT_LABEL if MOIS_COURANT_LABEL in mois_dispo else mois_dispo[-1]
    mois_sel   = st.select_slider(
        "Mois courant",
        options=mois_dispo,
        value=mois_def,
        label_visibility="collapsed",
        key="mois_slider",
    )
    # Met a jour le mois courant du loader pour toutes les vues
    loader.set_mois_courant(mois_sel)

    # Perimetre info
    nb_sites = loader.soldes_raw["site_id"].nunique()
    st.markdown(
        f'<div style="padding:0 16px;font-size:11px;color:#94A3B8;line-height:1.8">'
        f'{nb_sites} sites reseau<br>'
        f'{mois_dispo[0]} → {mois_dispo[-1]}<br>'
        f'Mois courant : <b style="color:#F1F5F9">{mois_sel}</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Statut solde par site (top 6 worst)
    st.markdown(
        '<div style="padding:0 16px;font-size:10px;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.08em;color:#475569;'
        f'margin-bottom:8px">Statut Solde — {mois_sel}</div>',
        unsafe_allow_html=True,
    )
    sol_cur = loader.position()["soldes_site"]
    for _, r in sol_cur.sort_values("solde_fin").head(6).iterrows():
        fin = r["solde_fin"]
        c   = "#DC2626" if fin < 0 else "#D97706" if fin < 15_000 else "#059669"
        pct = f"{fin/1e3:+.0f}k€"
        nm  = r["site_nom"][:16]
        st.markdown(
            f'<div style="padding:2px 16px;display:flex;justify-content:space-between;'
            f'align-items:center">'
            f'<span style="font-size:11px;color:#94A3B8">{nm}</span>'
            f'<span style="font-size:11px;font-weight:700;color:{c}">{pct}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Export PDF ───────────────────────────────────────────────────────
    if st.button("Exporter rapport PDF", use_container_width=True, key="btn_pdf"):
        with st.spinner("Generation du rapport..."):
            try:
                from utils.pdf_export import generate_pdf
                from core.forecaster import TresoForecaster
                fc = TresoForecaster(loader)
                sc = fc.scenarios(horizon=6)
                pdf_bytes = generate_pdf(loader, sc)
                st.session_state["pdf_bytes"] = pdf_bytes
                st.success("PDF pret !")
            except Exception as e:
                st.error(f"Erreur PDF : {e}")

    if "pdf_bytes" in st.session_state:
        st.download_button(
            label="Telecharger le rapport",
            data=st.session_state["pdf_bytes"],
            file_name=f"rapport_treso_{mois_sel.replace(' ','_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="dl_pdf",
        )

    st.markdown(
        '<div style="padding:0 16px 16px">'
        '<div style="font-size:10px;color:#334155">FloMind Consulting</div>'
        '<div style="font-size:10px;color:#334155">CDG x Data x IA pour PME</div>'
        '<div style="font-size:10px;color:#334155;margin-top:2px">v4.0 · 2026</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Aide contextuelle — au-dessus des KPI cards ──────────────────────────
VUE_AIDE = {
    "Tour de controle":    "position",
    "Flux de tresorerie":  "flux",
    "BFR":                 "bfr",
    "Alertes reseau":      "alertes",
    "Budget & Pilotage":   "budget",
    "Previsionnel":        "previsionnel",
}
if vue in VUE_AIDE:
    aide_expander(VUE_AIDE[vue])

# ── Header KPIs ─────────────────────────────────────────────────────────
kpis = loader.kpi_global()
render_header_kpis(kpis)

# ── Bannière critique globale — impossible à rater ────────────────────────
if kpis.nb_sites_critiques > 0:
    sites_crit = (loader.position()["soldes_site"]
                  [loader.position()["soldes_site"]["runway_mois"] < 1]["site_nom"]
                  .tolist())
    noms = ", ".join(sites_crit[:4]) + ("…" if len(sites_crit) > 4 else "")
    st.error(
        f"**{kpis.nb_sites_critiques} site(s) en rupture de trésorerie** "
        f"({noms}) — Runway < 1 mois. Action immédiate requise.",
        icon="🚨",
    )
elif kpis.nb_sites_negatifs > 0:
    st.warning(
        f"**{kpis.nb_sites_negatifs} site(s) en solde négatif** ce mois. "
        f"Couverture CT réseau : {kpis.taux_couverture_ct:.2f}x.",
        icon="⚠️",
    )

# ── Titre de vue ─────────────────────────────────────────────────────────
SOUS_TITRES = {
    "Tour de controle":    f"Soldes · Runway · Incidents · {mois_sel}",
    "Flux de tresorerie":  "Waterfall · Evolution 28 mois · Comparaison annuelle",
    "BFR":                 "DSO · DPO · DIO · Balance clients · Stock · Fournisseurs",
    "Alertes reseau":      "Score de risque · Alertes consolidees · Priorites",
    "Budget & Pilotage":   "Budget vs Realise · Ecarts · Concentration clients",
    "Previsionnel":        "Forecast par composante · 3 scenarios · IC 80%",
    "Guide d'utilisation": "Navigation · Utilisation · Script presentation · Glossaire",
}
section(vue.upper(), CARD_COLORS["bleu"])
st.markdown(
    f'<div style="font-size:12px;color:#6B7280;margin:-6px 0 12px">'
    f'{SOUS_TITRES.get(vue,"")}</div>',
    unsafe_allow_html=True,
)

# ── Résumé narratif contextuel — insight first ────────────────────────────
if vue != "Guide d'utilisation":
    narr = loader.narrative(vue)
    if narr["texte"]:
        _fn = {"info": st.info, "warning": st.warning, "error": st.error}
        _fn.get(narr["niveau"], st.info)(narr["texte"])
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Routing ──────────────────────────────────────────────────────────────
if   vue == "Tour de controle":    v_position.render(loader)
elif vue == "Flux de tresorerie":  v_flux.render(loader)
elif vue == "BFR":                 v_bfr.render(loader)
elif vue == "Alertes reseau":      v_alertes.render(loader)
elif vue == "Budget & Pilotage":   v_budget.render(loader)
elif vue == "Previsionnel":        v_previsionnel.render(loader)
elif vue == "Guide d'utilisation": v_guide.render(loader)

# -*- coding: utf-8 -*-
"""views/position.py"""
import streamlit as st
from components.styles import section, CARD_COLORS
from components.aide import aide_expander
import pandas as pd
from components.charts import chart_evolution_solde, chart_heatmap_soldes
from components.formatters import fmt_eur

TYPE_LABELS = {
    "tresorerie": "Tresorerie",
    "client":     "Client",
    "stock":      "Stock",
    "fournisseur":"Fournisseur",
}

ACTIONS_SITE = {
    "tresorerie": "Virement DG ou acceleration recouvrement",
    "client":     "Relance ou mise en demeure client",
    "stock":      "Reapprovisionnement urgent",
    "fournisseur":"Negociation delai fournisseur",
}


def _statut(rag):
    return {"rouge": "Critique", "orange": "Vigilance", "vert": "Normal"}.get(rag, "")


def render(loader) -> None:
    data     = loader.position()
    sol      = data["soldes_site"].copy()
    evo      = data["evolution"]
    incidents = data["incidents"]

    nb_neg  = int((sol["solde_fin"] < 0).sum())
    nb_crit = int((sol["runway_mois"] < 1).sum())
    nb_vig  = int(((sol["runway_mois"] >= 1) & (sol["runway_mois"] < 3)).sum())
    nb_ok   = int((sol["runway_mois"] >= 3).sum())

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Solde negatif",    f"{nb_neg} sites",
                  delta="Action immediate", delta_color="inverse",
                  help="Nombre de sites dont le solde bancaire est négatif ce mois. "
                       "Un solde négatif = découvert bancaire en cours.")
        c2.metric("Runway < 1 mois",  f"{nb_crit} sites",
                  delta="Critique", delta_color="inverse",
                  help="Runway = Solde / Décaissements moyens mensuels. "
                       "Sous 1 mois : le site sera à sec dans moins de 30 jours "
                       "sans action immédiate (virement DG ou ligne de crédit).")
        c3.metric("Runway < 3 mois",  f"{nb_vig} sites",
                  delta="Surveillance", delta_color="off",
                  help="Sites avec 1 à 3 mois de trésorerie disponible. "
                       "Surveillance active : accélérer le recouvrement "
                       "et surveiller les décaissements exceptionnels.")
        c4.metric("Runway >= 3 mois", f"{nb_ok} sites",
                  help="Sites en situation normale. "
                       "Runway > 3 mois = coussin de sécurité suffisant "
                       "pour absorber un choc d'encaissement d'1 à 2 mois.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.plotly_chart(chart_evolution_solde(evo),
                        use_container_width=True,
                        config={"displayModeBar": False})

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    col_tbl, col_hm = st.columns([1, 2], gap="medium")

    with col_tbl:
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:12px;font-weight:600;color:#374151;'
                f'text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">'
                f'Classement sites — {loader._mois_courant}</div>',
                unsafe_allow_html=True,
            )
            rows = []
            for _, r in sol.sort_values("solde_fin").iterrows():
                rows.append({
                    "Statut":   _statut(r["rag"]),
                    "Site":     r["site_nom"],
                    "Solde":    fmt_eur(r["solde_fin"]),
                    "Flux net": fmt_eur(r["flux_net"], sign=True),
                    "Runway":   f"{r['runway_mois']:.1f} m",
                })
            df_disp = pd.DataFrame(rows)

            def hl(row):
                if row["Statut"] == "Critique":
                    return ["background-color:#FEF2F2"] * len(row)
                if row["Statut"] == "Vigilance":
                    return ["background-color:#FFFBEB"] * len(row)
                return [""] * len(row)

            st.dataframe(df_disp.style.apply(hl, axis=1),
                         height=510, use_container_width=True, hide_index=True)

    with col_hm:
        with st.container(border=True):
            st.plotly_chart(chart_heatmap_soldes(loader.soldes_raw),
                            use_container_width=True,
                            config={"displayModeBar": False})

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Plan d'action ─────────────────────────────────────────────────────────
    alertes    = loader.alertes()
    rouge_site = {}
    for a in alertes:
        if a.gravite == "rouge" and a.site_id not in rouge_site:
            rouge_site[a.site_id] = a

    rouges = sol[sol["rag"] == "rouge"].sort_values("solde_fin")

    if len(rouges):
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:12px;font-weight:600;color:#DC2626;'
                'text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px">'
                f'Plan d\'action — {len(rouges)} site(s) critique(s)</div>',
                unsafe_allow_html=True,
            )
            for _, r in rouges.iterrows():
                a        = rouge_site.get(r["site_id"])
                type_a   = a.type if a else "tresorerie"
                action   = ACTIONS_SITE.get(type_a, "A traiter en priorite")
                type_lbl = TYPE_LABELS.get(type_a, type_a)
                solde_fmt  = fmt_eur(r["solde_fin"])
                runway_fmt = f"{r['runway_mois']:.1f} mois"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;'
                    f'padding:9px 12px;border-radius:7px;background:#FFF8F8;'
                    f'border-left:3px solid #EF4444;margin-bottom:5px">'
                    f'<div style="flex:1;min-width:0">'
                    f'<span style="font-size:12px;font-weight:700;color:#1E293B">'
                    f'{r["site_id"]} — {r["site_nom"]}</span>'
                    f'<span style="font-size:11px;color:#94A3B8;margin-left:8px">'
                    f'{solde_fmt} · runway {runway_fmt}</span>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#6B7280;flex-shrink:0">{type_lbl}</div>'
                    f'<div style="font-size:11px;font-weight:600;color:#1D4ED8;'
                    f'flex-shrink:0">&rarr; {action}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    elif nb_vig > 0:
        with st.container(border=True):
            st.warning(
                f"Aucun site en situation critique. "
                f"{nb_vig} site(s) en vigilance — runway < 3 mois."
            )
    else:
        with st.container(border=True):
            st.success("Tous les sites sont en situation normale ce mois.")

    aide_expander("position")

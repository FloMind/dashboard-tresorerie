# -*- coding: utf-8 -*-
"""views/budget.py — Vue Budget & Pilotage."""
import streamlit as st
import pandas as pd
from components.styles import section, CARD_COLORS
from components.charts import chart_budget_ecart, chart_budget_mensuel
from components.formatters import fmt_eur


def _concentration_gauge(pct: float, label: str, seuil_orange: float,
                          seuil_rouge: float) -> None:
    """Mini-jauge textuelle avec coloration RAG — sans emoji."""
    if pct >= seuil_rouge:
        color, tag = "#DC2626", "Critique"
    elif pct >= seuil_orange:
        color, tag = "#D97706", "Vigilance"
    else:
        color, tag = "#059669", "Normal"
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:7px 0;border-bottom:0.5px solid #F1F5F9">'
        f'<span style="font-size:13px;color:#374151">{label}</span>'
        f'<span style="font-size:13px;font-weight:600;color:{color}">'
        f'{pct:.1f}% '
        f'<span style="font-size:11px;font-weight:500;background:{color}18;'
        f'padding:1px 7px;border-radius:10px">{tag}</span>'
        f'</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render(loader) -> None:
    bdg = loader.budget_vs_reel()

    if not bdg:
        st.info(
            "Fichier **budget_treso.xlsx** non trouvé dans data/. "
            "Ajoutez-le pour activer cette vue.",
        )
        return

    an       = bdg["annee"]
    taux_ca  = bdg["taux_realisation_ca"]
    ecart_fx = bdg["ecart_flux_ytd"]
    ca_r     = bdg["ca_reel_ytd"]
    ca_b     = bdg["ca_budget_ytd"]

    # ── KPIs synthétiques ────────────────────────────────────────────────────
    with st.container(border=True):
        st.caption(
            f"Budget vs Réalisé {an} — Réseau consolidé — jusqu'à {loader._mois_courant}"
        )
        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Taux réalisation CA",
            f"{taux_ca:.1f}%",
            delta=f"{taux_ca - 100:+.1f}pt vs objectif",
            delta_color="normal" if taux_ca >= 100 else "inverse",
            help="CA encaissé YTD / CA budgété YTD × 100. "
                 "Un taux < 100% peut indiquer un retard d'encaissement "
                 "(vérifier le niveau de facturation avant de conclure "
                 "à une baisse d'activité).",
        )
        c2.metric("CA réalisé YTD",  fmt_eur(ca_r),
                  help=f"Chiffre d'affaires encaissé du 1er janvier au mois de {an}.")
        c3.metric("CA budget YTD",   fmt_eur(ca_b),
                  help=f"Chiffre d'affaires budgété du 1er janvier au mois de {an}. "
                       "Issu du fichier budget_treso.xlsx.")
        c4.metric(
            "Écart flux net YTD",
            fmt_eur(ecart_fx, sign=True),
            delta="Favorable" if ecart_fx >= 0 else "Défavorable",
            delta_color="normal" if ecart_fx >= 0 else "inverse",
            help="Flux net réalisé YTD − Flux net budgété YTD. "
                 "Favorable = plus de cash que prévu. "
                 "Défavorable = moins de cash que prévu. "
                 "Analyser par poste pour identifier l'origine de l'écart.",
        )
        cat       = bdg["par_sous_categorie"]
        nb_defav  = int((cat["favorable"] == False).sum())
        nb_total  = len(cat)
        c5.metric(
            "Postes défavorables",
            f"{nb_defav} / {nb_total}",
            delta="Vérifier détail",
            delta_color="inverse" if nb_defav > nb_total // 2 else "off",
            help="Nombre de postes budgétaires dont le réalisé est moins bon que le budget. "
                 "Favorable = plus encaissé ou moins dépensé que prévu. "
                 "Voir le tableau détaillé pour identifier les postes prioritaires.",
        )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Graphiques côte à côte ───────────────────────────────────────────────
    col_l, col_r = st.columns([3, 2], gap="medium")

    with col_l:
        with st.container(border=True):
            section("Écarts par poste")
            st.plotly_chart(
                chart_budget_ecart(cat),
                use_container_width=True, config={"displayModeBar": False},
            )
            st.caption(
                "Vert = favorable (plus encaissé ou moins dépensé que prévu). "
                "Rouge = défavorable."
            )

    with col_r:
        with st.container(border=True):
            section("Évolution mensuelle")
            st.plotly_chart(
                chart_budget_mensuel(bdg["par_mois"]),
                use_container_width=True, config={"displayModeBar": False},
            )
            st.caption(
                "Barres = écart mensuel. Pleine = réalisé. Pointillée = budget."
            )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Tableau détaillé ────────────────────────────────────────────────────
    with st.container(border=True):
        section(f"Détail par poste — {an} YTD")

        # Filtres inline
        fc1, fc2, _ = st.columns([1, 1, 3])
        f_statut = fc1.selectbox(
            "Statut", ["Tous", "Favorable", "Défavorable"], key="bdg_statut"
        )
        f_cat = fc2.selectbox(
            "Catégorie",
            ["Toutes"] + sorted(cat["categorie"].dropna().unique().tolist()),
            key="bdg_cat",
        )

        cat_aff = cat.copy()
        if f_statut == "Favorable":
            cat_aff = cat_aff[cat_aff["favorable"] == True]
        elif f_statut == "Défavorable":
            cat_aff = cat_aff[cat_aff["favorable"] == False]
        if f_cat != "Toutes":
            cat_aff = cat_aff[cat_aff["categorie"] == f_cat]

        cat_aff["Réalisé"]  = cat_aff["reel"].apply(fmt_eur)
        cat_aff["Budget"]   = cat_aff["budget"].apply(fmt_eur)
        cat_aff["Écart"]    = cat_aff["ecart"].apply(lambda v: fmt_eur(v, sign=True))
        cat_aff["Écart %"]  = cat_aff["ecart_pct"].apply(lambda v: f"{v:+.1f}%")
        cat_aff["Statut"]   = cat_aff["favorable"].map(
            {True: "Favorable", False: "Défavorable"}
        )

        def hl_bdg(row):
            if "Favorable" in str(row["Statut"]):
                return ["background-color:#F0FDF4"] * len(row)
            return ["background-color:#FEF2F2"] * len(row)

        st.dataframe(
            cat_aff[["sous_categorie", "categorie", "Réalisé", "Budget",
                      "Écart", "Écart %", "Statut"]]
            .rename(columns={"sous_categorie": "Poste", "categorie": "Catégorie"})
            .style.apply(hl_bdg, axis=1),
            use_container_width=True, hide_index=True,
        )

        # Export CSV
        csv = cat_aff[["sous_categorie", "categorie", "reel", "budget",
                        "ecart", "ecart_pct", "favorable"]].to_csv(index=False)
        st.download_button(
            "⬇ Télécharger en CSV",
            data=csv,
            file_name=f"budget_vs_reel_{an}_{loader._mois_courant.replace(' ','_')}.csv",
            mime="text/csv",
            key="dl_bdg_csv",
        )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Concentration clients ────────────────────────────────────────────────
    with st.container(border=True):
        section("Concentration clients réseau — risque systémique")
        conc = loader.concentration_clients()
        res  = conc["reseau"]

        st.caption(
            "Un client > 30% du CA d'un site = risque systémique. "
            "Top 3 > 50% = dépendance forte. HHI > 0.18 = marché concentré."
        )

        col_g, col_t = st.columns([1, 2], gap="medium")

        with col_g:
            st.markdown(
                '<div style="font-size:12px;font-weight:600;color:#374151;'
                'margin-bottom:8px">Réseau consolidé</div>',
                unsafe_allow_html=True,
            )
            _concentration_gauge(res["top1_pct"],  "Client n°1",          30, 40)
            _concentration_gauge(res["top3_pct"],  "Top 3 clients",       50, 65)
            _concentration_gauge(res["top10_pct"], "Top 10 clients",      75, 85)

        with col_t:
            # Tableau par site — top3_pct coloré
            ps = conc["par_site"].copy()
            if len(ps):
                def hl_site(row):
                    t3 = float(str(row.get("top3_pct", 0)).replace("%", ""))
                    if t3 >= 65:
                        return ["background-color:#FEF2F2"] * len(row)
                    if t3 >= 50:
                        return ["background-color:#FFFBEB"] * len(row)
                    return [""] * len(row)

                ps_aff = ps.copy()
                for col_pct in ["top1_pct", "top3_pct", "top10_pct"]:
                    if col_pct in ps_aff.columns:
                        ps_aff[col_pct] = ps_aff[col_pct].apply(lambda v: f"{v:.1f}%")
                if "herfindahl" in ps_aff.columns:
                    ps_aff["HHI"] = ps_aff["herfindahl"].apply(lambda v: f"{v:.3f}")
                if "nb_clients" in ps_aff.columns:
                    ps_aff["nb_clients"] = ps_aff["nb_clients"].astype(int)

                cols_show = ["site_nom", "nb_clients", "top1_pct",
                             "top3_pct", "top10_pct", "HHI"]
                cols_show = [c for c in cols_show if c in ps_aff.columns]
                st.dataframe(
                    ps_aff[cols_show].rename(columns={
                        "site_nom": "Site", "nb_clients": "Clients",
                        "top1_pct": "Top 1", "top3_pct": "Top 3",
                        "top10_pct": "Top 10",
                    }).style.apply(hl_site, axis=1),
                    use_container_width=True, hide_index=True, height=280,
                )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Top clients individuels ──────────────────────────────────────────────
    with st.expander("Top 30 clients par CA annuel"):
        tc = conc["top_clients"].copy()
        if len(tc):
            if "ca_annuel" in tc.columns:
                tc["CA annuel"] = tc["ca_annuel"].apply(fmt_eur)
            if "encours" in tc.columns:
                tc["Encours"]   = tc["encours"].apply(fmt_eur)
            cols_tc = ["site_nom", "client_nom", "secteur", "CA annuel", "Encours"]
            cols_tc = [c for c in cols_tc if c in tc.columns]
            st.dataframe(
                tc[cols_tc].rename(columns={
                    "site_nom": "Site", "client_nom": "Client", "secteur": "Secteur"
                }),
                use_container_width=True, hide_index=True,
            )


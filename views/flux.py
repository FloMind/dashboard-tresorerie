# -*- coding: utf-8 -*-
"""views/flux.py"""
import streamlit as st
from components.styles import section, CARD_COLORS
import pandas as pd
from components.charts import (
    chart_waterfall, chart_flux_mensuel,
)
from components.formatters import fmt_eur


def render(loader) -> None:
    sites = ["Reseau consolide"] + sorted(loader.flux_raw["site_nom"].unique().tolist())
    choix = st.selectbox("Perimetre", sites, key="flux_site")
    site_id = None
    if choix != "Reseau consolide":
        site_id = loader.flux_raw.set_index("site_nom")["site_id"].to_dict().get(choix)

    data = loader.flux(site_id)
    wf   = data["waterfall_courant"]
    enc  = wf[wf["montant"] > 0]["montant"].sum()
    dec  = abs(wf[wf["montant"] < 0]["montant"].sum())
    net  = enc - dec

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Encaissements", fmt_eur(enc),
                  help=f"Total des entrées de trésorerie sur {loader._mois_courant}. "
                       "Principalement les encaissements clients TTC.")
        c2.metric("Decaissements", fmt_eur(dec),
                  help=f"Total des sorties de trésorerie sur {loader._mois_courant}. "
                       "Inclut fournisseurs, salaires, charges, TVA, loyers, emprunt, CAPEX.")
        c3.metric("Flux net",      fmt_eur(net, sign=True),
                  delta=fmt_eur(net, sign=True), delta_color="normal",
                  help="Flux net = Encaissements − Décaissements. "
                       "Positif : le mois génère du cash. "
                       "Négatif : le mois consomme de la trésorerie.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        f"Waterfall — {loader._mois_courant}",
        "Evolution 28 mois",
        "Analyse annuelle",
    ])

    fx_source = (loader.flux_raw if site_id is None
                 else loader.flux_raw[loader.flux_raw["site_id"] == site_id])

    with tab1:
        with st.container(border=True):
            st.plotly_chart(chart_waterfall(wf),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption("Chaque barre = un poste de flux. Barre bleue = flux net total du mois.")

    with tab2:
        with st.container(border=True):
            st.plotly_chart(chart_flux_mensuel(fx_source),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption("Barres empilees par categorie. Ligne noire = flux net mensuel.")

    with tab3:
        n1 = data["n_vs_n1"]
        if "an_n1" in n1.columns and "an_courant" in n1.columns:
            lbl_n1      = n1["an_n1_label"].iloc[0]      if len(n1) else "N-1"
            lbl_courant = n1["an_courant_label"].iloc[0] if len(n1) else "N"
            with st.container(border=True):
                section(f"Comparaison {lbl_courant} vs {lbl_n1}")
                df_aff = n1.copy()
                df_aff[lbl_n1]      = df_aff["an_n1"].apply(fmt_eur)
                df_aff[lbl_courant] = df_aff["an_courant"].apply(fmt_eur)
                df_aff["Variation"] = n1["evolution_pct"].apply(
                    lambda x: f"{'+ ' if x > 0 else '- '}{abs(x):.1f}%")
                def col_d(row):
                    pct = n1.loc[row.name, "evolution_pct"] if row.name in n1.index else 0
                    cat = str(n1.loc[row.name, "categorie"]) if row.name in n1.index else ""
                    bon = (pct > 0) == ("ENCAISS" in cat)
                    return [""] * (len(row)-1) + [
                        f"background-color:{'#F0FDF4' if bon else '#FEF2F2'}"]
                st.dataframe(
                    df_aff[["categorie", lbl_n1, lbl_courant, "Variation"]]
                    .rename(columns={"categorie": "Categorie"}),
                    use_container_width=True, hide_index=True)

        if data["top_contributeurs"] is not None:
            with st.container(border=True):
                section(f"Contribution des sites — {loader._mois_courant}")
                top = data["top_contributeurs"].head(10).copy()
                tot = top["montant"].abs().sum()
                top["Contribution"] = (top["montant"]/tot*100).round(1).astype(str) + "%"
                top["Flux net"]     = top["montant"].apply(lambda x: fmt_eur(x, sign=True))
                st.dataframe(
                    top[["site_id","site_nom","profil","Flux net","Contribution"]]
                    .rename(columns={"site_id":"ID","site_nom":"Site","profil":"Profil"}),
                    use_container_width=True, hide_index=True)


# -*- coding: utf-8 -*-
"""views/bfr.py — Vue BFR.
Ajout : filtre site (perimetre site specifique ou reseau consolide).
"""
import streamlit as st
from components.styles import section, CARD_COLORS
from components.aide import aide_expander
import pandas as pd
from components.charts import chart_aging_donut, chart_bfr_evolution
from components.formatters import fmt_eur, fmt_jours
from config.settings import BENCH


def _ratio(col, label, val, bench_min, bench_max, help_txt=""):
    if val < bench_min: delta, dc = f"Sous benchmark ({bench_min}j)", "normal"
    elif val > bench_max: delta, dc = f"Au-dessus benchmark ({bench_max}j)", "inverse"
    else:                 delta, dc = f"Dans la norme ({bench_min}-{bench_max}j)", "off"
    col.metric(label, fmt_jours(val), delta, delta_color=dc,
               help=help_txt if help_txt else None)


def render(loader) -> None:
    # ── Filtre site ──────────────────────────────────────────────────────────
    sites   = ["Reseau consolide"] + sorted(
        loader.balance_cli_raw["site_nom"].unique().tolist()
    )
    site_sel = st.selectbox("Perimetre", sites, key="bfr_site")
    site_id  = None
    if site_sel != "Reseau consolide":
        site_id = (loader.balance_cli_raw
                   .set_index("site_nom")["site_id"]
                   .to_dict().get(site_sel))

    data = loader.bfr(site_id=site_id)
    rat  = data["ratios_reseau"]

    with st.container(border=True):
        label_perim = site_sel if site_id else "Reseau consolide"
        st.caption(f"Moyennes ponderees par CA · Benchmark negoce B2B France · {label_perim}")
        c1, c2, c3, c4 = st.columns(4)
        _ratio(c1, "DSO — Delai clients",      rat["dso"], *BENCH["dso"],
               help_txt="Days Sales Outstanding — délai moyen entre facturation et encaissement. "
                        "Formule : Encours clients / CA × 30. "
                        "Benchmark négoce B2B France : 45–55 jours. "
                        "Chaque journée supplémentaire = CA/360 € immobilisés.")
        _ratio(c2, "DPO — Delai fournisseurs", rat["dpo"], *BENCH["dpo"],
               help_txt="Days Payable Outstanding — délai moyen de paiement fournisseur. "
                        "Formule : Encours fournisseurs / Achats × 30. "
                        "Plafond légal LME : 60 jours. Benchmark : 30–45 jours. "
                        "Un DPO élevé améliore la trésorerie mais risque les pénalités.")
        _ratio(c3, "DIO — Rotation stocks",    rat["dio"], *BENCH["dio"],
               help_txt="Days Inventory Outstanding — durée moyenne de rotation des stocks. "
                        "Formule : Valeur stock / Achats × 30. "
                        "DIO > 90j sur une catégorie = stock dormant. "
                        "Benchmark négoce : 20–35 jours.")
        _ratio(c4, "CCC — Cycle conversion",   rat["ccc"], *BENCH["ccc"],
               help_txt="Cash Conversion Cycle = DSO + DIO − DPO. "
                        "Durée entre décaissement des achats et encaissement des ventes. "
                        "Négatif = vous êtes payé avant de payer (position idéale). "
                        "Benchmark négoce : 40–70 jours.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "BFR et evolution",
        "Balance clients",
        "Stock",
        "Fournisseurs",
    ])

    with tab1:
        with st.container(border=True):
            # Evolution sur le reseau (chart toujours reseau pour la lisibilite)
            st.plotly_chart(chart_bfr_evolution(loader.flux_raw),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption(
                "BFR estime mensuel = Creances (DSO 47j) + Stocks (DIO 28j) "
                "- Dettes fournisseurs (DPO 38j), calcule depuis les flux reels."
            )

        with st.container(border=True):
            section("BFR par site — " + loader._mois_courant)
            bfr_s = data["bfr_par_site"].sort_values("bfr", ascending=False).copy()
            for col_f in ["bfr","creances","stocks","dettes"]:
                bfr_s[col_f.capitalize()] = bfr_s[col_f].apply(fmt_eur)
            st.dataframe(
                bfr_s[["site_nom","profil","Bfr","Creances","Stocks","Dettes"]]
                .rename(columns={"site_nom":"Site","profil":"Profil",
                                  "Bfr":"BFR","Creances":"Creances"}),
                use_container_width=True, hide_index=True, height=280)

    with tab2:
        col_d, col_t = st.columns([1, 2], gap="medium")
        with col_d:
            with st.container(border=True):
                st.plotly_chart(chart_aging_donut(data["aging_consolide"]),
                                use_container_width=True, config={"displayModeBar": False})
                tot    = data["aging_total"]
                retard = tot - data["aging_consolide"]["Non echu"]
                st.caption(
                    f"Encours total : **{fmt_eur(tot)}**  \n"
                    f"En retard : **{fmt_eur(retard)}** ({retard/tot*100:.1f}%)"
                    if tot > 0 else "Aucun encours"
                )
        with col_t:
            with st.container(border=True):
                section("Clients a surveiller")
                cr = data["top_risque_cli"]
                if len(cr):
                    rows = []
                    for _, r in cr.head(12).iterrows():
                        rows.append({
                            "Site":     r["site_nom"],
                            "Client":   r["client_nom"][:28],
                            "Secteur":  r["secteur"],
                            "Encours":  fmt_eur(r["encours_total"]),
                            "+90j":     fmt_eur(r["dont_plus_90j"]),
                            "Retard":   f"{r['jours_retard_moy']:.0f}j",
                            "Statut":   r["statut_risque"],
                        })
                    df_r = pd.DataFrame(rows)
                    def hl(row):
                        if row["Statut"] == "Contentieux":
                            return ["background-color:#FEF2F2"] * len(row)
                        return ["background-color:#FFFBEB"] * len(row)
                    st.dataframe(df_r.style.apply(hl, axis=1),
                                 use_container_width=True, hide_index=True, height=320)
                else:
                    st.success("Aucun client a risque sur ce perimetre.")

    with tab3:
        with st.container(border=True):
            abc = data["stock_abc"]
            if len(abc):
                cols_abc = st.columns(min(len(abc), 3))
                for col_st, (_, r) in zip(cols_abc, abc.iterrows()):
                    cat = r["categorie_abc"]
                    col_st.metric(
                        f"Categorie {cat} — {fmt_eur(r['valeur_stock'])}",
                        f"DIO moyen {r['dio_moyen']:.0f}j",
                        delta=f"Dormant {r['taux_dormant_pct']:.1f}%",
                        delta_color="inverse" if r["taux_dormant_pct"] > 5 else "off",
                        help=f"Catégorie ABC {cat} : "
                             f"{'80% du CA (20% des références)' if cat=='A' else '15% du CA (30% des références)' if cat=='B' else '5% du CA (50% des références)'}. "
                             f"DIO = rotation moyenne en jours. "
                             f"Taux dormant = % de références sans mouvement depuis 90j+."
                    )
        sa = data["stock_alertes"]
        if len(sa):
            with st.container(border=True):
                section("References en alerte")
                st.dataframe(
                    sa[["ref_id","designation","categorie_abc","site_nom",
                         "qte_stock","stock_mini","valeur_stock_ht",
                         "statut_stock","dernier_mvt_jours"]]
                    .rename(columns={
                        "ref_id":"Reference","designation":"Designation",
                        "categorie_abc":"Cat","site_nom":"Site",
                        "qte_stock":"Qte","stock_mini":"Mini",
                        "valeur_stock_ht":"Valeur HT",
                        "statut_stock":"Statut","dernier_mvt_jours":"Dern. mvt (j)"}),
                    use_container_width=True, hide_index=True, height=260)

    with tab4:
        with st.container(border=True):
            fou = data["four_retard"]
            if len(fou):
                section(f"{len(fou)} depassements detectes")
                st.dataframe(
                    fou.rename(columns={
                        "site_nom":"Site","fournisseur_nom":"Fournisseur",
                        "type_fournisseur":"Type","encours_total":"Encours",
                        "dont_30_60j_et_plus":"Retard 30j+",
                        "conditions_paiement":"Conditions"}),
                    use_container_width=True, hide_index=True)
            else:
                st.success("Aucun depassement fournisseur sur ce perimetre.")

    aide_expander("bfr")

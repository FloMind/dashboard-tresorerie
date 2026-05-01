# -*- coding: utf-8 -*-
"""views/previsionnel.py — Vue Prévisionnel."""
import streamlit as st
from components.styles import section, CARD_COLORS
import pandas as pd
from core.forecaster import TresoForecaster
from components.charts import chart_forecast, chart_forecast_composantes
from components.formatters import fmt_eur



def render(loader) -> None:
    fc = TresoForecaster(loader)

    # ── Paramètres ─────────────────────────────────────────────────────────
    with st.container(border=True):
        st.caption("Paramètres des scénarios — modifiez les valeurs pour simuler")
        c1, c2, c3, c4 = st.columns(4)
        horizon        = c1.slider("Horizon (mois)", 3, 12, 6)
        delta_enc_opt  = c2.slider("Encaissements optimiste (+%)", 5, 25, 10) / 100
        delta_enc_pess = c3.slider("Encaissements pessimiste (−%)", 5, 20, 8) / 100
        delta_dso_pess = c4.slider("DSO pessimiste (+jours)", 5, 20, 12)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Calcul ─────────────────────────────────────────────────────────────
    sc = fc.scenarios(
        horizon=horizon,
        delta_enc_opt=delta_enc_opt,
        delta_enc_pess=-delta_enc_pess,
        delta_dso_pess=delta_dso_pess,
        delta_dpo_opt=5,
    )
    df_base = sc["base"]
    df_opt  = sc["optimiste"]
    df_pess = sc["pessimiste"]

    # Solde de départ : mois courant sélectionné par le slider (dynamique)
    mois_courant = loader._mois_courant
    pos_data = loader.position()
    evo      = pos_data["evolution"]
    sol_dep  = evo[evo["mois_label"] == mois_courant]["solde_reseau"].values
    sol_dep  = float(sol_dep[0]) if len(sol_dep) else 0.0

    # ── KPIs scénarios ─────────────────────────────────────────────────────
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Solde départ ({mois_courant})", fmt_eur(sol_dep),
                  help="Solde bancaire réseau au mois courant sélectionné. "
                       "C'est le point de départ de tous les scénarios forecast.")
        c2.metric(f"Base — {horizon} mois",
                  fmt_eur(df_base["solde"].iloc[-1]),
                  delta=fmt_eur(df_base["flux_net"].sum(), sign=True),
                  delta_color="normal",
                  help="Prolongement de la tendance actuelle (WLS sur l'historique). "
                       "La valeur affichée est le solde prévu dans {horizon} mois. "
                       "Le delta = variation totale de trésorerie sur la période.")
        c3.metric(f"Optimiste (+{int(delta_enc_opt*100)}%)",
                  fmt_eur(df_opt["solde"].iloc[-1]),
                  delta=fmt_eur(df_opt["solde"].iloc[-1] - sol_dep, sign=True),
                  delta_color="normal",
                  help=f"Scénario avec encaissements +{int(delta_enc_opt*100)}% "
                       "et DSO raccourci. Correspond à une campagne de recouvrement efficace "
                       "ou à une accélération des paiements clients.")
        c4.metric(f"Pessimiste (−{int(delta_enc_pess*100)}%)",
                  fmt_eur(df_pess["solde"].iloc[-1]),
                  delta=fmt_eur(df_pess["solde"].iloc[-1] - sol_dep, sign=True),
                  delta_color="normal",
                  help=f"Scénario avec encaissements −{int(delta_enc_pess*100)}% "
                       "et DSO allongé. Correspond à un ralentissement des paiements clients "
                       "ou à un choc d'activité.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Graphiques ─────────────────────────────────────────────────────────
    evo_reel = evo[evo["est_reel"] == True].sort_values("periode_idx")

    # Ligne budget cible : solde cumule depuis le solde de depart
    # Calcule uniquement si le fichier budget est present et couvre l'horizon
    budget_mensuel_fc = None
    bdg = loader.budget_vs_reel()
    if bdg:
        par_mois_bdg = bdg["par_mois"].copy()
        # Extraire uniquement les mois du forecast
        mois_fc = set(df_base["mois_label"])
        par_mois_bdg = par_mois_bdg[par_mois_bdg["mois_label"].isin(mois_fc)]
        if len(par_mois_bdg) > 0:
            par_mois_bdg = par_mois_bdg.sort_values("periode_idx")
            par_mois_bdg["solde_budget_cumul"] = sol_dep + par_mois_bdg["flux_budget"].cumsum()
            budget_mensuel_fc = par_mois_bdg[["mois_label", "solde_budget_cumul"]]

    with st.container(border=True):
        st.plotly_chart(chart_forecast(evo_reel, df_base, df_opt, df_pess,
                                       budget_mensuel=budget_mensuel_fc),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.plotly_chart(chart_forecast_composantes(df_base),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption(
            f"Décomposition du scénario base · tx. de marque réseau : "
            f"{fc.tx_marque:.1%} · masse salariale : {fc.tx_sal_ca:.1%} du CA"
        )

    # ── Table mensuelle ─────────────────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        section("Tableau mensuel des scénarios")
        rows = []
        for i, mois in enumerate(df_base["mois_label"]):
            s_b = df_base["solde"].iloc[i]
            s_o = df_opt["solde"].iloc[i]
            s_p = df_pess["solde"].iloc[i]
            fn  = df_base["flux_net"].iloc[i]
            alerte = "Rupture possible" if s_p < 0 else \
                     "Tension" if s_p < 20_000 else ""
            rows.append({
                "Mois":           mois,
                "Flux net (base)":fmt_eur(fn, sign=True),
                "Solde base":     fmt_eur(s_b),
                "Solde optimiste":fmt_eur(s_o),
                "Solde pessimiste":fmt_eur(s_p),
                "Alerte":         alerte,
            })
        df_tbl = pd.DataFrame(rows)
        def col_tbl(row):
            if row["Alerte"] == "Rupture possible":
                return ["background-color:#FEF2F2"] * len(row)
            if row["Alerte"] == "Tension":
                return ["background-color:#FFFBEB"] * len(row)
            return [""] * len(row)
        st.dataframe(df_tbl.style.apply(col_tbl, axis=1),
                     use_container_width=True, hide_index=True)

    # ── Méthodologie ────────────────────────────────────────────────────────
    with st.expander("Méthodologie du forecast par composante"):
        an_n1_label = str(int(mois_courant.split()[-1]) - 1)
        st.markdown(f"""
Contrairement à une extrapolation globale du solde, ce forecast utilise **la logique économique propre à chaque poste**.

| Composante | Méthode | Poids flux |
|---|---|---|
| Encaissements clients | WLS + saisonnalité N-1 ({an_n1_label}) | ~80% des entrées |
| Paiements fournisseurs | Déduit du CA prév × (1−{fc.tx_marque:.0%}) | ~60% des sorties |
| Masse salariale | WLS tendance | ~{fc.tx_sal_ca:.0%} du CA |
| TVA nette | Règle : f(CA × 20%), décalée d'1 mois | calendrier CA3 |
| Loyers | Fixe + indexation 2%/an | contractuel |
| Remboursement emprunt | Fixe par contrat | contractuel |
| Capex | Pattern saisonnier T1/T3 | budgété |
| Impôts/taxes | CFE décembre, CVAE mai/sept | calendrier fiscal |

Intervalle de confiance 80% basé sur les résidus historiques des encaissements (z = 1.28, croissant avec l'horizon).
""")


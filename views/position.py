# -*- coding: utf-8 -*-
"""
views/position.py — Tour de contrôle v4
=========================================
Principe : le header global (render_header_kpis) affiche déjà
Solde / Flux net / Couverture CT / Point mort / EBE / BFR.
Cette vue NE RÉPÈTE PAS ces KPIs — elle les DÉCOMPOSE.

Structure :
    Bloc 1 — Bandeau de statut réseau (verdict en 1 ligne)
    Bloc 2 — Santé du réseau : compteurs runway + graphique évolution
    Bloc 3 — BFR décomposé : créances / stocks / dettes fournisseurs
    Bloc 4 — Structure du flux mois courant (encaissements vs décaissements)
    Bloc 5 — Message d'action global
"""
import streamlit as st
from components.styles import section, alert_counters, CARD_COLORS
from components.charts import chart_evolution_solde
from components.formatters import fmt_eur


# ── Helpers ───────────────────────────────────────────────────────────────────

def _statut_global(nb_crit: int, nb_vig: int, nb_neg: int) -> tuple[str, str, str]:
    if nb_crit > 0 or nb_neg > 0:
        return "RÉSEAU EN ALERTE", "#FEF2F2", "#DC2626"
    if nb_vig > 0:
        return "RÉSEAU SOUS SURVEILLANCE", "#FFFBEB", "#D97706"
    return "RÉSEAU EN SITUATION NORMALE", "#F0FDF4", "#059669"


def _jauge_html(label: str, valeur: float, ref: float,
                unite: str = "j", inverse: bool = False,
                alerte_txt: str = "") -> str:
    """
    Mini-jauge horizontale comparant valeur vs référence sectorielle.
    inverse=True : valeur haute = mauvais (DSO, DIO).
    inverse=False : valeur haute = bon (DPO).
    """
    if ref <= 0:
        return ""
    pct = min(valeur / ref * 100, 150)
    if inverse:
        color = "#DC2626" if valeur > ref * 1.1 else "#D97706" if valeur > ref else "#059669"
    else:
        color = "#059669" if valeur >= ref * 0.9 else "#D97706" if valeur >= ref * 0.7 else "#DC2626"

    barre_pct = min(pct, 100)
    alerte_div = (f'<div style="font-size:10px;color:{color};margin-top:2px">{alerte_txt}</div>'
                  if alerte_txt else "")
    return (
        f'<div style="margin:6px 0 10px">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:11px;color:#64748B;margin-bottom:3px">'
        f'<span><b style="color:#1E293B">{valeur:.0f}{unite}</b> {label}</span>'
        f'<span style="color:#94A3B8">réf. {ref:.0f}{unite}</span>'
        f'</div>'
        f'<div style="background:#F1F5F9;border-radius:3px;height:5px;overflow:hidden">'
        f'<div style="background:{color};width:{barre_pct}%;height:100%;border-radius:3px"></div>'
        f'</div>'
        f'{alerte_div}'
        f'</div>'
    )


def _ligne_flux(label: str, montant: float,
                positif: bool, pct_total: float) -> str:
    """Ligne de décomposition du flux avec mini-barre proportionnelle."""
    color = "#059669" if positif else "#DC2626"
    sign  = "+" if positif else "−"
    barre = min(abs(pct_total), 100)
    return (
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'padding:5px 0;border-bottom:1px solid #F1F5F9">'
        f'<div style="width:130px;font-size:12px;color:#475569;flex-shrink:0">{label}</div>'
        f'<div style="flex:1;background:#F8FAFC;border-radius:3px;height:8px;overflow:hidden">'
        f'<div style="background:{color}33;width:{barre}%;height:100%;border-radius:3px"></div>'
        f'</div>'
        f'<div style="font-size:13px;font-weight:700;color:{color};'
        f'width:90px;text-align:right;flex-shrink:0">{sign} {fmt_eur(abs(montant))}</div>'
        f'</div>'
    )


def render(loader) -> None:
    data  = loader.position()
    sol   = data["soldes_site"].copy()
    evo   = data["evolution"]
    kpis  = loader.kpi_global()
    mois  = loader._mois_courant

    # ── Compteurs réseau ──────────────────────────────────────────────────────
    nb_total   = len(sol)
    nb_crit    = int((sol["runway_mois"] < 1).sum())
    nb_vig     = int(((sol["runway_mois"] >= 1) & (sol["runway_mois"] < 3)).sum())
    nb_ok      = int((sol["runway_mois"] >= 3).sum())
    nb_neg     = int((sol["solde_fin"] < 0).sum())
    runway_moy = float(sol["runway_mois"].mean())

    # ── Données BFR ───────────────────────────────────────────────────────────
    cli = loader.balance_cli_raw.copy()
    fou = loader.balance_fou_raw.copy()
    sto = loader.stock_raw.copy()
    bfr_r = loader.bfr_raw.copy()

    # Créances clients
    enc_total   = cli["encours_total"].sum()
    enc_retard  = cli[["dont_30_60j", "dont_60_90j", "dont_plus_90j"]].sum().sum()
    enc_90plus  = cli["dont_plus_90j"].sum()
    pct_retard  = enc_retard / enc_total * 100 if enc_total > 0 else 0
    nb_conten   = int((cli["statut_risque"] == "Contentieux").sum())

    # Stocks
    sto_total   = sto["valeur_stock_ht"].sum()
    sto_dormant = sto["valeur_dormante"].sum()
    pct_dormant = sto_dormant / sto_total * 100 if sto_total > 0 else 0
    nb_ruptures = int(sto["alerte_rupture"].sum())
    nb_surstk   = int(sto["alerte_surstockage"].sum())

    # Dettes fournisseurs
    det_total   = fou["encours_total"].sum()
    nb_depasse  = int(fou["alerte_depassement"].sum())
    enc_depasse = fou[fou["alerte_depassement"] == True]["encours_total"].sum()
    pct_depasse = enc_depasse / det_total * 100 if det_total > 0 else 0

    # DSO / DIO / DPO moyens (mois courant, pondérés)
    bfr_cur = bfr_r[bfr_r["mois_label"] == mois]
    dso_moy = float(bfr_cur["dso_jours"].mean()) if len(bfr_cur) else 0
    dpo_moy = float(bfr_cur["dpo_jours"].mean()) if len(bfr_cur) else 0
    dio_moy = float(bfr_cur["dio_jours"].mean()) if len(bfr_cur) else 0

    # ── Flux du mois décomposé ────────────────────────────────────────────────
    fx_cur = loader.flux_raw[loader.flux_raw["mois_label"] == mois]
    def _get(sous_cat: str) -> float:
        return float(fx_cur[fx_cur["sous_categorie"] == sous_cat]["montant"].sum())

    enc_cl   = _get("Encaissements clients")         # positif
    pmt_four = _get("Paiements fournisseurs")          # négatif
    salaires = _get("Masse salariale")                 # négatif
    charges  = _get("Charges d'exploitation")          # négatif
    tva      = _get("TVA nette")                       # négatif
    loyers   = _get("Loyers et charges locatives")     # négatif
    emprunt  = _get("Remboursement emprunt")           # négatif
    capex    = _get("Capex")                           # négatif
    flux_net = float(fx_cur["montant"].sum())

    dec_total = abs(pmt_four + salaires + charges + tva + loyers + emprunt + capex)

    # =========================================================================
    # BLOC 1 — Bandeau statut global
    # =========================================================================
    label_statut, bg_statut, border_statut = _statut_global(nb_crit, nb_vig, nb_neg)
    if nb_crit > 0 or nb_neg > 0:
        sous_titre = f"{nb_crit} site(s) en rupture · {nb_neg} solde(s) négatif(s) · Action immédiate"
        icone = "🔴"
    elif nb_vig > 0:
        sous_titre = f"{nb_vig} site(s) en vigilance · Runway moyen : {runway_moy:.1f} mois · À piloter"
        icone = "🟡"
    else:
        sous_titre = f"Runway moyen : {runway_moy:.1f} mois · {nb_total} sites en situation normale"
        icone = "🟢"

    st.markdown(
        f'<div style="background:{bg_statut};border:1.5px solid {border_statut};'
        f'border-radius:10px;padding:14px 20px;margin-bottom:14px;'
        f'display:flex;align-items:center;gap:14px">'
        f'<div style="font-size:22px">{icone}</div>'
        f'<div>'
        f'<div style="font-size:13px;font-weight:800;color:{border_statut};'
        f'text-transform:uppercase;letter-spacing:.1em">{label_statut}</div>'
        f'<div style="font-size:12px;color:#475569;margin-top:2px">'
        f'{mois} — {sous_titre}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


    # =========================================================================
    # BLOC 2 — Santé réseau : compteurs + graphique
    # =========================================================================
    col_cnt, col_evo = st.columns([1, 2], gap="medium")

    with col_cnt:
        with st.container(border=True):
            section("Runway — santé réseau")
            alert_counters(
                rouge=nb_crit,
                orange=nb_vig,
                gris=nb_ok,
                labels=("Critique < 1m", "Vigilance < 3m", "Normal ≥ 3m"),
            )
            st.markdown(
                f'<div style="padding:10px 0 4px;font-size:12px;color:#64748B;'
                f'border-top:1px solid #F1F5F9;margin-top:4px">'
                f'Runway moyen réseau : <b style="color:#1E293B">{runway_moy:.1f} mois</b>'
                f'<br>Sites en solde négatif : <b style="color:{"#DC2626" if nb_neg > 0 else "#059669"}">'
                f'{nb_neg} / {nb_total}</b>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_evo:
        with st.container(border=True):
            st.plotly_chart(
                chart_evolution_solde(evo),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # =========================================================================
    # BLOC 3 — BFR décomposé : créances / stocks / dettes
    # =========================================================================
    section("Décomposition du BFR réseau", CARD_COLORS["teal"])

    c_enc, c_sto, c_det = st.columns(3, gap="medium")

    with c_enc:
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#0891B2;margin-bottom:6px">Créances clients</div>'
                f'<div style="font-size:24px;font-weight:800;color:#0F172A;'
                f'letter-spacing:-.02em">{fmt_eur(enc_total)}</div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:2px;margin-bottom:8px">'
                f'Encours total réseau</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                _jauge_html("DSO moyen", dso_moy, ref=50, unite="j", inverse=True,
                            alerte_txt=f"Au-dessus de la référence 50j" if dso_moy > 50 else ""),
                unsafe_allow_html=True,
            )
            # Indicateurs qualité
            retard_col = "#DC2626" if pct_retard > 20 else "#D97706" if pct_retard > 10 else "#059669"
            conten_col = "#DC2626" if nb_conten > 0 else "#059669"
            st.markdown(
                f'<div style="display:flex;flex-direction:column;gap:5px;margin-top:4px">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Retard > 30j</span>'
                f'<span style="font-weight:700;color:{retard_col}">'
                f'{pct_retard:.1f}% · {fmt_eur(enc_retard)}</span></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Retard > 90j</span>'
                f'<span style="font-weight:700;color:{retard_col}">{fmt_eur(enc_90plus)}</span></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Contentieux</span>'
                f'<span style="font-weight:700;color:{conten_col}">{nb_conten} client(s)</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with c_sto:
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#7C3AED;margin-bottom:6px">Stocks réseau</div>'
                f'<div style="font-size:24px;font-weight:800;color:#0F172A;'
                f'letter-spacing:-.02em">{fmt_eur(sto_total)}</div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:2px;margin-bottom:8px">'
                f'Valeur stock HT réseau</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                _jauge_html("DIO moyen", dio_moy, ref=28, unite="j", inverse=True,
                            alerte_txt=f"Rotation lente — au-dessus de la référence 28j" if dio_moy > 28 else ""),
                unsafe_allow_html=True,
            )
            dorm_col = "#DC2626" if pct_dormant > 15 else "#D97706" if pct_dormant > 8 else "#059669"
            rupt_col = "#DC2626" if nb_ruptures > 5 else "#D97706" if nb_ruptures > 0 else "#059669"
            st.markdown(
                f'<div style="display:flex;flex-direction:column;gap:5px;margin-top:4px">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Stock dormant</span>'
                f'<span style="font-weight:700;color:{dorm_col}">'
                f'{pct_dormant:.1f}% · {fmt_eur(sto_dormant)}</span></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Ruptures</span>'
                f'<span style="font-weight:700;color:{rupt_col}">{nb_ruptures} référence(s)</span></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Surstockages</span>'
                f'<span style="font-weight:700;color:#D97706">{nb_surstk} référence(s)</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with c_det:
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#059669;margin-bottom:6px">Dettes fournisseurs</div>'
                f'<div style="font-size:24px;font-weight:800;color:#0F172A;'
                f'letter-spacing:-.02em">{fmt_eur(det_total)}</div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:2px;margin-bottom:8px">'
                f'Encours total réseau</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                _jauge_html("DPO moyen", dpo_moy, ref=38, unite="j", inverse=False,
                            alerte_txt=f"DPO court — levier de négociation possible" if dpo_moy < 30 else ""),
                unsafe_allow_html=True,
            )
            dep_col = "#DC2626" if nb_depasse > 3 else "#D97706" if nb_depasse > 0 else "#059669"
            st.markdown(
                f'<div style="display:flex;flex-direction:column;gap:5px;margin-top:4px">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Dépassements LME</span>'
                f'<span style="font-weight:700;color:{dep_col}">'
                f'{nb_depasse} fournisseur(s)</span></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">Encours en retard</span>'
                f'<span style="font-weight:700;color:{dep_col}">{fmt_eur(enc_depasse)}'
                f' ({pct_depasse:.0f}%)</span></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px">'
                f'<span style="color:#64748B">BFR = Cré. + Stock − Det.</span>'
                f'<span style="font-weight:700;color:#1E293B">'
                f'{fmt_eur(enc_total + sto_total - det_total)}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # =========================================================================
    # BLOC 4 — Structure du flux mois courant
    # =========================================================================
    section(f"Structure du flux — {mois}", CARD_COLORS["bleu"])

    with st.container(border=True):
        col_fl, col_net = st.columns([3, 1], gap="medium")

        with col_fl:
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.07em;color:#64748B;margin-bottom:10px">'
                f'Encaissements vs Décaissements</div>',
                unsafe_allow_html=True,
            )
            lignes = (
                _ligne_flux("Clients (enc.)", enc_cl, True,
                            enc_cl / dec_total * 100 if dec_total else 0)
                + _ligne_flux("Fournisseurs", abs(pmt_four), False,
                              abs(pmt_four) / dec_total * 100 if dec_total else 0)
                + _ligne_flux("Masse salariale", abs(salaires), False,
                              abs(salaires) / dec_total * 100 if dec_total else 0)
                + _ligne_flux("Charges exploit.", abs(charges), False,
                              abs(charges) / dec_total * 100 if dec_total else 0)
                + _ligne_flux("TVA nette", abs(tva), False,
                              abs(tva) / dec_total * 100 if dec_total else 0)
                + _ligne_flux("Loyers", abs(loyers), False,
                              abs(loyers) / dec_total * 100 if dec_total else 0)
                + _ligne_flux("Emprunt + Capex", abs(emprunt) + abs(capex), False,
                              (abs(emprunt) + abs(capex)) / dec_total * 100 if dec_total else 0)
            )
            st.markdown(f'<div style="padding:0 4px">{lignes}</div>',
                        unsafe_allow_html=True)

        with col_net:
            flux_col   = "#059669" if flux_net >= 0 else "#DC2626"
            flux_sign  = "+" if flux_net >= 0 else ""
            flux_label = "Génération" if flux_net >= 0 else "Consommation"
            st.markdown(
                f'<div style="text-align:center;padding:20px 10px">'
                f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#64748B;margin-bottom:8px">Flux net</div>'
                f'<div style="font-size:32px;font-weight:800;color:{flux_col};'
                f'letter-spacing:-.03em">{flux_sign}{fmt_eur(flux_net)}</div>'
                f'<div style="font-size:11px;color:{flux_col};margin-top:4px">'
                f'{flux_label} de cash</div>'
                f'<div style="margin-top:20px;font-size:11px;color:#64748B">'
                f'Enc. clients<br>'
                f'<b style="font-size:14px;color:#1E293B">{fmt_eur(enc_cl)}</b></div>'
                f'<div style="margin-top:10px;font-size:11px;color:#64748B">'
                f'Déc. totaux<br>'
                f'<b style="font-size:14px;color:#1E293B">{fmt_eur(dec_total)}</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )


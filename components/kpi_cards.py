# -*- coding: utf-8 -*-
"""components/kpi_cards.py"""
from components.formatters import fmt_eur, fmt_pct
from components.styles import kpi_row, kpi_card, CARD_COLORS


def _delta_label(val: float, unit: str = "eur") -> str:
    if unit == "pct":
        return f"{'▲' if val >= 0 else '▼'} {abs(val):.1f}% vs M-1"
    v = abs(val)
    sign = "▲" if val >= 0 else "▼"
    if v >= 1_000_000:
        return f"{sign} {v/1e6:.1f} M€ vs M-1"
    if v >= 10_000:
        return f"{sign} {v/1e3:.0f} k€ vs M-1"
    return f"{sign} {v:,.0f} € vs M-1"


def _couverture_label(ratio: float) -> tuple[str, str, bool]:
    """Retourne (delta_text, ref_text, delta_pos) selon le niveau du ratio."""
    if ratio >= 1.5:
        return f"Confortable (seuil 1.0)", "Solde / (Four. + Emprunt CT)", True
    if ratio >= 1.0:
        return f"Acceptable (seuil 1.0)", "Solde / (Four. + Emprunt CT)", True
    if ratio >= 0.5:
        return f"Alerte — sous 1.0", "Risque de defaut CT", False
    return f"Critique — sous 0.5", "Insuffisance de tresorerie", False


def render_header_kpis(kpis) -> None:
    sol   = kpis.solde_reseau
    flux  = kpis.flux_net_courant
    ebe   = kpis.ebe_cash_ytd_pct
    bfr   = kpis.bfr_reseau
    al    = kpis.nb_alertes
    pm    = kpis.point_mort_mensuel
    ccr   = kpis.cash_conversion
    ca    = kpis.ca_reseau_annualise
    ca_m  = ca / 12 if ca > 0 else 0.0
    d_sol = kpis.delta_solde_m1
    d_fx  = kpis.delta_flux_m1
    cct   = kpis.taux_couverture_ct

    marge_pm = ((ca_m - pm) / pm * 100) if pm > 0 else 0.0
    cct_delta, cct_ref, cct_pos = _couverture_label(cct)

    # Couleur couverture CT : vert >= 1.5, orange 1.0-1.5, rouge < 1.0
    cct_color = (CARD_COLORS["vert"] if cct >= 1.5
                 else CARD_COLORS["orange"] if cct >= 1.0
                 else CARD_COLORS["rouge"])

    cards = [
        kpi_card(
            "Solde reseau", fmt_eur(sol),
            delta=_delta_label(d_sol),
            ref=f"{kpis.nb_sites_negatifs} negatifs · {kpis.nb_sites_critiques} critiques",
            color=CARD_COLORS["bleu"],
            delta_pos=d_sol >= 0,
        ),
        kpi_card(
            "Flux net mois", fmt_eur(flux, sign=True),
            delta=_delta_label(d_fx),
            ref="Encaissements - Decaissements",
            color=CARD_COLORS["vert"] if flux >= 0 else CARD_COLORS["rouge"],
            delta_pos=flux >= 0,
        ),
        kpi_card(
            "Couverture CT", f"{cct:.2f}x",
            delta=cct_delta,
            ref=cct_ref,
            color=cct_color,
            delta_pos=cct_pos,
        ),
        kpi_card(
            "Point mort tresorerie", fmt_eur(pm),
            delta=f"Marge securite {marge_pm:+.0f}%",
            ref=f"CA mensuel : {fmt_eur(ca_m)} HT",
            color=CARD_COLORS["orange"] if marge_pm > 0 else CARD_COLORS["rouge"],
            delta_pos=marge_pm > 10,
        ),
        kpi_card(
            "EBE cash YTD", fmt_pct(ebe, sign=True),
            delta=f"{'Au-dessus' if ebe >= 3 else 'Sous'} benchmark 3-7%",
            ref=f"CCR : {ccr:.2f}",
            color=CARD_COLORS["violet"],
            delta_pos=ebe >= 3,
        ),
        kpi_card(
            "BFR reseau", fmt_eur(bfr),
            delta="Creances + Stock - Dettes",
            ref=f"Alertes actives : {al}",
            color=CARD_COLORS["teal"],
            delta_pos=None,
        ),
    ]
    kpi_row(cards)

# -*- coding: utf-8 -*-
"""
utils/pdf_export.py -- FloMind Dashboard Tresorerie
=====================================================
Export PDF executif 3 pages.

Page 1 : KPIs + Soldes par site (top 10 worst)
Page 2 : Alertes critiques + Ratios BFR
Page 3 : Previsionnel 6 mois (3 scenarios)

Usage :
    from utils.pdf_export import generate_pdf
    pdf_bytes = generate_pdf(loader, scenarios_dict)
    st.download_button("Telecharger PDF", pdf_bytes, "rapport_treso.pdf", "application/pdf")

Dependance : fpdf2 >= 2.7.9
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

import pandas as pd
from fpdf import FPDF

# Couleurs FloMind
_BLEU   = (29,  78,  216)
_ROUGE  = (185, 28,  28)
_ORANGE = (180, 83,  9)
_VERT   = (15,  110, 78)
_GRIS   = (100, 116, 139)
_NOIR   = (15,  23,  42)
_GRIS_L = (241, 245, 249)


class _PDF(FPDF):
    _subtitle = ""

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_BLEU)
        self.cell(80, 5, "FloMind - Dashboard Tresorerie", align="L")
        self.set_text_color(*_GRIS)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5,
                  f"Confidentiel · Genere le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                  align="R")
        self.ln(5)
        self.set_draw_color(203, 213, 225)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_GRIS)
        self.cell(0, 4,
                  f"FloMind Consulting - CDG x Data x IA · Page {self.page_no()}",
                  align="C")

    def section_title(self, txt: str, color=_BLEU) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.set_fill_color(*_GRIS_L)
        self.cell(0, 6, txt.upper(), fill=True, ln=True)
        self.ln(2)

    def kpi_row(self, items: list[tuple[str, str, str]]) -> None:
        """items = [(label, valeur, delta), ...]"""
        w = 190 / len(items)
        y0 = self.get_y()
        for label, valeur, delta in items:
            x0 = self.get_x()
            self.set_draw_color(203, 213, 225)
            self.set_fill_color(255, 255, 255)
            self.rect(x0, y0, w - 2, 22, "DF")
            self.set_xy(x0 + 2, y0 + 2)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*_GRIS)
            self.cell(w - 4, 4, label[:28], ln=True)
            self.set_x(x0 + 2)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*_NOIR)
            self.cell(w - 4, 7, valeur[:18], ln=True)
            self.set_x(x0 + 2)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*_GRIS)
            self.cell(w - 4, 4, delta[:32], ln=True)
            self.set_xy(x0 + w, y0)
        self.ln(26)

    def table_row(self, cells: list[str], widths: list[int],
                  fill: bool = False, bold: bool = False) -> None:
        """Ligne de tableau avec cellules."""
        if fill:
            self.set_fill_color(*_GRIS_L)
        else:
            self.set_fill_color(255, 255, 255)
        style = "B" if bold else ""
        self.set_font("Helvetica", style, 7)
        self.set_text_color(*_NOIR)
        for cell, w in zip(cells, widths):
            self.cell(w, 5, str(cell)[:24], border=1, fill=fill, align="L")
        self.ln()


def _fmt(val: float) -> str:
    """Formatage monetaire court."""
    if abs(val) >= 1_000_000:
        return f"{val/1e6:.2f} Me"
    if abs(val) >= 10_000:
        return f"{val/1e3:.0f} ke"
    return f"{val:,.0f} E"


def _safe(s: str, maxlen: int = 60) -> str:
    """Encode-safe pour fpdf Helvetica (latin-1). Tronque a maxlen."""
    return s[:maxlen].encode('latin-1', errors='replace').decode('latin-1')



def generate_pdf(loader, scenarios: dict | None = None) -> bytes:
    """
    Genere le rapport PDF executif.

    Parametres :
        loader    : TresoLoader charge
        scenarios : dict {"base": df, "optimiste": df, "pessimiste": df}
                    Si None, la page 3 est omise.

    Retourne :
        bytes du PDF
    """
    kpis    = loader.kpi_global()
    pos     = loader.position()
    alertes = loader.alertes()
    bfr     = loader.bfr()
    mois    = loader._mois_courant

    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(10, 14, 10)

    # ==========================================================================
    # PAGE 1 : KPIs + Soldes sites
    # ==========================================================================
    pdf.add_page()

    # En-tete rapport
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*_BLEU)
    pdf.cell(0, 8, f"Rapport Tresorerie - {mois}", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_GRIS)
    pdf.cell(0, 5, f"Reseau 30 sites · FloMind Consulting", ln=True)
    pdf.ln(4)

    # KPIs header
    pdf.section_title("Indicateurs cles")
    nb_neg  = kpis.nb_sites_negatifs
    nb_crit = kpis.nb_sites_critiques
    marge   = ((kpis.ca_reseau_annualise / 12 - kpis.point_mort_mensuel)
                / kpis.point_mort_mensuel * 100) if kpis.point_mort_mensuel > 0 else 0

    pdf.kpi_row([
        ("Solde reseau", _fmt(kpis.solde_reseau),
         f"{nb_neg} negatifs · {nb_crit} critiques"),
        ("Flux net mois", _fmt(kpis.flux_net_courant),
         f"YTD : {_fmt(kpis.flux_net_ytd)}"),
        ("CA annualise", _fmt(kpis.ca_reseau_annualise),
         "12 mois glissants HT"),
    ])
    pdf.kpi_row([
        ("Point mort treso", _fmt(kpis.point_mort_mensuel),
         f"Marge securite : {marge:+.0f}%"),
        ("EBE cash YTD", f"{kpis.ebe_cash_ytd_pct:.1f}%",
         f"CCR : {kpis.cash_conversion:.2f}"),
        ("BFR reseau", _fmt(kpis.bfr_reseau),
         f"{kpis.nb_alertes} alertes actives"),
    ])

    # Soldes par site (30 lignes)
    pdf.section_title("Soldes par site")
    sol  = pos["soldes_site"].sort_values("solde_fin")
    cols = ["site_nom", "solde_fin", "flux_net", "runway_mois", "rag"]
    hdrs = ["Site", "Solde", "Flux net", "Runway", "Statut"]
    wds  = [55, 30, 30, 25, 25]
    pdf.table_row(hdrs, wds, bold=True, fill=True)
    for i, (_, r) in enumerate(sol.iterrows()):
        rag = r["rag"]
        if rag == "rouge":
            pdf.set_text_color(*_ROUGE)
        elif rag == "orange":
            pdf.set_text_color(*_ORANGE)
        else:
            pdf.set_text_color(*_VERT)
        stat = {"rouge": "Critique", "orange": "Vigilance", "vert": "Normal"}.get(rag, "")
        pdf.table_row(
            [_safe(r["site_nom"][:22]), _fmt(r["solde_fin"]),
             _fmt(r["flux_net"]), f"{r['runway_mois']:.1f} m", stat],
            wds, fill=(i % 2 == 0),
        )
        pdf.set_text_color(*_NOIR)

    # ==========================================================================
    # PAGE 2 : Alertes + BFR ratios
    # ==========================================================================
    pdf.add_page()

    # Alertes critiques
    pdf.section_title("Alertes prioritaires (rouge uniquement)", color=_ROUGE)
    rouges = [a for a in alertes if a.gravite == "rouge"][:20]
    if rouges:
        wds_al = [30, 60, 40, 30]
        pdf.table_row(["Type", "Message", "Site", "Valeur"], wds_al, bold=True, fill=True)
        TYPE_FR = {"tresorerie":"Tresorerie","client":"Client",
                   "stock":"Stock","fournisseur":"Fournisseur"}
        for a in rouges:
            val = f"{a.valeur:,.0f} E" if (a.valeur and abs(a.valeur) > 100) else ""
            pdf.table_row(
                [TYPE_FR.get(a.type, a.type), _safe(a.message, 55),
                 _safe(f"{a.site_id} {a.site_nom[:14]}"), val],
                wds_al,
            )
    else:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_VERT)
        pdf.cell(0, 6, "Aucune alerte critique ce mois.", ln=True)
        pdf.set_text_color(*_NOIR)
    pdf.ln(4)

    # BFR ratios
    pdf.section_title("Ratios BFR - Moyennes ponderees reseau")
    rat = bfr["ratios_reseau"]
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_NOIR)
    bench_map = {
        "DSO (delai clients)":      (rat["dso"], *rat["dso_bench"]),
        "DPO (delai fournisseurs)": (rat["dpo"], *rat["dpo_bench"]),
        "DIO (rotation stocks)":    (rat["dio"], *rat["dio_bench"]),
        "CCC (cycle cash)":         (rat["ccc"], *rat["ccc_bench"]),
    }
    for label, (val, bmin, bmax) in bench_map.items():
        color = _VERT if bmin <= val <= bmax else (_ROUGE if val > bmax else _BLEU)
        statut = "OK" if bmin <= val <= bmax else ("Eleve" if val > bmax else "Bas")
        pdf.set_text_color(*color)
        pdf.cell(70, 5, f"  {label}", border="B")
        pdf.cell(20, 5, f"{val:.1f} j", border="B", align="C")
        pdf.cell(40, 5, f"Bench : {bmin}-{bmax} j", border="B", align="C")
        pdf.cell(25, 5, statut, border="B", align="C")
        pdf.ln()
        pdf.set_text_color(*_NOIR)
    pdf.ln(4)

    # Aging clients
    pdf.section_title("Aging encours clients")
    aging = bfr["aging_consolide"]
    aging_pct = bfr["aging_pct"]
    aging_total = bfr["aging_total"]
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_NOIR)
    for tranche, montant in aging.items():
        pct = aging_pct.get(tranche, 0)
        bar_w = int(pct * 0.8)
        pdf.cell(25, 5, tranche, border="B")
        pdf.cell(35, 5, _fmt(montant), border="B", align="R")
        pdf.cell(15, 5, f"{pct:.1f}%", border="B", align="C")
        pdf.cell(bar_w, 5, "", border=0, fill=True)
        pdf.ln()
        pdf.set_fill_color(255, 255, 255)

    # ==========================================================================
    # PAGE 3 : Previsionnel (si fourni)
    # ==========================================================================
    if scenarios:
        pdf.add_page()
        pdf.section_title("Previsionnel - 3 scenarios")

        df_base = scenarios.get("base")
        df_opt  = scenarios.get("optimiste")
        df_pess = scenarios.get("pessimiste")

        if df_base is not None:
            wds_fc = [28, 30, 30, 30, 35, 32]
            pdf.table_row(
                ["Mois", "Flux base", "Solde base", "Solde opt.", "Solde pess.", "Alerte"],
                wds_fc, bold=True, fill=True,
            )
            for i in range(len(df_base)):
                mois_l = df_base["mois_label"].iloc[i]
                fn     = _fmt(df_base["flux_net"].iloc[i])
                sb     = _fmt(df_base["solde"].iloc[i])
                so     = _fmt(df_opt["solde"].iloc[i])   if df_opt  is not None else "-"
                sp_v   = df_pess["solde"].iloc[i]        if df_pess is not None else 0
                sp     = _fmt(sp_v)
                alerte = ("RUPTURE POSSIBLE" if sp_v < 0 else
                          "Tension" if sp_v < 20_000 else "")
                pdf.set_text_color(*(_ROUGE if alerte else _NOIR))
                pdf.table_row([mois_l, fn, sb, so, sp, alerte],
                              wds_fc, fill=(i % 2 == 0))
                pdf.set_text_color(*_NOIR)

            pdf.ln(6)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(*_GRIS)
            pdf.multi_cell(0, 4,
                "Methode : WLS + saisonnalite N-1 par composante. "
                "IC 80% base sur residus historiques. "
                "Optimiste : +10% encaissements + DPO +7j. "
                "Pessimiste : -8% encaissements + DSO +12j.")

    return bytes(pdf.output())

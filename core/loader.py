# -*- coding: utf-8 -*-
"""
core/loader.py -- FloMind Dashboard Tresorerie
==============================================
Couche de calcul entre les fichiers bruts et les vues Streamlit.

Architecture :
    TresoLoader
    ├── _load()              lecture via TresoDataSource ou Excel direct
    ├── set_mois_courant()   navigation temporelle
    ├── mois_courant_idx     property : index du mois selectionne
    ├── mois_reels_disponibles : list pour le slider
    ├── kpi_global()         KPIs header (incl. point_mort, CCR)
    ├── position()           soldes, runway, RAG par site
    ├── flux()               flux mensuels, waterfall, N vs N-1
    ├── bfr(site_id)         DSO/DPO/aging/stock/fournisseurs, filtrable par site
    ├── alertes(site_id)     alertes consolidees, filtrables par site
    └── score_risque()       score 0-100 par site

Constantes : toutes importees depuis config.settings (source unique).
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import (
    MOIS_COURANT_LABEL, MOIS_COURANT_IDX,
    TVA,
    SEUIL_RUNWAY_CRITIQUE, SEUIL_RUNWAY_VIGILANCE, SEUIL_SOLDE_FAIBLE,
    BENCH,
)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class KpiGlobal:
    """KPIs de la barre d'en-tete."""
    solde_reseau:        float   # EUR
    flux_net_courant:    float   # EUR (mois courant)
    flux_net_ytd:        float   # EUR (annee en cours)
    ca_reseau_annualise: float   # EUR HT, 12m glissants
    ebe_cash_ytd_pct:    float   # % CA
    bfr_reseau:          float   # EUR (encours cli + stock - dettes four.)
    nb_alertes:          int
    nb_sites_negatifs:   int
    nb_sites_critiques:  int     # runway < 1 mois
    point_mort_mensuel:  float   # CA HT/mois minimum pour flux net >= 0
    cash_conversion:     float   # flux net operationnel YTD / EBE cash YTD
    delta_solde_m1:      float   # variation solde vs mois precedent (EUR)
    delta_flux_m1:       float   # variation flux net vs mois precedent (EUR)
    taux_couverture_ct:  float   # Solde bancaire / (dettes four. + mensualites emprunt)


@dataclass
class AlerteItem:
    """Une alerte individuelle."""
    type:       str             # "tresorerie" | "client" | "stock" | "fournisseur"
    gravite:    str             # "rouge" | "orange" | "jaune"
    site_id:    str
    site_nom:   str
    message:    str
    valeur:     Optional[float] = None
    ref_id:     Optional[str]   = None


# =============================================================================
# LOADER PRINCIPAL
# =============================================================================

class TresoLoader:
    """
    Charge et calcule tous les KPIs du dashboard tresorerie.

    Deux modes d'alimentation :
        source   : TresoDataSource (Excel, SQL Sage, API)
        data_dir : chemin Excel direct (retrocompat.)

    Note demo : set_mois_courant() modifie l'objet en place.
    Avec @st.cache_resource (singleton par session) c'est acceptable
    en usage mono-utilisateur. Pour multi-tenant, passer mois_courant
    en parametre a chaque methode.
    """

    def __init__(
        self,
        source=None,                     # TresoDataSource | None
        data_dir: Path | str | None = None,
        mois_courant: str = MOIS_COURANT_LABEL,
    ):
        self._mois_courant = mois_courant
        self._cache: dict  = {}

        if source is not None:
            self._source = source
            # Deriver data_dir depuis ExcelSource si possible
            if data_dir is None and hasattr(source, "_paths"):
                data_dir = Path(list(source._paths.values())[0]).parent
        else:
            self._source = None

        self._dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"

    # -------------------------------------------------------------------------
    # LECTURE CACHEE
    # -------------------------------------------------------------------------

    def _load(self, fname: str) -> pd.DataFrame:
        """Lecture avec cache in-process. Delegue a la source pour les 3 tables principales."""
        if fname not in self._cache:
            if self._source is not None:
                if fname == "treso_flux.xlsx":
                    self._cache[fname] = self._source.load_flux()
                elif fname == "treso_soldes.xlsx":
                    self._cache[fname] = self._source.load_soldes()
                elif fname == "treso_bfr.xlsx":
                    self._cache[fname] = self._source.load_bfr()
                else:
                    # Fichiers complementaires (balance, stock, catalogue) : data_dir
                    self._cache[fname] = pd.read_excel(self._dir / fname)
            else:
                self._cache[fname] = pd.read_excel(self._dir / fname)
        return self._cache[fname]

    @property
    def flux_raw(self)        -> pd.DataFrame: return self._load("treso_flux.xlsx")
    @property
    def soldes_raw(self)      -> pd.DataFrame: return self._load("treso_soldes.xlsx")
    @property
    def bfr_raw(self) -> pd.DataFrame:
        """
        Ratios DSO/DPO/DIO/CCC mensuels theoriques.
        Usage UNIQUE : evolution mensuelle des ratios (evo_ratios).
        Pour le BFR financier, utiliser balance_cli_raw + balance_fou_raw + stock_raw.
        Ecart normal : BFR theorique ~4.6 Me vs BFR reel ~7.3 Me.
        """
        return self._load("treso_bfr.xlsx")
    @property
    def balance_cli_raw(self) -> pd.DataFrame: return self._load("balance_client.xlsx")
    @property
    def balance_fou_raw(self) -> pd.DataFrame: return self._load("balance_fournisseur.xlsx")
    @property
    def stock_raw(self)       -> pd.DataFrame: return self._load("stock_detail.xlsx")
    @property
    def catalogue_raw(self)   -> pd.DataFrame: return self._load("ref_catalogue.xlsx")
    @property
    def budget_raw(self) -> pd.DataFrame:
        """Budget annuel par site / mois / sous-categorie.
        Retourne DataFrame vide si le fichier n'existe pas (mode demo sans budget).
        """
        try:
            return self._load("budget_treso.xlsx")
        except FileNotFoundError:
            return pd.DataFrame()

    # -------------------------------------------------------------------------
    # NAVIGATION TEMPORELLE
    # -------------------------------------------------------------------------

    def set_mois_courant(self, mois: str) -> None:
        """Met a jour le mois courant pour toutes les vues."""
        self._mois_courant = mois

    @property
    def mois_courant_idx(self) -> int:
        """Retourne l'index (periode_idx) du mois courant selectionne."""
        mask = self.soldes_raw["mois_label"] == self._mois_courant
        idxs = self.soldes_raw[mask]["periode_idx"]
        return int(idxs.iloc[0]) if not idxs.empty else MOIS_COURANT_IDX

    @property
    def mois_reels_disponibles(self) -> list[str]:
        """Liste triee des mois reels pour le slider de navigation."""
        df = (self.soldes_raw[self.soldes_raw["est_reel"] == True]
              .drop_duplicates("mois_label")
              .sort_values("periode_idx"))
        return df["mois_label"].tolist()

    # -------------------------------------------------------------------------
    # HELPERS INTERNES
    # -------------------------------------------------------------------------

    def _soldes_courant(self) -> pd.DataFrame:
        return self.soldes_raw[self.soldes_raw["mois_label"] == self._mois_courant].copy()

    def _flux_reel(self) -> pd.DataFrame:
        return self.flux_raw[self.flux_raw["est_reel"] == True].copy()

    def _fx_12m_reels(self) -> pd.DataFrame:
        """12 derniers mois de flux reels avant le mois courant (inclus)."""
        fx_reel = self._flux_reel()
        m_max   = self.mois_courant_idx
        m_min   = max(0, m_max - 11)
        return fx_reel[fx_reel["periode_idx"].between(m_min, m_max)]

    # -------------------------------------------------------------------------
    # NOUVEAUX KPIs : POINT MORT TRESORERIE + CASH CONVERSION RATIO
    # -------------------------------------------------------------------------

    def _compute_point_mort(self, fx_12m: pd.DataFrame) -> float:
        """
        Point mort de tresorerie : CA HT mensuel minimum pour flux net >= 0.

        Modele :
            Charges fixes mensuelles = (loyers + remb. emprunt + frais fi)
                                     + 80% masse salariale
            Taux de marge sur couts variables (TTC) = (enc - pmt_four) / enc
            Point mort CA HT = charges_fixes_mensuelles / taux_mcv / (1 + TVA)

        Hypothese : 80% de la masse salariale est incompressible a court terme.
        Limite : ne modelise pas les economies d'echelle ni les couts semi-variables.
        """
        FIXES = [
            "Loyers et charges locatives",
            "Remboursement emprunt",
            "Frais financiers",
        ]
        ch_fixes_ann = abs(fx_12m[fx_12m["sous_categorie"].isin(FIXES)]["montant"].sum())
        sal_ann      = abs(fx_12m[fx_12m["sous_categorie"] == "Masse salariale"]["montant"].sum())
        ch_fixes_ann += sal_ann * 0.80
        ch_fixes_mois = ch_fixes_ann / 12

        enc_ann = abs(fx_12m[fx_12m["sous_categorie"] == "Encaissements clients"]["montant"].sum())
        pmt_ann = abs(fx_12m[fx_12m["sous_categorie"] == "Paiements fournisseurs"]["montant"].sum())

        if enc_ann <= 0:
            return 0.0
        taux_mcv = (enc_ann - pmt_ann) / enc_ann   # marge sur couts variables TTC
        if taux_mcv <= 0:
            return float("inf")
        # Point mort en CA TTC mensuel converti en HT
        return (ch_fixes_mois / taux_mcv) / (1 + TVA)

    def _compute_ccr(self, fx_ytd: pd.DataFrame) -> float:
        """
        Cash Conversion Ratio = flux net operationnel YTD / EBE cash YTD.

        Numerateur : flux operationnel = encaissements + paiements four.
                     + masse salariale + charges exploitation + loyers.
        Denominateur (EBE cash) : meme perimetre, valeur absolue.

        Convention : hors CAPEX, remboursement emprunt, frais financiers,
        impots differees — pour isoler la performance operationnelle.
        Valeur saine : 0.5-0.8 selon secteur negoce.
        Un CCR > 1 signale un BFR qui se contracte (encaissements acceleres).
        """
        EXPLOIT = [
            "Encaissements clients", "Paiements fournisseurs",
            "Masse salariale", "Charges d'exploitation",
            "Loyers et charges locatives",
        ]
        # Flux operationnel seul (hors financement / investissement / fiscal)
        fx_exploit = fx_ytd[fx_ytd["sous_categorie"].isin(EXPLOIT)]["montant"]
        ebe_cash    = fx_exploit.sum()            # positif si profitable
        flux_oper   = fx_exploit.sum()            # identique ici : le CCR mesure
        # Note : si on voulait un CCR "pur", flux_oper exclurait aussi les loyers
        # (qui peuvent etre des charges fixes). On reste sur la definition standard.
        if abs(ebe_cash) < 1:
            return 0.0
        return round(flux_oper / abs(ebe_cash), 3)

    def _compute_couverture_ct(self, solde_reseau: float, fx_12m: pd.DataFrame) -> float:
        """
        Taux de couverture des dettes a court terme.

        Ratio = Solde bancaire reseau / (Dettes fournisseurs echues + Mensualites emprunt mois courant)

        Interpretation :
            > 1.5  : confortable — la tresorerie couvre largement les echeances
            1.0-1.5: acceptable
            < 1.0  : alerte — risque de defaut a court terme
            < 0.5  : critique

        Hypothese : la mensualite emprunt = remb. emprunt 12m / 12.
        Les dettes fournisseurs echues = encours total balance fournisseurs.
        """
        dettes_four   = self.balance_fou_raw["encours_total"].sum()
        remb_ann      = abs(fx_12m[fx_12m["sous_categorie"] == "Remboursement emprunt"]["montant"].sum())
        mensualite    = remb_ann / 12
        obligations_ct = dettes_four + mensualite
        if obligations_ct < 1:
            return 0.0
        return round(solde_reseau / obligations_ct, 2)

    # -------------------------------------------------------------------------
    # KPI GLOBAL
    # -------------------------------------------------------------------------

    def kpi_global(self) -> KpiGlobal:
        """Calcule les KPIs de la barre d'en-tete. Appele une fois par rerun."""
        sol     = self._soldes_courant()
        fx      = self.flux_raw
        cur_idx = self.mois_courant_idx

        # Solde reseau consolide + flux net mois courant
        solde_reseau = sol["solde_fin"].sum()
        flux_courant = sol["flux_net"].sum()

        # Flux net YTD (annee du mois courant)
        an_courant = int(self._mois_courant.split()[-1])
        fx_ytd_df  = fx[(fx["annee"] == an_courant) & (fx["est_reel"] == True)]
        flux_ytd   = fx_ytd_df["montant"].sum()

        # CA annualise (12 derniers mois reels)
        fx_12m = self._fx_12m_reels()
        ca_12m = abs(
            fx_12m[fx_12m["sous_categorie"] == "Encaissements clients"]["montant"].sum()
            / (1 + TVA)
        )
        n_mois       = min(cur_idx - max(0, cur_idx - 11) + 1, 12)
        ca_annualise = ca_12m * (12 / n_mois) if n_mois > 0 else 0.0

        # EBE cash YTD / CA YTD
        ca_ytd = abs(
            fx_ytd_df[fx_ytd_df["sous_categorie"] == "Encaissements clients"]["montant"].sum()
            / (1 + TVA)
        )
        ebe_pct = (flux_ytd / ca_ytd * 100) if ca_ytd > 0 else 0.0

        # BFR reseau (encours cli + stock - dettes four.)
        enc_cli = self.balance_cli_raw["encours_total"].sum()
        dettes  = self.balance_fou_raw["encours_total"].sum()
        stock_v = self.stock_raw["valeur_stock_ht"].sum()
        bfr     = enc_cli + stock_v - dettes

        # Alertes
        alertes_list = self.alertes()
        nb_alertes   = len(alertes_list)
        nb_negatifs  = int((sol["solde_fin"] < 0).sum())
        nb_critiques = int((sol["runway_mois"] < SEUIL_RUNWAY_CRITIQUE).sum())

        # Nouveaux KPIs
        point_mort = self._compute_point_mort(fx_12m)
        ccr        = self._compute_ccr(fx_ytd_df)

        # Delta vs mois precedent
        mois_list = self.mois_reels_disponibles
        try:
            cur_pos  = mois_list.index(self._mois_courant)
            mois_m1  = mois_list[cur_pos - 1] if cur_pos > 0 else None
        except ValueError:
            mois_m1 = None

        if mois_m1:
            sol_m1        = self.soldes_raw[self.soldes_raw["mois_label"] == mois_m1]["solde_fin"].sum()
            delta_solde   = solde_reseau - sol_m1
            sol_m1_df     = self.soldes_raw[self.soldes_raw["mois_label"] == mois_m1]
            delta_flux    = flux_courant - sol_m1_df["flux_net"].sum()
        else:
            delta_solde = 0.0
            delta_flux  = 0.0

        couverture_ct = self._compute_couverture_ct(solde_reseau, fx_12m)

        return KpiGlobal(
            solde_reseau        = solde_reseau,
            flux_net_courant    = flux_courant,
            flux_net_ytd        = flux_ytd,
            ca_reseau_annualise = ca_annualise,
            ebe_cash_ytd_pct    = ebe_pct,
            bfr_reseau          = bfr,
            nb_alertes          = nb_alertes,
            nb_sites_negatifs   = int(nb_negatifs),
            nb_sites_critiques  = int(nb_critiques),
            point_mort_mensuel  = point_mort,
            cash_conversion     = ccr,
            delta_solde_m1      = delta_solde,
            delta_flux_m1       = delta_flux,
            taux_couverture_ct  = couverture_ct,
        )

    # -------------------------------------------------------------------------
    # VUE POSITION
    # -------------------------------------------------------------------------

    def position(self) -> dict:
        sol_cur = self._soldes_courant()
        cur_idx = self.mois_courant_idx

        def rag(row) -> str:
            if row["solde_fin"] < 0:                               return "rouge"
            if row["runway_mois"] < SEUIL_RUNWAY_CRITIQUE:         return "rouge"
            if row["solde_fin"]  < SEUIL_SOLDE_FAIBLE:             return "orange"
            if row["runway_mois"] < SEUIL_RUNWAY_VIGILANCE:        return "orange"
            return "vert"

        sol_cur = sol_cur.copy()
        sol_cur["rag"] = sol_cur.apply(rag, axis=1)
        sol_cur = sol_cur.sort_values("solde_fin")

        evo = (self.soldes_raw
               .groupby(["periode_idx", "mois_label", "annee", "mois_num"])
               .agg(
                   solde_reseau = ("solde_fin", "sum"),
                   flux_net     = ("flux_net",  "sum"),
                   nb_negatifs  = ("alerte_negatif", "sum"),
               )
               .reset_index()
               .sort_values("periode_idx"))
        evo["est_reel"] = evo["periode_idx"] <= cur_idx

        # Incidents dynamiques : top alertes rouges de tresorerie
        incidents = [a for a in self.alertes()
                     if a.gravite == "rouge" and a.type == "tresorerie"][:4]

        return {
            "soldes_site":  sol_cur,
            "evolution":    evo,
            "mois_courant": self._mois_courant,
            "incidents":    incidents,
        }

    # -------------------------------------------------------------------------
    # VUE FLUX
    # -------------------------------------------------------------------------

    def flux(self, site_id: str | None = None) -> dict:
        fx      = self.flux_raw.copy()
        cur_idx = self.mois_courant_idx
        if site_id:
            fx = fx[fx["site_id"] == site_id]

        mensuel = (fx.groupby(["periode_idx", "mois_label", "annee", "mois_num"])
                   .agg(flux_net=("montant", "sum"))
                   .reset_index().sort_values("periode_idx"))
        mensuel["est_reel"] = mensuel["periode_idx"] <= cur_idx
        mensuel["cumul"]    = mensuel["flux_net"].cumsum()

        par_cat = (fx.groupby(["mois_label", "periode_idx", "categorie"])
                   ["montant"].sum().reset_index().sort_values("periode_idx"))

        fx_cur = fx[fx["mois_label"] == self._mois_courant]
        waterfall = (fx_cur.groupby("sous_categorie")["montant"]
                     .sum().reset_index().sort_values("montant"))
        waterfall["couleur"] = waterfall["montant"].apply(
            lambda x: "positif" if x >= 0 else "negatif")

        # Comparaison N vs N-1 : annees derivees du mois courant (pas hardcodees)
        an_courant = int(self._mois_courant.split()[-1])
        an_n1      = an_courant - 1
        n_vs_n1 = (fx[fx["annee"].isin([an_n1, an_courant])]
                   .groupby(["annee", "categorie"])["montant"]
                   .sum().unstack("annee").fillna(0).reset_index())
        if an_n1 in n_vs_n1.columns and an_courant in n_vs_n1.columns:
            n_vs_n1["evolution_pct"] = (
                (n_vs_n1[an_courant] - n_vs_n1[an_n1]) / n_vs_n1[an_n1].abs() * 100
            ).round(1)
        # Renommer pour que la vue puisse acceder aux colonnes par annee symbolique
        n_vs_n1 = n_vs_n1.rename(columns={an_n1: "an_n1", an_courant: "an_courant"})
        n_vs_n1["an_n1_label"]      = str(an_n1)
        n_vs_n1["an_courant_label"] = str(an_courant)

        top_sites = None
        if site_id is None:
            top_sites = (fx[fx["mois_label"] == self._mois_courant]
                         .groupby(["site_id", "site_nom", "profil"])["montant"]
                         .sum().reset_index().sort_values("montant", ascending=False))

        return {
            "mensuel":           mensuel,
            "par_categorie":     par_cat,
            "waterfall_courant": waterfall,
            "n_vs_n1":           n_vs_n1,
            "top_contributeurs": top_sites,
        }

    # -------------------------------------------------------------------------
    # VUE BFR (filtre site optionnel)
    # -------------------------------------------------------------------------

    def bfr(self, site_id: str | None = None) -> dict:
        """
        Tout ce qu'il faut pour la vue BFR.

        Parametres :
            site_id : None = reseau consolide | "S01" = site specifique
        """
        cli   = self.balance_cli_raw.copy()
        fou   = self.balance_fou_raw.copy()
        sto   = self.stock_raw.copy()
        bfr_r = self.bfr_raw.copy()

        if site_id:
            cli   = cli[cli["site_id"]     == site_id]
            fou   = fou[fou["site_id"]     == site_id]
            sto   = sto[sto["site_id"]     == site_id]
            bfr_r = bfr_r[bfr_r["site_id"] == site_id]

        # ── Ratios DSO/DPO/DIO/CCC ponderes ──────────────────────────────────
        bfr_cur  = bfr_r[bfr_r["mois_label"] == self._mois_courant]
        poids_ca = cli.groupby("site_id")["ca_annuel_client"].sum()
        bfr_cur  = bfr_cur.merge(poids_ca.rename("poids"), on="site_id", how="left")
        if bfr_cur["poids"].notna().any():
            bfr_cur["poids"] = bfr_cur["poids"].fillna(bfr_cur["poids"].mean())
        else:
            bfr_cur["poids"] = 1.0

        def wmean(col: str) -> float:
            w = bfr_cur["poids"].values
            return float(np.average(bfr_cur[col], weights=w)) if w.sum() > 0 and len(bfr_cur) else 0.0

        ratios = {
            "dso": round(wmean("dso_jours"), 1),
            "dpo": round(wmean("dpo_jours"), 1),
            "dio": round(wmean("dio_jours"), 1),
            "ccc": round(wmean("ccc_jours"), 1),
            "dso_bench": BENCH["dso"],
            "dpo_bench": BENCH["dpo"],
            "dio_bench": BENCH["dio"],
            "ccc_bench": BENCH["ccc"],
        }

        # ── Evolution mensuelle ───────────────────────────────────────────────
        cur_idx    = self.mois_courant_idx
        evo_ratios = (bfr_r
                      .groupby(["periode_idx", "mois_label"])
                      .agg(dso=("dso_jours","mean"), dpo=("dpo_jours","mean"),
                           dio=("dio_jours","mean"), ccc=("ccc_jours","mean"))
                      .reset_index().sort_values("periode_idx"))
        evo_ratios["est_reel"] = evo_ratios["periode_idx"] <= cur_idx

        # ── Aging clients ─────────────────────────────────────────────────────
        aging = {
            "Non echu":  cli["dont_non_echu"].sum(),
            "0-30j":     cli["dont_0_30j"].sum(),
            "30-60j":    cli["dont_30_60j"].sum(),
            "60-90j":    cli["dont_60_90j"].sum(),
            "+90j":      cli["dont_plus_90j"].sum(),
        }
        aging_total = sum(aging.values())
        aging_pct   = {k: round(v / aging_total * 100, 1) if aging_total > 0 else 0
                       for k, v in aging.items()}

        # ── Top clients a risque ──────────────────────────────────────────────
        cli_risque = cli[cli["statut_risque"].isin(["Contentieux","Surveillance"])].copy()
        cli_risque["retard_total"] = (cli_risque["dont_30_60j"] +
                                      cli_risque["dont_60_90j"] +
                                      cli_risque["dont_plus_90j"])
        cli_risque = cli_risque.sort_values("retard_total", ascending=False)

        # ── Stock ABC ─────────────────────────────────────────────────────────
        stock_abc = (sto.groupby("categorie_abc")
                     .agg(
                         valeur_stock = ("valeur_stock_ht",   "sum"),
                         valeur_dorm  = ("valeur_dormante",   "sum"),
                         nb_ruptures  = ("alerte_rupture",    "sum"),
                         nb_surstk    = ("alerte_surstockage","sum"),
                         dio_moyen    = ("dio_reel_jours",    "mean"),
                     ).reset_index())
        stock_abc["pct_valeur"] = (
            stock_abc["valeur_stock"] / stock_abc["valeur_stock"].sum() * 100
        ).round(1)
        stock_abc["taux_dormant_pct"] = (
            stock_abc["valeur_dorm"] / stock_abc["valeur_stock"] * 100
        ).round(1)

        # ── References en alerte ──────────────────────────────────────────────
        stock_alertes = sto[
            sto["statut_stock"].isin(["Rupture","Sous mini","Surstockage"])
        ][[
            "ref_id","designation","categorie_abc","site_id","site_nom",
            "qte_stock","stock_mini","valeur_stock_ht","statut_stock",
            "dernier_mvt_jours","couverture_mois",
        ]].copy()

        # ── Fournisseurs en retard ────────────────────────────────────────────
        four_retard = fou[fou["alerte_depassement"] == True][[
            "site_id","site_nom","profil","fournisseur_nom","type_fournisseur",
            "encours_total","dont_30_60j_et_plus","conditions_paiement",
        ]].copy()

        # ── BFR par site (toujours sur le reseau entier pour la carte) ────────
        enc_site = self.balance_cli_raw.groupby("site_id")["encours_total"].sum().rename("creances")
        fou_site = self.balance_fou_raw.groupby("site_id")["encours_total"].sum().rename("dettes")
        sto_site = self.stock_raw.groupby("site_id")["valeur_stock_ht"].sum().rename("stocks")
        bfr_site = pd.concat([enc_site, fou_site, sto_site], axis=1).fillna(0)
        bfr_site["bfr"] = bfr_site["creances"] + bfr_site["stocks"] - bfr_site["dettes"]
        bfr_site = bfr_site.reset_index()
        meta     = (self.soldes_raw[self.soldes_raw["mois_label"] == self._mois_courant]
                    [["site_id","site_nom","profil"]])
        bfr_site = bfr_site.merge(meta, on="site_id", how="left")

        return {
            "ratios_reseau":   ratios,
            "evo_ratios":      evo_ratios,
            "aging_consolide": aging,
            "aging_pct":       aging_pct,
            "aging_total":     aging_total,
            "top_risque_cli":  cli_risque,
            "stock_abc":       stock_abc,
            "stock_alertes":   stock_alertes,
            "four_retard":     four_retard,
            "bfr_par_site":    bfr_site,
        }

    # -------------------------------------------------------------------------
    # VUE ALERTES (filtre site optionnel)
    # -------------------------------------------------------------------------

    def alertes(self, site_id: str | None = None) -> list[AlerteItem]:
        """
        Consolide toutes les alertes, triees par gravite.
        site_id=None : toutes / "S01" : site specifique
        """
        items: list[AlerteItem] = []

        sol = self.soldes_raw[self.soldes_raw["mois_label"] == self._mois_courant]
        if site_id:
            sol = sol[sol["site_id"] == site_id]

        for _, row in sol.iterrows():
            if row["solde_fin"] < 0:
                items.append(AlerteItem(
                    type="tresorerie", gravite="rouge",
                    site_id=row["site_id"], site_nom=row["site_nom"],
                    message=f"Solde negatif : {row['solde_fin']:,.0f} EUR",
                    valeur=row["solde_fin"],
                ))
            elif row["runway_mois"] < SEUIL_RUNWAY_CRITIQUE:
                items.append(AlerteItem(
                    type="tresorerie", gravite="rouge",
                    site_id=row["site_id"], site_nom=row["site_nom"],
                    message=f"Runway critique : {row['runway_mois']:.1f} mois",
                    valeur=row["runway_mois"],
                ))
            elif row["runway_mois"] < SEUIL_RUNWAY_VIGILANCE or row["alerte_faible"]:
                items.append(AlerteItem(
                    type="tresorerie", gravite="orange",
                    site_id=row["site_id"], site_nom=row["site_nom"],
                    message=f"Tresorerie tendue : runway {row['runway_mois']:.1f} mois",
                    valeur=row["runway_mois"],
                ))

        cli = self.balance_cli_raw.copy()
        if site_id:
            cli = cli[cli["site_id"] == site_id]

        for _, row in cli[cli["statut_risque"] == "Contentieux"].iterrows():
            items.append(AlerteItem(
                type="client", gravite="rouge",
                site_id=row["site_id"], site_nom=row["site_nom"],
                message=(f"Contentieux : {row['client_nom']} — "
                         f"+90j : {row['dont_plus_90j']:,.0f} EUR"),
                valeur=row["dont_plus_90j"],
            ))
        for _, row in cli[cli["taux_utilisation"] > 100].iterrows():
            items.append(AlerteItem(
                type="client", gravite="rouge",
                site_id=row["site_id"], site_nom=row["site_nom"],
                message=(f"Limite credit depassee : {row['client_nom']} "
                         f"({row['taux_utilisation']:.0f}%)"),
                valeur=row["taux_utilisation"],
            ))

        cli_surv = cli[cli["statut_risque"] == "Surveillance"].copy()
        cli_surv["retard_sig"] = (cli_surv["dont_30_60j"] +
                                  cli_surv["dont_60_90j"] +
                                  cli_surv["dont_plus_90j"])
        cli_surv = cli_surv[
            (cli_surv["retard_sig"] > 10_000) | (cli_surv["dont_plus_90j"] > 2_000)
        ]
        for _, row in cli_surv.iterrows():
            retard = row["dont_30_60j"] + row["dont_60_90j"] + row["dont_plus_90j"]
            items.append(AlerteItem(
                type="client", gravite="orange",
                site_id=row["site_id"], site_nom=row["site_nom"],
                message=(f"Surveillance : {row['client_nom'][:35]} — "
                         f"{retard:,.0f} EUR en retard"),
                valeur=retard,
            ))

        sto = self.stock_raw.copy()
        if site_id:
            sto = sto[sto["site_id"] == site_id]

        for _, row in sto[sto["statut_stock"] == "Rupture"].iterrows():
            items.append(AlerteItem(
                type="stock", gravite="rouge",
                site_id=row["site_id"], site_nom=row["site_nom"],
                ref_id=row["ref_id"],
                message=(f"Rupture : {row['designation'][:40]} "
                         f"(commande {row['qte_en_commande']} uts en cours)"),
                valeur=0,
            ))
        for _, row in sto[sto["alerte_dormant_180"] == True].iterrows():
            if row["valeur_dormante"] > 3_000:
                items.append(AlerteItem(
                    type="stock", gravite="orange",
                    site_id=row["site_id"], site_nom=row["site_nom"],
                    ref_id=row["ref_id"],
                    message=(f"Dormant +180j : {row['designation'][:35]} — "
                             f"{row['valeur_dormante']:,.0f} EUR"),
                    valeur=row["valeur_dormante"],
                ))
        for _, row in sto[sto["statut_stock"] == "Surstockage"].iterrows():
            if row["valeur_stock_ht"] > 10_000:
                items.append(AlerteItem(
                    type="stock", gravite="orange",
                    site_id=row["site_id"], site_nom=row["site_nom"],
                    ref_id=row["ref_id"],
                    message=(f"Surstockage : {row['designation'][:35]} — "
                             f"{row['couverture_mois']:.0f} mois couverture"),
                    valeur=row["couverture_mois"],
                ))

        fou = self.balance_fou_raw.copy()
        if site_id:
            fou = fou[fou["site_id"] == site_id]

        for _, row in fou[fou["alerte_depassement"] == True].iterrows():
            gravite = "rouge" if row["profil"] in ["tension_bfr","nouveau"] else "orange"
            items.append(AlerteItem(
                type="fournisseur", gravite=gravite,
                site_id=row["site_id"], site_nom=row["site_nom"],
                message=(f"Retard fournisseur : {row['fournisseur_nom'][:35]} — "
                         f"{row['dont_30_60j_et_plus']:,.0f} EUR en retard"),
                valeur=row["dont_30_60j_et_plus"],
            ))

        ordre = {"rouge": 0, "orange": 1, "jaune": 2}
        items.sort(key=lambda x: (ordre.get(x.gravite, 9), -(x.valeur or 0)))
        return items

    # -------------------------------------------------------------------------
    # SCORE RISQUE (toujours sur le reseau entier)
    # -------------------------------------------------------------------------

    def score_risque(self) -> pd.DataFrame:
        alertes = self.alertes()
        scores: dict[str, dict] = {}

        for a in alertes:
            if a.site_id not in scores:
                scores[a.site_id] = {"rouge": 0, "orange": 0, "site_nom": a.site_nom}
            scores[a.site_id][a.gravite] = scores[a.site_id].get(a.gravite, 0) + 1

        rows = []
        for sid, s in scores.items():
            n_rouge  = s.get("rouge",  0)
            n_orange = s.get("orange", 0)
            pts_rouge  = int(20 * math.log1p(n_rouge)  / math.log1p(1)) if n_rouge  else 0
            pts_orange = int(5  * math.log1p(n_orange) / math.log1p(1)) if n_orange else 0
            score = min(pts_rouge + pts_orange, 100)
            rows.append({"site_id": sid, "site_nom": s["site_nom"],
                         "nb_rouge": n_rouge, "nb_orange": n_orange,
                         "score_risque": score})

        df = (pd.DataFrame(rows).sort_values("score_risque", ascending=False)
              if rows else pd.DataFrame(columns=["site_id","site_nom","nb_rouge","nb_orange","score_risque"]))

        tous_sites = self.soldes_raw[["site_id","site_nom"]].drop_duplicates()
        df = tous_sites.merge(df, on=["site_id","site_nom"], how="left").fillna(0)
        df["score_risque"] = df["score_risque"].astype(int)
        return df.sort_values("score_risque", ascending=False).reset_index(drop=True)


    def budget_vs_reel(self, annee: int | None = None) -> dict:
        """
        Comparaison budget vs realise.

        Parametres :
            annee : None = annee du mois courant | 2025 = annee specifique

        Retourne :
            taux_realisation_ca : % CA realise / CA budget YTD
            ecart_flux_ytd      : flux net reel - flux net budget YTD
            par_sous_categorie  : DataFrame reel | budget | ecart | ecart_pct | favorable
            par_mois            : DataFrame flux_reel | flux_budget par mois (annee courante)
            annee               : annee analysee
        """
        budget = self.budget_raw
        if budget.empty:
            return {}

        an = annee or int(self._mois_courant.split()[-1])

        # Filtrer sur l'annee courante, jusqu'au mois courant
        cur_idx  = self.mois_courant_idx
        fx_ytd   = self.flux_raw[
            (self.flux_raw["annee"] == an) &
            (self.flux_raw["est_reel"] == True) &
            (self.flux_raw["periode_idx"] <= cur_idx)
        ]
        bdg_ytd  = budget[
            (budget["annee"] == an) &
            (budget["periode_idx"] <= cur_idx)
        ]

        # ── Par sous-categorie ────────────────────────────────────────────────
        reel_cat = (fx_ytd.groupby("sous_categorie")["montant"]
                    .sum().rename("reel").reset_index())
        bdg_cat  = (bdg_ytd.groupby("sous_categorie")["montant_budget"]
                    .sum().rename("budget").reset_index())
        cat = reel_cat.merge(bdg_cat, on="sous_categorie", how="outer").fillna(0)
        cat["ecart"]      = cat["reel"] - cat["budget"]
        cat["ecart_pct"]  = (cat["ecart"] / cat["budget"].abs() * 100).round(1)
        cat["ecart_pct"]  = cat["ecart_pct"].replace([float("inf"), float("-inf")], 0)
        # Favorable = ecart positif (plus encaisse ou moins depense que prevu)
        cat["favorable"]  = cat["ecart"] >= 0
        # Trier par ecart absolu descendant
        cat = cat.sort_values("ecart", key=abs, ascending=False)

        # Ajouter la categorie de flux pour le tri/couleur
        cat_map = (self.flux_raw[["sous_categorie","categorie"]]
                   .drop_duplicates().set_index("sous_categorie")["categorie"])
        cat["categorie"] = cat["sous_categorie"].map(cat_map)

        # ── Par mois (annee courante) ─────────────────────────────────────────
        reel_m = (fx_ytd.groupby(["periode_idx","mois_label"])["montant"]
                  .sum().rename("flux_reel").reset_index())
        bdg_m  = (bdg_ytd.groupby(["periode_idx","mois_label"])["montant_budget"]
                  .sum().rename("flux_budget").reset_index())
        par_mois = reel_m.merge(bdg_m, on=["periode_idx","mois_label"], how="outer").fillna(0)
        par_mois = par_mois.sort_values("periode_idx")
        par_mois["ecart"] = par_mois["flux_reel"] - par_mois["flux_budget"]

        # ── KPIs synthetiques ─────────────────────────────────────────────────
        ca_reel = fx_ytd[fx_ytd["sous_categorie"] == "Encaissements clients"]["montant"].sum()
        ca_bdg  = bdg_ytd[bdg_ytd["sous_categorie"] == "Encaissements clients"]["montant_budget"].sum()
        taux_ca = (ca_reel / ca_bdg * 100) if ca_bdg > 0 else 0.0

        ecart_flux = cat["ecart"].sum()

        return {
            "taux_realisation_ca": round(taux_ca, 1),
            "ecart_flux_ytd":      ecart_flux,
            "ca_reel_ytd":         ca_reel,
            "ca_budget_ytd":       ca_bdg,
            "par_sous_categorie":  cat,
            "par_mois":            par_mois,
            "annee":               an,
        }

    def concentration_clients(self, site_id: str | None = None) -> dict:
        """
        Analyse de concentration du portefeuille clients.

        Retourne :
            par_site : DataFrame site_id | site_nom | top1_pct | top3_pct | top10_pct
                       | herfindahl | nb_clients | ca_total
            top_clients : DataFrame des N plus gros clients (optionnel, filtrable par site)
            reseau : dict top1_pct / top3_pct / top10_pct consolides

        Indicateurs :
            top3_pct > 50%  : dependance forte — alerte orange
            top1_pct > 30%  : client systemique — alerte rouge
            herfindahl > 0.18 : marche concentre (seuil EU antitrust)

        Hypothese : ca_annuel_client utilisé comme proxy de l'encours (disponible balance_client).
        Si colonne absente : fallback sur encours_total.
        """
        bal = self.balance_cli_raw.copy()
        if site_id:
            bal = bal[bal["site_id"] == site_id]

        # Choisir la colonne de CA client (ordre de preference)
        ca_col = ("ca_annuel_client" if "ca_annuel_client" in bal.columns
                  else "encours_total")

        bal = bal[bal[ca_col] > 0].copy()

        def _concentration(group: pd.DataFrame) -> pd.Series:
            ca_sort  = group[ca_col].sort_values(ascending=False).values
            ca_total = ca_sort.sum()
            if ca_total <= 0:
                return pd.Series({"top1_pct": 0, "top3_pct": 0, "top10_pct": 0,
                                  "herfindahl": 0, "nb_clients": 0, "ca_total": 0})
            shares    = ca_sort / ca_total
            hhi       = float((shares ** 2).sum())  # Herfindahl-Hirschman Index
            top1_pct  = float(shares[0] * 100)      if len(shares) >= 1  else 0.0
            top3_pct  = float(shares[:3].sum() * 100) if len(shares) >= 1 else 0.0
            top10_pct = float(shares[:10].sum() * 100) if len(shares) >= 1 else 0.0
            return pd.Series({
                "top1_pct":   round(top1_pct,  1),
                "top3_pct":   round(top3_pct,  1),
                "top10_pct":  round(top10_pct, 1),
                "herfindahl": round(hhi, 3),
                "nb_clients": len(shares),
                "ca_total":   round(ca_total, 0),
            })

        par_site = (bal.groupby(["site_id", "site_nom"])
                    .apply(_concentration, include_groups=False)
                    .reset_index())

        # Top clients individuels (pour le tableau detaille)
        top_clients = (bal.sort_values(ca_col, ascending=False)
                       [["site_id", "site_nom", "client_nom", "secteur",
                         ca_col, "encours_total"]]
                       .rename(columns={ca_col: "ca_annuel", "encours_total": "encours"})
                       .head(30))

        # Consolidé réseau
        ca_total_reseau = bal[ca_col].sum()
        if ca_total_reseau > 0:
            top_n = bal.nlargest(1,  ca_col)[ca_col].sum()
            top3  = bal.nlargest(3,  ca_col)[ca_col].sum()
            top10 = bal.nlargest(10, ca_col)[ca_col].sum()
            reseau = {
                "top1_pct":  round(top_n  / ca_total_reseau * 100, 1),
                "top3_pct":  round(top3   / ca_total_reseau * 100, 1),
                "top10_pct": round(top10  / ca_total_reseau * 100, 1),
            }
        else:
            reseau = {"top1_pct": 0, "top3_pct": 0, "top10_pct": 0}

        return {
            "par_site":    par_site,
            "top_clients": top_clients,
            "reseau":      reseau,
            "ca_col":      ca_col,
        }

    def narrative(self, vue: str) -> dict:
        """
        Génère un résumé narratif contextuel (2-3 phrases) pour chaque vue.

        Retourne :
            texte  : str — résumé en langage naturel
            niveau : "info" | "warning" | "error" — pour st.info / st.warning / st.error
            icone  : str emoji pour le contexte visuel

        Principe : insight first — le DAF lit le résumé, puis plonge dans les détails.
        Hypothese : appelé apres set_mois_courant(), données fraîches.
        """
        from components.formatters import fmt_eur

        kpis  = self.kpi_global()
        mois  = self._mois_courant
        sol   = kpis.solde_reseau
        flux  = kpis.flux_net_courant
        d_sol = kpis.delta_solde_m1
        cct   = kpis.taux_couverture_ct
        ebe   = kpis.ebe_cash_ytd_pct
        pm    = kpis.point_mort_mensuel
        ca_m  = kpis.ca_reseau_annualise / 12 if kpis.ca_reseau_annualise > 0 else 0

        # ── Helpers ──────────────────────────────────────────────────────────
        def _sign(v): return "en hausse" if v >= 0 else "en baisse"
        def _abs_eur(v): return fmt_eur(abs(v))

        if vue == "Tour de controle":
            statut = ("critique" if kpis.nb_sites_critiques > 0
                      else "sous surveillance" if kpis.nb_sites_negatifs > 0
                      else "satisfaisante")
            alerte = (f" **{kpis.nb_sites_critiques} site(s) en rupture**,"
                      if kpis.nb_sites_critiques > 0 else "")
            flux_txt = (f"flux net {_sign(flux)} à {fmt_eur(flux, sign=True)}"
                        if flux != 0 else "flux net stable")
            texte = (
                f"**{mois}** — Solde réseau : **{fmt_eur(sol)}** "
                f"({_sign(d_sol)} de {_abs_eur(d_sol)} vs M-1). "
                f"Situation de trésorerie **{statut}** :{alerte} "
                f"{kpis.nb_sites_negatifs} site(s) négatif(s), {kpis.nb_alertes} alerte(s) active(s). "
                f"Couverture CT : **{cct:.2f}x** — {flux_txt}."
            )
            niveau = ("error" if kpis.nb_sites_critiques > 0
                      else "warning" if kpis.nb_sites_negatifs > 0
                      else "info")
            icone  = ""

        elif vue == "Flux de tresorerie":
            marge_pm = ((ca_m - pm) / pm * 100) if pm > 0 else 0
            texte = (
                f"**{mois}** — Flux net mensuel : **{fmt_eur(flux, sign=True)}** "
                f"({_sign(d_sol)} de {_abs_eur(kpis.delta_flux_m1)} vs M-1). "
                f"EBE cash YTD : **{ebe:.1f}%** du CA "
                f"({'au-dessus' if ebe >= 3 else 'sous'} benchmark 3-7%). "
                f"Marge sur point mort : **{marge_pm:+.0f}%** — "
                f"{'confortable' if marge_pm > 20 else 'à surveiller' if marge_pm > 0 else 'sous le seuil critique'}."
            )
            niveau = "error" if marge_pm < 0 else "warning" if marge_pm < 10 else "info"
            icone  = ""

        elif vue == "BFR":
            bfr = kpis.bfr_reseau
            bfr_j = (bfr / (kpis.ca_reseau_annualise / 360)) if kpis.ca_reseau_annualise > 0 else 0
            texte = (
                f"**{mois}** — BFR réseau : **{fmt_eur(bfr)}** "
                f"({bfr_j:.0f}j de CA). "
                f"Couverture CT : **{cct:.2f}x** "
                f"({'confortable' if cct >= 1.5 else 'acceptable' if cct >= 1.0 else 'risque de défaut'}). "
                f"Surveiller les {kpis.nb_alertes} alerte(s) active(s) sur clients et fournisseurs."
            )
            niveau = "error" if cct < 1.0 else "warning" if cct < 1.5 else "info"
            icone  = ""

        elif vue == "Alertes reseau":
            nb_r = sum(1 for a in self.alertes() if a.gravite == "rouge")
            nb_o = sum(1 for a in self.alertes() if a.gravite == "orange")
            if nb_r == 0 and nb_o == 0:
                texte  = f"**{mois}** — Aucune alerte active sur le réseau. Situation nominale."
                niveau = "info"
                icone  = ""
            else:
                texte = (
                    f"**{mois}** — **{nb_r} alerte(s) critique(s)** et {nb_o} en vigilance "
                    f"sur le réseau ({kpis.nb_sites_critiques} site(s) en rupture). "
                    f"Traiter en priorité les alertes rouges : virement DG ou activation ligne de crédit "
                    f"pour les sites sous le seuil critique."
                )
                niveau = "error" if nb_r > 0 else "warning"
                icone  = ""

        elif vue == "Budget & Pilotage":
            bdg = self.budget_vs_reel()
            if not bdg:
                texte  = f"**{mois}** — Fichier budget non disponible. Ajoutez budget_treso.xlsx pour activer cette vue."
                niveau = "warning"
                icone  = ""
            else:
                taux = bdg["taux_realisation_ca"]
                ecart = bdg["ecart_flux_ytd"]
                statut_bdg = "au-dessus" if taux >= 100 else "en dessous"
                texte = (
                    f"**{mois}** — Taux de réalisation CA : **{taux:.1f}%** "
                    f"({statut_bdg} de l'objectif). "
                    f"Écart flux net YTD : **{fmt_eur(ecart, sign=True)}** "
                    f"({'favorable' if ecart >= 0 else 'défavorable'}). "
                    f"CA réalisé : {fmt_eur(bdg['ca_reel_ytd'])} vs budget {fmt_eur(bdg['ca_budget_ytd'])}."
                )
                niveau = "error" if taux < 85 else "warning" if taux < 95 else "info"
                icone  = ""

        elif vue == "Previsionnel":
            from core.forecaster import TresoForecaster
            try:
                fc_data = TresoForecaster(self).forecast(horizon=6)
                solde_fin = float(fc_data["solde"].iloc[-1])
                solde_pess = float(
                    TresoForecaster(self).forecast(horizon=6, delta_enc=-0.10,
                                                   delta_dso=12)["solde"].iloc[-1]
                )
                alerte_pess = " **Risque de rupture en scénario pessimiste.**" if solde_pess < 0 else ""
                texte = (
                    f"**{mois}** — Solde de départ : **{fmt_eur(sol)}**. "
                    f"Forecast base à 6 mois : **{fmt_eur(solde_fin)}** "
                    f"({'positif' if solde_fin >= 0 else 'négatif'}). "
                    f"Couverture CT actuelle : {cct:.2f}x.{alerte_pess}"
                )
                niveau = "error" if solde_pess < 0 else "warning" if solde_fin < sol * 0.8 else "info"
            except Exception:
                texte  = f"**{mois}** — Données insuffisantes pour le forecast."
                niveau = "warning"
            icone  = ""

        else:
            texte  = ""
            niveau = "info"
            icone  = ""

        return {"texte": texte, "niveau": niveau, "icone": icone}


# =============================================================================
# FACTORY
# =============================================================================

def build_loader(
    source=None,
    data_dir: Path | str | None = None,
) -> TresoLoader:
    """
    Point d'entree principal pour Streamlit.
    Selectionne automatiquement la source via resolve_source() si non fournie.
    """
    if source is None:
        from core.data_source import resolve_source
        source = resolve_source()
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    return TresoLoader(source=source, data_dir=data_dir)

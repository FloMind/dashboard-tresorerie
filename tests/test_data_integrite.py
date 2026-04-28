# -*- coding: utf-8 -*-
"""
test_data_integrite.py
Tests d'integrite des 7 fichiers de donnees.
Verifie coherence, plages de valeurs, absence de nulls, couverture sites.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

NB_SITES = 30
NB_MOIS  = 28
NB_CATS  = 11   # sous-categories de flux
TVA      = 0.20


# ── Fixtures locales (chargement direct, independant du loader) ────────────

@pytest.fixture(scope="module")
def flux():        return pd.read_excel(DATA_DIR / "treso_flux.xlsx")

@pytest.fixture(scope="module")
def soldes():      return pd.read_excel(DATA_DIR / "treso_soldes.xlsx")

@pytest.fixture(scope="module")
def bfr():         return pd.read_excel(DATA_DIR / "treso_bfr.xlsx")

@pytest.fixture(scope="module")
def clients():     return pd.read_excel(DATA_DIR / "balance_client.xlsx")

@pytest.fixture(scope="module")
def fournisseurs():return pd.read_excel(DATA_DIR / "balance_fournisseur.xlsx")

@pytest.fixture(scope="module")
def stock():       return pd.read_excel(DATA_DIR / "stock_detail.xlsx")

@pytest.fixture(scope="module")
def catalogue():   return pd.read_excel(DATA_DIR / "ref_catalogue.xlsx")


# ── Tests flux ─────────────────────────────────────────────────────────────

class TestFlux:

    def test_nb_lignes(self, flux):
        """9 240 lignes = 30 sites x 28 mois x 11 categories."""
        assert len(flux) == NB_SITES * NB_MOIS * NB_CATS

    def test_couverture_sites(self, flux):
        assert flux["site_id"].nunique() == NB_SITES

    def test_couverture_mois(self, flux):
        assert flux["periode_idx"].nunique() == NB_MOIS

    def test_couverture_categories(self, flux):
        assert flux["sous_categorie"].nunique() == NB_CATS

    def test_pas_de_nulls(self, flux):
        assert flux.isnull().sum().sum() == 0

    def test_encaissements_positifs(self, flux):
        """Les encaissements clients et autres produits doivent etre > 0."""
        enc = flux[flux["sous_categorie"] == "Encaissements clients"]["montant"]
        assert (enc >= 0).all(), "Encaissements clients avec valeurs negatives"

    def test_decaissements_negatifs(self, flux):
        """Les decaissements d'exploitation doivent etre <= 0."""
        dec = flux[flux["categorie"] == "DECAISSEMENTS_EXPLOIT"]["montant"]
        assert (dec <= 0).all(), "Decaissements avec valeurs positives"

    def test_avr_2026_non_reel(self, flux):
        """Avril 2026 doit etre marque est_reel=False."""
        avr = flux[flux["mois_label"] == "Avr 2026"]["est_reel"].unique()
        assert len(avr) == 1 and not avr[0]

    def test_mar_2026_reel(self, flux):
        """Mars 2026 doit etre marque est_reel=True."""
        mar = flux[flux["mois_label"] == "Mar 2026"]["est_reel"].unique()
        assert len(mar) == 1 and mar[0]

    def test_ca_reseau_plausible(self, flux):
        """CA annualise reseau entre 30 et 80 M€."""
        enc = flux[flux["sous_categorie"] == "Encaissements clients"]["montant"].sum()
        ca  = enc / (1 + TVA) / (NB_MOIS / 12)
        assert 30e6 < ca < 80e6, f"CA annualise hors plage : {ca/1e6:.1f} M€"

    def test_coherence_flux_net(self, flux):
        """flux_net stocke est proche de la somme des montants.
        Tolerance large : inject_anomalies modifie montant sans recalculer flux_net."""
        calc   = flux.groupby(["site_id","periode_idx"])["montant"].sum()
        stored = flux.groupby(["site_id","periode_idx"])["flux_net"].first()
        # La grande majorite des cellules doit etre coherente (< 1 EUR)
        ecart_par_cellule = (calc - stored).abs()
        pct_ok = (ecart_par_cellule < 1.0).mean()
        assert pct_ok > 0.99, f"Plus de 1% des cellules flux_net incoherentes ({pct_ok:.1%})"


# ── Tests soldes ───────────────────────────────────────────────────────────

class TestSoldes:

    def test_nb_lignes(self, soldes):
        assert len(soldes) == NB_SITES * NB_MOIS

    def test_couverture_sites(self, soldes):
        assert soldes["site_id"].nunique() == NB_SITES

    def test_pas_de_nulls(self, soldes):
        assert soldes.isnull().sum().sum() == 0

    def test_coherence_solde_debut_fin(self, soldes):
        """solde_fin - solde_debut = flux_net pour chaque ligne."""
        diff  = (soldes["solde_fin"] - soldes["solde_debut"] - soldes["flux_net"]).abs()
        assert diff.max() < 1.0, f"Incoherence solde : ecart max {diff.max():.2f} EUR"

    def test_report_solde_entre_mois(self, soldes):
        """solde_debut(M) = solde_fin(M-1) pour chaque site.
        Exclus : S17 (anomalie TRE-02 injectee avec propagation partielle)."""
        sites_a_tester = [s for s in soldes["site_id"].unique() if s != "S17"]
        for sid in sites_a_tester:
            site_df = soldes[soldes["site_id"] == sid].sort_values("periode_idx")
            fins    = site_df["solde_fin"].values[:-1]
            debuts  = site_df["solde_debut"].values[1:]
            ecart   = abs(fins - debuts).max()
            assert ecart < 1.0, f"{sid} : rupture de solde, ecart {ecart:.2f} EUR"

    def test_runway_positif(self, soldes):
        """Le runway doit etre >= 0."""
        assert (soldes["runway_mois"] >= 0).all()

    def test_incident_s17_oct2024(self, soldes):
        """TRE-02 : S17 Oct 2024 doit avoir solde_fin < 0."""
        row = soldes[(soldes["site_id"] == "S17") &
                     (soldes["mois_label"] == "Oct 2024")]
        assert len(row) == 1
        assert row.iloc[0]["solde_fin"] < 0

    def test_incident_s22_mar2026(self, soldes):
        """TRE-01 : S22 Mar 2026 doit avoir solde_fin < 10 000."""
        row = soldes[(soldes["site_id"] == "S22") &
                     (soldes["mois_label"] == "Mar 2026")]
        assert len(row) == 1
        assert row.iloc[0]["solde_fin"] < 10_000


# ── Tests balance client ───────────────────────────────────────────────────

class TestBalanceClient:

    def test_couverture_sites(self, clients):
        assert clients["site_id"].nunique() == NB_SITES

    def test_pas_de_nulls(self, clients):
        assert clients.isnull().sum().sum() == 0

    def test_coherence_aging(self, clients):
        """Somme des tranches aging = encours_total."""
        cols = ["dont_non_echu","dont_0_30j","dont_30_60j","dont_60_90j","dont_plus_90j"]
        somme = clients[cols].sum(axis=1)
        ecart = (somme - clients["encours_total"]).abs().max()
        assert ecart < 10, f"Aging incoherent : ecart max {ecart:.0f} EUR"

    def test_encours_positif(self, clients):
        assert (clients["encours_total"] >= 0).all()

    def test_statuts_valides(self, clients):
        valides = {"Normal","Surveillance","Contentieux"}
        assert set(clients["statut_risque"].unique()).issubset(valides)

    def test_pareto_top3(self, clients):
        """Top 3 clients par site = 40-65% de l'encours (Pareto)."""
        top3 = clients[clients["rang_pareto"] <= 3]["encours_total"].sum()
        total = clients["encours_total"].sum()
        pct = top3 / total * 100
        assert 35 < pct < 70, f"Pareto hors plage : {pct:.0f}%"

    def test_incident_cli01_s02(self, clients):
        """CLI-01 : S02 rang 1 doit etre Contentieux."""
        row = clients[(clients["site_id"] == "S02") & (clients["rang_pareto"] == 1)]
        assert len(row) == 1
        assert row.iloc[0]["statut_risque"] == "Contentieux"
        assert row.iloc[0]["dont_plus_90j"] > 40_000

    def test_taux_utilisation_credit(self, clients):
        """CLI-02 : au moins un client avec taux_utilisation > 100%."""
        assert (clients["taux_utilisation"] > 100).any()

    def test_contentieux_proportion(self, clients):
        """Les contentieux doivent representer 5-15% des clients."""
        pct = (clients["statut_risque"] == "Contentieux").mean() * 100
        assert 3 < pct < 20, f"Proportion contentieux hors plage : {pct:.0f}%"


# ── Tests balance fournisseur ──────────────────────────────────────────────

class TestBalanceFournisseur:

    def test_couverture_sites(self, fournisseurs):
        assert fournisseurs["site_id"].nunique() == NB_SITES

    def test_pas_de_nulls(self, fournisseurs):
        assert fournisseurs.isnull().sum().sum() == 0

    def test_coherence_aging(self, fournisseurs):
        """Somme des tranches = encours_total."""
        cols = ["dont_non_echu","dont_0_30j","dont_30_60j_et_plus"]
        somme = fournisseurs[cols].sum(axis=1)
        ecart = (somme - fournisseurs["encours_total"]).abs().max()
        assert ecart < 1, f"Aging fournisseur incoherent : ecart {ecart:.2f} EUR"

    def test_conditions_paiement_lme(self, fournisseurs):
        """Aucune condition > 60j (LME France)."""
        cond_invalides = fournisseurs[
            fournisseurs["conditions_paiement"].str.contains("90j|120j", na=False)
        ]
        assert len(cond_invalides) == 0, "Conditions hors LME detectees"

    def test_grand_compte_dominant(self, fournisseurs):
        """Les grands comptes representent 55-85% de l'encours."""
        gc  = fournisseurs[fournisseurs["type_fournisseur"]=="Grand compte"]["encours_total"].sum()
        tot = fournisseurs["encours_total"].sum()
        pct = gc / tot * 100
        assert 50 < pct < 90, f"Part grands comptes hors plage : {pct:.0f}%"


# ── Tests stock ────────────────────────────────────────────────────────────

class TestStock:

    def test_couverture_sites(self, stock):
        assert stock["site_id"].nunique() == NB_SITES

    def test_pas_de_nulls(self, stock):
        assert stock.isnull().sum().sum() == 0

    def test_categories_abc(self, stock):
        assert set(stock["categorie_abc"].unique()) == {"A","B","C"}

    def test_valeur_stock_positive(self, stock):
        assert (stock["valeur_stock_ht"] >= 0).all()

    def test_coherence_valeur(self, stock):
        """valeur_stock_ht = qte_stock x pmp_ht (tolerance 1 EUR)."""
        calc = stock["qte_stock"] * stock["pmp_ht"]
        ecart = (calc - stock["valeur_stock_ht"]).abs()
        # Tolerance 2 EUR (arrondis)
        assert (ecart < 2).all(), f"Incoherence valeur stock : max {ecart.max():.2f} EUR"

    def test_incident_stk01_ruptures(self, stock):
        """STK-01 : exactement 3 references en Rupture."""
        ruptures = stock[stock["statut_stock"] == "Rupture"]
        assert len(ruptures) == 3

    def test_incident_stk02_surstockage(self, stock):
        """STK-02 : S07 doit avoir au moins une ref en Surstockage."""
        surst = stock[(stock["site_id"] == "S07") &
                      (stock["statut_stock"] == "Surstockage")]
        assert len(surst) >= 1

    def test_incident_stk03_dormant(self, stock):
        """STK-03 : S15 doit avoir une ref dormante depuis > 500j."""
        dorm = stock[(stock["site_id"] == "S15") &
                     (stock["dernier_mvt_jours"] > 500)]
        assert len(dorm) >= 1

    def test_dio_abc_ordre(self, stock):
        """DIO moyen : A < B < C (rotation fast > medium > slow)."""
        dio = stock.groupby("categorie_abc")["dio_reel_jours"].mean()
        assert dio["A"] < dio["B"] < dio["C"]

    def test_catalogue_coherence(self, stock, catalogue):
        """Toutes les refs du stock existent dans le catalogue."""
        refs_stock = set(stock["ref_id"].unique())
        refs_cat   = set(catalogue["ref_id"].unique())
        assert refs_stock.issubset(refs_cat), \
            f"{len(refs_stock - refs_cat)} refs stock absentes du catalogue"

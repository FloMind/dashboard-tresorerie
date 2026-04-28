# -*- coding: utf-8 -*-
"""test_data_source.py -- Tests de la couche d'abstraction des sources de donnees."""
import pytest
import pandas as pd
from pathlib import Path
from core.data_source import ExcelSource, TresoDataSource

DATA_DIR = Path(__file__).parent.parent / "data"
REQUIRED_COLS_FLUX = {
    "site_id","site_nom","profil","annee","mois_num","mois_label",
    "periode_idx","est_reel","categorie","sous_categorie","montant"
}
REQUIRED_COLS_SOLDES = {
    "site_id","site_nom","solde_debut","flux_net","solde_fin","runway_mois"
}


@pytest.fixture(scope="module")
def source():
    return ExcelSource(
        flux_path=DATA_DIR / "treso_flux.xlsx",
        soldes_path=DATA_DIR / "treso_soldes.xlsx",
        bfr_path=DATA_DIR / "treso_bfr.xlsx",
    )


class TestExcelSource:

    def test_herite_treso_data_source(self, source):
        assert isinstance(source, TresoDataSource)

    def test_load_flux_retourne_dataframe(self, source):
        df = source.load_flux()
        assert isinstance(df, pd.DataFrame)

    def test_load_flux_colonnes(self, source):
        df = source.load_flux()
        assert REQUIRED_COLS_FLUX.issubset(set(df.columns))

    def test_load_flux_non_vide(self, source):
        df = source.load_flux()
        assert len(df) > 0

    def test_load_soldes_retourne_dataframe(self, source):
        df = source.load_soldes()
        assert isinstance(df, pd.DataFrame)

    def test_load_soldes_colonnes(self, source):
        df = source.load_soldes()
        assert REQUIRED_COLS_SOLDES.issubset(set(df.columns))

    def test_load_bfr_retourne_dataframe(self, source):
        df = source.load_bfr()
        assert isinstance(df, pd.DataFrame)

    def test_load_all_retourne_3_dataframes(self, source):
        result = source.load_all()
        assert len(result) == 3
        for df in result:
            assert isinstance(df, pd.DataFrame)

    def test_fichier_inexistant_leve_erreur(self):
        s = ExcelSource(flux_path="inexistant.xlsx")
        with pytest.raises(Exception):
            s.load_flux()

    def test_flux_et_soldes_meme_sites(self, source):
        """Les deux fichiers couvrent exactement les memes sites."""
        sites_flux   = set(source.load_flux()["site_id"].unique())
        sites_soldes = set(source.load_soldes()["site_id"].unique())
        assert sites_flux == sites_soldes

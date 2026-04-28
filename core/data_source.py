# -*- coding: utf-8 -*-
"""
core/data_source.py -- FloMind Dashboard Tresorerie
=====================================================
Abstraction de la source de donnees de tresorerie.

Principe : le dashboard ne connait que TresoDataSource.
           La source concrete (Excel, SQL Server, API) est transparente.

V1   : ExcelSource     -- upload manuel ou fichier local
V1.5 : SQLServerSource -- connexion directe Sage 100 Premium / Cegid
V2   : PowensAPISource -- Open Banking via agregateur

Usage :
    from core.data_source import ExcelSource, resolve_source
    source = resolve_source()
    df_flux, df_soldes, df_bfr = source.load_all()
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd


class TresoDataSource(ABC):
    """Interface commune -- le dashboard consomme uniquement cette classe."""

    @abstractmethod
    def load_flux(self) -> pd.DataFrame:
        """
        Retourne les flux mensuels au format FloMind standard.
        Colonnes : site_id | site_nom | profil | annee | mois_num | mois_label
                   periode_idx | est_reel | categorie | sous_categorie
                   montant | flux_net
        Convention : encaissements > 0, decaissements < 0
        """

    @abstractmethod
    def load_soldes(self) -> pd.DataFrame:
        """
        Retourne les soldes bancaires mensuels.
        Colonnes : site_id | site_nom | profil | annee | mois_num | mois_label
                   periode_idx | est_reel | solde_debut | flux_net | solde_fin
                   solde_min | alerte_negatif | alerte_faible | runway_mois
        """

    @abstractmethod
    def load_bfr(self) -> pd.DataFrame:
        """
        Retourne les composantes BFR mensuelles.
        Colonnes : site_id | site_nom | profil | annee | mois_num | mois_label
                   periode_idx | est_reel | creances_clients | dettes_fournisseurs
                   stocks | bfr | dso_jours | dpo_jours | dio_jours | ccc_jours
                   bfr_jours_ca | alerte_dso_eleve | alerte_ccc_eleve
        """

    def load_all(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Charge les 3 tables en une seule fois."""
        return self.load_flux(), self.load_soldes(), self.load_bfr()


# ── V1 : Source Excel (fichiers locaux ou upload) ─────────────────────────────

class ExcelSource(TresoDataSource):
    """
    Lit les 3 fichiers Excel generes par generators/generate_treso.py.
    Compatible avec un upload Streamlit ou un chemin local.
    """
    def __init__(
        self,
        flux_path:   str | Path = "data/treso_flux.xlsx",
        soldes_path: str | Path = "data/treso_soldes.xlsx",
        bfr_path:    str | Path = "data/treso_bfr.xlsx",
    ):
        self._paths = {
            "flux":   Path(flux_path),
            "soldes": Path(soldes_path),
            "bfr":    Path(bfr_path),
        }

    def _read(self, path: Path) -> pd.DataFrame:
        """Lecture directe -- le cache est gere par TresoLoader._cache."""
        return pd.read_excel(path)

    def load_flux(self)   -> pd.DataFrame: return self._read(self._paths["flux"])
    def load_soldes(self) -> pd.DataFrame: return self._read(self._paths["soldes"])
    def load_bfr(self)    -> pd.DataFrame: return self._read(self._paths["bfr"])


# ── V1.5 : Source SQL Server (Sage 100 Premium / Cegid) ──────────────────────

class SQLServerSource(TresoDataSource):
    """
    Connexion directe a une base SQL Server comptable.
    Requiert : pyodbc + driver ODBC 17 for SQL Server

    La requete lit les ecritures comptables et les normalise
    vers le format FloMind standard via des regles de mapping PCG.

    Hypotheses :
      - Table F_ECRITUREC (Sage 100 standard)
      - Comptes 512xxx = banque, 401xxx = fournisseurs, 411xxx = clients
      - Journaux BQ/BQ* = banque, CA = caisse, AC/VT = achats/ventes

    Usage :
        source = SQLServerSource(
            server="192.168.1.10",
            database="GESCOM_2024",
            username="lecteur",
            password="***",
        )
    """
    def __init__(
        self,
        server:   str,
        database: str,
        username: str,
        password: str,
        driver:   str = "ODBC Driver 17 for SQL Server",
    ):
        self._conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "Trusted_Connection=no;"
        )

    def _connect(self):
        try:
            import pyodbc
            return pyodbc.connect(self._conn_str)
        except ImportError:
            raise RuntimeError(
                "pyodbc non installe. Lancez : pip install pyodbc"
            )

    def _query(self, sql: str) -> pd.DataFrame:
        """Execute une requete SQL et retourne un DataFrame."""
        with self._connect() as conn:
            return pd.read_sql(sql, conn)

    # Requete de base : ecritures de tresorerie depuis Sage 100
    _SQL_ECRITURES = """
        SELECT
            e.DO_Tiers                          AS site_id,
            CONVERT(DATE, e.EC_Date)            AS date,
            e.JO_Num                            AS journal,
            e.CA_Num                            AS compte,
            e.EC_Libelle                        AS libelle,
            ISNULL(e.EC_Debit, 0)               AS debit,
            ISNULL(e.EC_Credit, 0)              AS credit,
            e.EC_Debit - e.EC_Credit            AS montant_net
        FROM F_ECRITUREC e
        WHERE e.EC_Date >= DATEADD(month, -24, GETDATE())
          AND e.JO_Num IN ('BQ','BQ1','BQ2','CA','VT','AC','OD')
        ORDER BY e.EC_Date
    """

    def _to_flomind_format(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Transforme les ecritures brutes vers le format FloMind.
        Mapping PCG simplifie -- a adapter selon le plan comptable client.
        """
        raise NotImplementedError(
            "Mapping PCG a implementer selon le plan comptable du client. "
            "Consulter la documentation FloMind pour le schema de mapping."
        )

    def load_flux(self)   -> pd.DataFrame:
        raw = self._query(self._SQL_ECRITURES)
        return self._to_flomind_format(raw)

    def load_soldes(self) -> pd.DataFrame:
        raise NotImplementedError("load_soldes non implemente pour SQLServerSource")

    def load_bfr(self)    -> pd.DataFrame:
        raise NotImplementedError("load_bfr non implemente pour SQLServerSource")


# ── V2 : Source API Powens/Open Banking (futur) ───────────────────────────────

class PowensAPISource(TresoDataSource):
    """
    Connexion Open Banking via Powens (ex-Budget Insight).
    Requiert : compte AISP Powens + API key client.
    Non implemente -- placeholder pour la roadmap V2.
    """
    def __init__(self, api_key: str, account_ids: list[str]):
        self._api_key     = api_key
        self._account_ids = account_ids

    def load_flux(self)   -> pd.DataFrame: raise NotImplementedError("Roadmap V2")
    def load_soldes(self) -> pd.DataFrame: raise NotImplementedError("Roadmap V2")
    def load_bfr(self)    -> pd.DataFrame: raise NotImplementedError("Roadmap V2")


# ── Factory : selection automatique selon st.secrets ou config ───────────────

def resolve_source() -> TresoDataSource:
    """
    Selectionne la source selon la config Streamlit.
    Priorite : SQL > Excel local > Excel demo

    Configuration dans .streamlit/secrets.toml :
        [treso]
        mode = "sql"   # ou "excel"
        # Si mode = "sql" :
        server   = "192.168.1.10"
        database = "GESCOM"
        username = "lecteur"
        password = "..."
        # Si mode = "excel" :
        flux_path   = "data/treso_flux.xlsx"
        soldes_path = "data/treso_soldes.xlsx"
        bfr_path    = "data/treso_bfr.xlsx"
    """
    try:
        import streamlit as st   # import local : evite dependance globale hors runtime
        cfg = st.secrets.get("treso", {})
        mode = cfg.get("mode", "excel")

        if mode == "sql":
            return SQLServerSource(
                server=cfg["server"],
                database=cfg["database"],
                username=cfg["username"],
                password=cfg["password"],
            )

        # Defaut : Excel
        return ExcelSource(
            flux_path=cfg.get("flux_path",   "data/treso_flux.xlsx"),
            soldes_path=cfg.get("soldes_path","data/treso_soldes.xlsx"),
            bfr_path=cfg.get("bfr_path",     "data/treso_bfr.xlsx"),
        )

    except Exception:
        # Fallback demo : donnees synthetiques locales
        return ExcelSource()

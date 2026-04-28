# -*- coding: utf-8 -*-
"""
core/forecaster.py -- FloMind Dashboard Tresorerie
===================================================
Forecast de tresorerie par composante.

Approche : chaque composante est prevue selon sa nature economique.
Constantes importees depuis config.settings (source unique).
Le mois courant est derive du loader (dynamique, navigation temporelle).

Usage :
    from core.forecaster import TresoForecaster
    fc = TresoForecaster(loader)
    result = fc.forecast(horizon=6, scenario="base")
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from config.settings import TVA

# MOIS_COURANT est derive du loader (plus de constante locale)


class TresoForecaster:
    """
    Forecast par composante sur le reseau consolide.

    Parametres :
        loader : TresoLoader charge (mois_courant_idx derive dynamiquement)
    """

    def __init__(self, loader):
        self.loader          = loader
        self._fx             = loader.flux_raw
        self._sol            = loader.soldes_raw
        # Derive du loader : suit la navigation temporelle
        self._mois_courant_idx = loader.mois_courant_idx
        self._mois_courant     = loader._mois_courant
        self._fitted           = {}

        self._compute_params()

    def _compute_params(self) -> None:
        """Calcule les ratios structurels depuis les 12 derniers mois reels."""
        fx_reel = self._fx[self._fx["est_reel"] == True]
        m_max   = self._mois_courant_idx
        m_min   = max(0, m_max - 11)
        fx_12   = fx_reel[fx_reel["periode_idx"].between(m_min, m_max)]

        def agg(scat):
            return fx_12[fx_12["sous_categorie"] == scat]["montant"].sum()

        enc     = abs(agg("Encaissements clients"))
        ach_ttc = abs(agg("Paiements fournisseurs"))
        ca_ht   = enc / (1 + TVA)
        ach_ht  = ach_ttc / (1 + TVA)

        self.tx_marque    = (ca_ht - ach_ht) / ca_ht if ca_ht > 0 else 0.37
        self.tx_sal_ca    = abs(agg("Masse salariale")) / enc if enc > 0 else 0.22
        self.loyer_moy    = abs(agg("Loyers et charges locatives")) / 12
        self.remb_moy     = abs(agg("Remboursement emprunt")) / 12
        self.frais_fi_moy = abs(agg("Frais financiers")) / 12
        self.ch_expl_moy  = abs(agg("Charges d'exploitation")) / 12
        self.capex_ann    = abs(agg("Capex"))

    def _wls(self, serie: np.ndarray, horizon: int
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        WLS avec poids exponentiels.
        Retourne (forecast, lower_80, upper_80).
        """
        n = len(serie)
        X = np.arange(n).reshape(-1, 1)
        w = np.exp(np.linspace(0, 1, n))

        reg = LinearRegression()
        reg.fit(X, serie, sample_weight=w)

        X_fut = np.arange(n, n + horizon).reshape(-1, 1)
        fc    = reg.predict(X_fut)

        residus = serie - reg.predict(X)
        sigma   = np.std(residus)
        ecarts  = sigma * np.sqrt(np.arange(1, horizon + 1))
        return fc, fc - 1.28 * ecarts, fc + 1.28 * ecarts

    def _saison_n1(self, scat: str) -> dict:
        """Ratios saisonniers N-1 par mois (1-12)."""
        an_n1 = 2024 + (self._mois_courant_idx // 12) - 1
        fx_n1 = self._fx[
            (self._fx["annee"] == an_n1) &
            (self._fx["sous_categorie"] == scat)
        ].groupby("mois_num")["montant"].mean()

        mean = fx_n1.mean()
        if abs(mean) < 1:
            return {m: 1.0 for m in range(1, 13)}
        return {int(m): float(v / mean) for m, v in fx_n1.items()}

    def _apply_saison(self, fc: np.ndarray, scat: str, debut_idx: int) -> np.ndarray:
        """Applique la saisonnalite N-1 au forecast."""
        saison = self._saison_n1(scat)
        out    = fc.copy()
        for i in range(len(fc)):
            mois    = ((debut_idx + i) % 12) + 1
            out[i]  = fc[i] * saison.get(mois, 1.0)
        return out

    def _serie_reseau(self, scat: str) -> np.ndarray:
        """Serie mensuelle reseau reelle pour une sous-categorie."""
        return (self._fx[
            (self._fx["sous_categorie"] == scat) &
            (self._fx["est_reel"] == True) &
            (self._fx["periode_idx"] <= self._mois_courant_idx)
        ].groupby("periode_idx")["montant"].sum()
         .sort_index().values)

    def _capex_pattern(self, mois_1based: int, ca_ann: float) -> float:
        """Capex rule-based : concentre T1 (fev/mars) et T3 (aout/sept).

        Les poids sont NORMALISES pour que leur somme sur 12 mois = 1.0,
        garantissant que le CAPEX annuel total = ca_ann * 1.5%.
        Bug corrige v4.1 : poids bruts sommaient a 1.525 → surestimation 52%.
        """
        # Poids normalises (divises par 1.525, somme = 1.0 sur les 12 mois)
        poids = {2: 0.2295, 3: 0.2295, 8: 0.1639, 9: 0.1639, 6: 0.0984}
        default = 0.0164   # les 7 autres mois (7 * 0.0164 ≈ 0.1148, total ≈ 1.0)
        return -ca_ann * 0.015 * poids.get(mois_1based, default)

    def _impots_pattern(self, mois_1based: int, ca_ann: float) -> float:
        """Impots rule-based : CFE dec, CVAE mai/sept, IS mensuel."""
        if   mois_1based == 12: return -ca_ann * 0.004
        elif mois_1based ==  5: return -ca_ann * 0.001
        elif mois_1based ==  9: return -ca_ann * 0.001
        else:                   return -ca_ann * 0.0003

    def forecast(
        self,
        horizon:   int   = 6,
        delta_enc: float = 0.0,
        delta_dso: int   = 0,
        delta_dpo: int   = 0,
    ) -> pd.DataFrame:
        """
        Forecast par composante sur `horizon` mois.

        Parametres :
            horizon    : nb de mois a prevoir (3-12)
            delta_enc  : choc sur les encaissements en % (+0.10 = +10%)
            delta_dso  : choc DSO en jours (ralentit les encaissements)
            delta_dpo  : choc DPO en jours (retarde les paiements, favorable)
        """
        debut_idx   = self._mois_courant_idx + 1
        mois_labels = self._mois_labels(debut_idx, horizon)

        # 1. Encaissements clients (WLS + saisonnalite)
        serie_enc = self._serie_reseau("Encaissements clients")
        fc_enc, lo_enc, hi_enc = self._wls(serie_enc, horizon)
        fc_enc = self._apply_saison(fc_enc, "Encaissements clients", debut_idx)

        if delta_dso != 0:
            fc_enc = fc_enc * (1 - delta_dso / 300)
        if delta_enc != 0:
            fc_enc = fc_enc * (1 + delta_enc)

        lo_enc = lo_enc * (1 + delta_enc) * (1 - delta_dso / 300)
        hi_enc = hi_enc * (1 + delta_enc) * (1 - delta_dso / 300)

        # 2. Paiements fournisseurs
        fc_ca_ht  = fc_enc / (1 + TVA)
        fc_ach_ht = fc_ca_ht * (1 - self.tx_marque)
        dpo_shift = delta_dpo / 30
        fc_pmt    = -(fc_ach_ht * (1 + TVA)) * (1 - dpo_shift)

        # 3. Masse salariale (WLS)
        serie_sal = self._serie_reseau("Masse salariale")
        fc_sal, _, _ = self._wls(serie_sal, horizon)
        fc_sal = np.clip(fc_sal, -fc_ca_ht.mean() * 0.35, 0)

        # 4. TVA nette (rule-based, decalage 1 mois)
        fc_tva    = -(fc_ca_ht - fc_ach_ht) * TVA
        fc_tva    = np.roll(fc_tva, 1)
        fc_tva[0] = fc_tva[1]

        # 5. Charges exploitation (WLS)
        serie_ch = self._serie_reseau("Charges d'exploitation")
        fc_ch, _, _ = self._wls(serie_ch, horizon)
        fc_ch = np.clip(fc_ch, -self.ch_expl_moy * 2, 0)

        # 6. Loyers (fixe + inflation 2%/an)
        fc_loyers = np.array([
            -self.loyer_moy * (1 + 0.02 * ((debut_idx + i) // 12))
            for i in range(horizon)
        ])

        # 7. Remboursement emprunt (fixe)
        fc_remb = np.full(horizon, -self.remb_moy)

        # 8. Capex (rule-based saisonnier)
        ca_ann_prev = float(fc_ca_ht.mean()) * 12
        fc_capex = np.array([
            self._capex_pattern((debut_idx + i) % 12 + 1, ca_ann_prev)
            for i in range(horizon)
        ])

        # 9. Impots et taxes (rule-based)
        fc_impots = np.array([
            self._impots_pattern((debut_idx + i) % 12 + 1, ca_ann_prev)
            for i in range(horizon)
        ])

        # 10. Frais financiers (fixe)
        fc_frais = np.full(horizon, -self.frais_fi_moy)

        # Flux net + solde
        flux_net = (fc_enc + fc_pmt + fc_sal + fc_tva + fc_ch +
                    fc_loyers + fc_remb + fc_capex + fc_impots + fc_frais)

        # Solde de depart = dernier solde reel reseau (mois courant dynamique)
        sol_depart = (self._sol[self._sol["mois_label"] == self._mois_courant]
                      ["solde_fin"].sum())
        soldes   = sol_depart + np.cumsum(flux_net)
        # IC 80% sur le solde — marche aleatoire sqrt(t), pas cumsum
        # Le cumsum sur-infle l'IC d'un facteur ~3x a M+6
        _reg_ic = LinearRegression()
        _x_ic   = np.arange(len(serie_enc)).reshape(-1, 1)
        _reg_ic.fit(_x_ic, serie_enc)
        sigma_enc  = float(np.std(serie_enc - _reg_ic.predict(_x_ic)))
        delta_ic   = 1.28 * sigma_enc * np.sqrt(np.arange(1, horizon + 1))
        solde_lo   = soldes - delta_ic
        solde_hi   = soldes + delta_ic

        return pd.DataFrame({
            "mois_label":           mois_labels,
            "periode_idx":          list(range(debut_idx, debut_idx + horizon)),
            "enc_clients":          fc_enc,
            "pmt_fournisseurs":     fc_pmt,
            "masse_salariale":      fc_sal,
            "tva_nette":            fc_tva,
            "charges_exploitation": fc_ch,
            "loyers":               fc_loyers,
            "remb_emprunt":         fc_remb,
            "capex":                fc_capex,
            "impots_taxes":         fc_impots,
            "frais_financiers":     fc_frais,
            "flux_net":             flux_net,
            "solde":                soldes,
            "solde_ic_lo":          solde_lo,
            "solde_ic_hi":          solde_hi,
        })

    def scenarios(
        self,
        horizon: int = 6,
        delta_enc_opt: float = 0.12,
        delta_enc_pess: float = -0.10,
        delta_dso_pess: int = 12,
        delta_dpo_opt: int = 7,
    ) -> dict[str, pd.DataFrame]:
        return {
            "base":       self.forecast(horizon),
            "optimiste":  self.forecast(horizon,
                                        delta_enc=delta_enc_opt,
                                        delta_dpo=delta_dpo_opt),
            "pessimiste": self.forecast(horizon,
                                        delta_enc=delta_enc_pess,
                                        delta_dso=delta_dso_pess),
        }

    @staticmethod
    def _mois_labels(debut_idx: int, horizon: int) -> list[str]:
        MOIS = ["Jan","Fev","Mar","Avr","Mai","Jun",
                "Jul","Aou","Sep","Oct","Nov","Dec"]
        return [
            f"{MOIS[(debut_idx + i) % 12]} {2024 + (debut_idx + i) // 12}"
            for i in range(horizon)
        ]

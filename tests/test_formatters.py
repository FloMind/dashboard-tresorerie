# -*- coding: utf-8 -*-
"""test_formatters.py -- Tests des fonctions de formatage."""
import pytest
from components.formatters import fmt_eur, fmt_pct, fmt_jours, rag_color, rag_solde


class TestFmtEur:

    def test_millions(self):
        assert fmt_eur(1_500_000) == "1.50 M€"

    def test_milliers(self):
        assert fmt_eur(45_000) == "45 k€"

    def test_euros(self):
        assert fmt_eur(3_200) == "3,200 €"

    def test_negatif_millions(self):
        assert fmt_eur(-2_300_000) == "-2.30 M€"

    def test_negatif_milliers(self):
        assert fmt_eur(-11_800) == "-12 k€"

    def test_signe_positif(self):
        r = fmt_eur(50_000, sign=True)
        assert r.startswith("+")

    def test_signe_negatif(self):
        r = fmt_eur(-50_000, sign=True)
        assert r.startswith("-")

    def test_force_unit_m(self):
        assert "M€" in fmt_eur(500_000, unit="M")

    def test_force_unit_k(self):
        assert "k€" in fmt_eur(500_000, unit="k")

    def test_zero(self):
        assert "0" in fmt_eur(0)


class TestFmtPct:

    def test_positif_avec_signe(self):
        assert fmt_pct(5.3) == "+5.3%"

    def test_negatif(self):
        assert fmt_pct(-3.7) == "-3.7%"

    def test_zero(self):
        """0.0% : pas de signe + (convention : sign s'applique seulement si val > 0)."""
        r = fmt_pct(0.0)
        assert "0.0%" in r

    def test_sans_signe(self):
        r = fmt_pct(5.3, sign=False)
        assert not r.startswith("+")


class TestFmtJours:

    def test_entier(self):
        assert fmt_jours(48.0) == "48j"

    def test_arrondi(self):
        assert fmt_jours(47.6) == "48j"


class TestRagColor:

    def test_rouge_depasse_seuil(self):
        from config.settings import RAG
        c = rag_color(80, seuil_rouge=70, seuil_orange=60)
        assert c == RAG["rouge"]

    def test_orange_entre_seuils(self):
        from config.settings import RAG
        c = rag_color(65, seuil_rouge=70, seuil_orange=60)
        assert c == RAG["orange"]

    def test_vert_sous_seuil(self):
        from config.settings import RAG
        c = rag_color(50, seuil_rouge=70, seuil_orange=60)
        assert c == RAG["vert"]

    def test_inverse_rouge_bas(self):
        from config.settings import RAG
        c = rag_color(0.5, seuil_rouge=1.0, seuil_orange=3.0, inverse=True)
        assert c == RAG["rouge"]

    def test_inverse_vert_haut(self):
        from config.settings import RAG
        c = rag_color(5.0, seuil_rouge=1.0, seuil_orange=3.0, inverse=True)
        assert c == RAG["vert"]


class TestRagSolde:

    def test_solde_negatif_rouge(self):
        assert rag_solde(-1000, 5.0) == "rouge"

    def test_runway_critique_rouge(self):
        assert rag_solde(50_000, 0.5) == "rouge"

    def test_solde_faible_orange(self):
        assert rag_solde(5_000, 5.0) == "orange"

    def test_runway_vigilance_orange(self):
        assert rag_solde(50_000, 2.0) == "orange"

    def test_normal_vert(self):
        assert rag_solde(100_000, 5.0) == "vert"

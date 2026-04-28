# -*- coding: utf-8 -*-
"""test_charts.py -- Tests de generation des graphiques Plotly."""
import pytest
import plotly.graph_objects as go
from components.charts import (
    chart_evolution_solde, chart_waterfall, chart_flux_mensuel,
    chart_aging_donut, chart_score_risque, chart_bfr_evolution,
    chart_heatmap_soldes,
)


class TestChartEvolutionSolde:

    def test_retourne_figure(self, position):
        fig = chart_evolution_solde(position["evolution"])
        assert isinstance(fig, go.Figure)

    def test_nb_traces_min(self, position):
        fig = chart_evolution_solde(position["evolution"])
        assert len(fig.data) >= 1

    def test_contient_annotations(self, position):
        fig = chart_evolution_solde(position["evolution"])
        assert len(fig.layout.annotations) >= 1


class TestChartWaterfall:

    def test_retourne_figure(self, flux_data):
        fig = chart_waterfall(flux_data["waterfall_courant"])
        assert isinstance(fig, go.Figure)

    def test_une_trace(self, flux_data):
        fig = chart_waterfall(flux_data["waterfall_courant"])
        assert len(fig.data) == 1

    def test_type_waterfall(self, flux_data):
        fig = chart_waterfall(flux_data["waterfall_courant"])
        assert isinstance(fig.data[0], go.Waterfall)

    def test_nb_elements(self, flux_data):
        """11 postes + 1 total = 12 elements."""
        fig = chart_waterfall(flux_data["waterfall_courant"])
        assert len(fig.data[0].x) == 12


class TestChartFluxMensuel:

    def test_retourne_figure(self, loader):
        fig = chart_flux_mensuel(loader.flux_raw)
        assert isinstance(fig, go.Figure)

    def test_plusieurs_traces(self, loader):
        """Au moins 5 traces : 4 categories + ligne flux net."""
        fig = chart_flux_mensuel(loader.flux_raw)
        assert len(fig.data) >= 5

    def test_barmode_relative(self, loader):
        fig = chart_flux_mensuel(loader.flux_raw)
        assert fig.layout.barmode == "relative"


class TestChartAgingDonut:

    def test_retourne_figure(self, bfr_data):
        fig = chart_aging_donut(bfr_data["aging_consolide"])
        assert isinstance(fig, go.Figure)

    def test_type_pie(self, bfr_data):
        fig = chart_aging_donut(bfr_data["aging_consolide"])
        assert isinstance(fig.data[0], go.Pie)

    def test_hole(self, bfr_data):
        fig = chart_aging_donut(bfr_data["aging_consolide"])
        assert fig.data[0].hole > 0

    def test_5_secteurs(self, bfr_data):
        fig = chart_aging_donut(bfr_data["aging_consolide"])
        assert len(fig.data[0].labels) == 5


class TestChartScoreRisque:

    def test_retourne_figure(self, score):
        fig = chart_score_risque(score)
        assert isinstance(fig, go.Figure)

    def test_barres_horizontales(self, score):
        fig = chart_score_risque(score)
        assert fig.data[0].orientation == "h"

    def test_15_sites_max(self, score):
        fig = chart_score_risque(score)
        assert len(fig.data[0].x) <= 15


class TestChartBfrEvolution:

    def test_retourne_figure(self, loader):
        fig = chart_bfr_evolution(loader.flux_raw)
        assert isinstance(fig, go.Figure)

    def test_traces(self, loader):
        fig = chart_bfr_evolution(loader.flux_raw)
        assert len(fig.data) >= 1


class TestChartHeatmapSoldes:

    def test_retourne_figure(self, loader):
        fig = chart_heatmap_soldes(loader.soldes_raw)
        assert isinstance(fig, go.Figure)

    def test_type_heatmap(self, loader):
        fig = chart_heatmap_soldes(loader.soldes_raw)
        assert isinstance(fig.data[0], go.Heatmap)

    def test_dimensions(self, loader):
        """30 sites x 28 mois."""
        fig = chart_heatmap_soldes(loader.soldes_raw)
        hm  = fig.data[0]
        assert len(hm.y) == 30
        assert len(hm.x) == 28

# -*- coding: utf-8 -*-
"""conftest.py -- Fixtures partagees pour pytest"""
import sys
from pathlib import Path
import pytest

# Ajout du root au path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.loader import build_loader

@pytest.fixture(scope="session")
def loader():
    """Loader charge une seule fois pour toute la session de tests."""
    return build_loader(data_dir=ROOT / "data")

@pytest.fixture(scope="session")
def kpis(loader):
    return loader.kpi_global()

@pytest.fixture(scope="session")
def position(loader):
    return loader.position()

@pytest.fixture(scope="session")
def flux_data(loader):
    return loader.flux()

@pytest.fixture(scope="session")
def bfr_data(loader):
    return loader.bfr()

@pytest.fixture(scope="session")
def alertes(loader):
    return loader.alertes()

@pytest.fixture(scope="session")
def score(loader):
    return loader.score_risque()

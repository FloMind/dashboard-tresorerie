# -*- coding: utf-8 -*-
"""config/settings.py -- FloMind Dashboard Tresorerie
======================================================
SOURCE UNIQUE DE VERITE pour toutes les constantes.
Importer depuis ici, ne jamais redefinir ailleurs.
"""

# ── Période courante ───────────────────────────────────────────────────────────
MOIS_COURANT_LABEL = "Mar 2026"
MOIS_COURANT_IDX   = 26          # 0-based : Jan 2024 = 0, Fev 2024 = 1 ...

# ── Paramètres financiers ─────────────────────────────────────────────────────
TVA = 0.20

# ── Seuils alertes ────────────────────────────────────────────────────────────
SEUIL_RUNWAY_CRITIQUE  = 1.0      # mois
SEUIL_RUNWAY_VIGILANCE = 3.0      # mois
SEUIL_SOLDE_FAIBLE     = 15_000   # EUR

# ── Benchmarks sectoriels (négoce B2B France) ─────────────────────────────────
BENCH = {
    "dso": (45, 55),   # jours
    "dpo": (30, 45),
    "dio": (20, 35),
    "ccc": (40, 70),
    "ebe": (3,   7),   # % CA
}

# ── Couleurs RAG ──────────────────────────────────────────────────────────────
RAG = {
    "rouge":  "#C62828",
    "orange": "#E65100",
    "vert":   "#2E7D32",
    "bleu":   "#1565C0",
    "gris":   "#546E7A",
}

# ── Couleurs Plotly catégories flux ───────────────────────────────────────────
CAT_COLORS = {
    "ENCAISSEMENTS":         "#2E7D32",
    "DECAISSEMENTS_EXPLOIT": "#C62828",
    "FISCAL":                "#E65100",
    "INVESTISSEMENT":        "#6A1B9A",
    "FINANCEMENT":           "#1565C0",
}

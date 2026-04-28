# FloMind — Dashboard Trésorerie Multisite

> Portfolio CDG × Data × IA — Florent, Data Scientist & Contrôleur de Gestion  
> Spécialisation : PME négoce B2B multisite, Auvergne-Rhône-Alpes

Dashboard de pilotage de la trésorerie conçu pour des réseaux de PME négoce B2B (type distributeur multisite). Démontre l'application concrète de la data science aux problématiques de contrôle de gestion terrain.

---

## Aperçu

7 vues de pilotage sur un réseau de 30 sites synthétiques (28 mois de données) :

| Vue | Contenu |
|-----|---------|
| **Tour de contrôle** | KPIs header, soldes bancaires, runway, heatmap sites × mois, incidents prioritaires |
| **Flux** | Waterfall mensuel, barchart empilé 28 mois, comparaison N vs N-1 dynamique |
| **BFR** | DSO/DPO/DIO/CCC vs benchmarks, aging balance clients, stock ABC, fournisseurs |
| **Alertes** | Score de risque 0–100 par site, feed filtrable, répartition par type |
| **Budget & Pilotage** | Budget vs Réalisé YTD, écarts par poste, concentration clients (HHI) |
| **Prévisionnel** | Rolling forecast WLS + saisonnalité N-1, 3 scénarios, IC 80%, ligne budget cible |
| **Guide d'utilisation** | Documentation, script de présentation 12 min, KPIs & méthodes, glossaire |

**Narratif auto-généré** : 2-3 phrases contextuelles en haut de chaque vue, niveau RAG (info / warning / error) calculé depuis les KPIs live.  
**Aide contextuelle inline** : `help=` sur tous les `st.metric()` + expander "Comment lire cette vue" en bas de chaque vue.  
**Bannière critique** : alerte rouge automatique si un site passe en rupture (runway < 1 mois), impossible à manquer quelle que soit la vue ouverte.

---

## KPIs financiers

| KPI | Formule | Nouveauté v4.1 |
|-----|---------|---------------|
| Solde réseau | Σ soldes fin de mois | — |
| Flux net mois | Encaissements − Décaissements | — |
| **Couverture CT** | Solde / (Dettes four. + Mensualité emprunt) | ✓ Nouveau |
| Point mort trésorerie | (CF + 80% MS) / Taux MCV | — |
| EBE cash YTD | Flux exploit. YTD / CA YTD × 100 | — |
| BFR réseau | Créances + Stocks − Dettes fournisseurs | — |
| **CCR** | Flux exploit. / \|EBE cash\| (périmètre opérationnel uniquement) | ✓ Corrigé |
| **Concentration clients** | Top 1/3/10 % + HHI par site | ✓ Nouveau |
| Score de risque | Log-normalisé 0–100 | — |
| Runway par site | Solde / Déc. moyens mensuels | — |

---

## Forecast — méthode

Contrairement aux outils qui extrapolent le solde global (Agicap, Fygr), le forecast raisonne **composante par composante** :

| Composante | Méthode |
|------------|---------|
| Encaissements clients | WLS + saisonnalité N-1 + IC 80% |
| Paiements fournisseurs | Déduit du CA prév × (1 − tx_marque) |
| Masse salariale | WLS tendance |
| TVA nette | Règle CA3, décalée d'1 mois |
| Loyers | Fixe + indexation 2%/an |
| Remboursement emprunt | Fixe contractuel |
| CAPEX | Pattern saisonnier T1/T3, poids normalisés (Σ = 1,0) |
| Impôts/taxes | CFE décembre, CVAE mai/septembre |

Ligne budget cible affichée dans le graphique forecast si `budget_treso.xlsx` est présent.

---

## Stack technique

```
Python 3.12
Streamlit        — UI & navigation
Plotly           — visualisations interactives (11 graphiques)
Pandas / NumPy   — traitement données
scikit-learn     — régression WLS forecast
fpdf2            — export PDF rapport exécutif 3 pages
bcrypt           — authentification (désactivée en mode démo)
openpyxl         — lecture fichiers Excel
pytest           — 85 tests (100% passing)
```

---

## Installation locale

```bash
git clone https://github.com/FloMind/dashboard-tresorerie
cd dashboard-tresorerie
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Sous Windows : double-cliquer sur `lancer.bat` (crée le venv automatiquement, détecte les conflits de port, lance l'app).

---

## Architecture

```
dashboard-tresorerie/
│
├── app.py                        ← Point d'entrée — sidebar, routing, bannière critique,
│                                   narratif auto, navigation sans emoji
├── config/
│   └── settings.py               ← Couleurs RAG, benchmarks sectoriels, mois courant
│
├── core/
│   ├── loader.py                 ← KPIs, agrégats, BFR, budget vs réalisé,
│   │                               concentration_clients(), narrative() auto
│   ├── forecaster.py             ← Rolling forecast WLS — 8 composantes, CAPEX normalisé
│   └── data_source.py            ← Abstraction V1 Excel / V1.5 SQL / V2 API
│
├── components/
│   ├── styles.py                 ← CSS global — typographie, cards, sidebar, tables
│   ├── kpi_cards.py              ← Header 6 KPIs custom (dont Couverture CT)
│   ├── charts.py                 ← 11 graphiques Plotly — hauteurs et polices calibrées
│   ├── formatters.py             ← M€/k€/€, badges HTML, RAG
│   └── aide.py                   ← Aide contextuelle — expanders par vue + contenu
│
├── views/
│   ├── position.py               ← Soldes, runway, heatmap, incidents
│   ├── flux.py                   ← Waterfall, barchart, N vs N-1
│   ├── bfr.py                    ← Ratios, aging, stock ABC, fournisseurs
│   ├── alertes.py                ← Score risque, feed, donut
│   ├── budget.py                 ← Budget vs Réalisé, écarts, concentration clients
│   ├── previsionnel.py           ← Forecast 3 scénarios, IC 80%, ligne budget
│   └── guide.py                  ← Documentation, script présentation, glossaire
│
├── utils/
│   ├── auth.py                   ← Authentification bcrypt (désactivée en démo)
│   └── pdf_export.py             ← Rapport PDF 3 pages (fpdf2)
│
├── tests/                        ← 85 tests pytest — intégrité, loader, formatters
├── data/                         ← Données synthétiques (voir section ci-dessous)
├── requirements.txt
└── lancer.bat                    ← Launcher Windows avec venv auto + détection port
```

---

## Données synthétiques

Toutes les données sont **entièrement synthétiques**, générées par les scripts dans `generators/` (non versionnés). Aucune donnée réelle ne doit être committée.

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `treso_flux.xlsx` | 9 240 | Flux mensuels 28 mois × 30 sites × 11 catégories |
| `treso_soldes.xlsx` | 840 | Soldes bancaires + runway par site |
| `balance_client.xlsx` | 628 | Encours + aging 5 tranches + CA annuel client |
| `balance_fournisseur.xlsx` | 285 | Dettes + conditions LME + retards |
| `stock_detail.xlsx` | 3 335 | 152 références × 30 sites (ABC, DIO, dormants) |
| `ref_catalogue.xlsx` | 152 | Référentiel articles |
| `budget_treso.xlsx` | — | Budget annuel par site / mois / sous-catégorie *(optionnel)* |

10 anomalies injectées pour la crédibilité démo : contentieux client 46 k€, rupture stock catégorie A, site S22 en solde critique 3 200 €, 3 fournisseurs hors LME, cluster de retards DSO > 90j sur 2 sites.

---

## Tests

```bash
python -m pytest tests/ -v
# 85 tests — 100% passing
```

Couverture : intégrité des données (nulls, signes, couverture sites/mois) · loader (KPIs, BFR, forecast) · formatters (M€/k€/€) · charts (smoke tests) · data source.

---

## Corrections v4.1

| # | Fichier | Correction |
|---|---------|------------|
| 1 | `loader.py` | `KpiGlobal` — champs `delta_solde_m1` / `delta_flux_m1` dupliqués supprimés |
| 2 | `loader.py` | `budget_raw` — double définition de propriété supprimée |
| 3 | `loader.py` | `CCR` — numérateur recalibré sur flux opérationnel uniquement |
| 4 | `loader.py` | `n_vs_n1` — années 2024/2025 hardcodées → `an_courant − 1` dynamique |
| 5 | `views/flux.py` | Colonnes `n_vs_n1` adaptées aux noms dynamiques |
| 6 | `views/previsionnel.py` | Solde départ "Mar 2026" hardcodé → `loader._mois_courant` |
| 7 | `core/forecaster.py` | CAPEX — poids non normalisés corrigés (surestimation +52% résolue) |
| 8 | `components/charts.py` | Titre de graphique figé → plage de dates dynamique |
| 9 | `views/previsionnel.py` | Label "N-1 (2025)" figé → dynamique |

---

## Évolutions v4.1

**Nouveaux KPIs**
- Couverture CT (solvabilité immédiate) dans le header — seuils ≥ 1,5x / 1,0x / < 1,0x
- Concentration clients par site — top 1/3/10 %, indice Herfindahl-Hirschman (HHI)

**Nouvelle vue**
- Budget & Pilotage — Budget vs Réalisé YTD, écarts par poste (graphiques + tableau filtrable + export CSV), concentration clients réseau

**Forecast enrichi**
- Ligne budget cible affichée sur le graphique forecast (pointillé ambre)
- Méthode `concentration_clients()` dans le loader

**Expérience utilisateur**
- Narratif auto : `narrative(vue)` génère 2-3 phrases contextuelles + niveau RAG par vue
- Bannière critique automatique si runway < 1 mois sur au moins un site
- `components/aide.py` : expander "Comment lire cette vue" dans les 6 vues opérationnelles
- `help=` sur tous les `st.metric()` — tooltip au survol du label
- Navigation sans emoji — charte visuelle professionnelle DAF/DG
- Polices 11 → 12–13px, hauteurs graphiques recalibrées, couleurs illisibles corrigées

**Guide d'utilisation**
- 4 onglets : Les 7 vues / Script de présentation / KPIs & Méthodes / Glossaire
- Script de présentation 12–15 min annoté (durée par bloc, texte verbatim)
- Documentation complète des KPIs avec formules et seuils RAG

---

## Roadmap

- **V1.5** — Connexion SQL Server directe (Sage 100 Premium, EBP)
- **V2** — Open Banking via Powens (AISP agréé)
- **RBAC** — Réactivation authentification bcrypt DG / directeur site
- **Multi-tenant** — Résolution singleton muté `TresoLoader` pour Streamlit Cloud multi-utilisateurs

---

## Contact

**Florent** — CDG × Data × IA  
Consulting FloMind · Ain · Rhône · Saône-et-Loire  
GitHub : [@FloMind](https://github.com/FloMind)

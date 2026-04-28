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

---

## KPIs financiers

| KPI | Formule |
|-----|---------|
| Solde réseau | Σ soldes fin de mois |
| Flux net mois | Encaissements − Décaissements |
| Couverture CT | Solde / (Dettes four. + Mensualité emprunt) |
| Point mort trésorerie | (CF + 80% MS) / Taux MCV |
| EBE cash YTD | Flux exploit. YTD / CA YTD × 100 |
| BFR réseau | Créances + Stocks − Dettes fournisseurs |
| CCR | Flux exploit. / \|EBE cash\| (périmètre opérationnel) |
| Concentration clients | Top 1/3/10 % + HHI par site |
| Score de risque | Log-normalisé 0–100 |
| Runway par site | Solde / Déc. moyens mensuels |

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
| CAPEX | Pattern saisonnier T1/T3, poids normalisés |
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
│                                   narratif auto
├── config/
│   └── settings.py               ← Couleurs RAG, benchmarks sectoriels, mois courant
│
├── core/
│   ├── loader.py                 ← KPIs, agrégats, BFR, budget vs réalisé,
│   │                               concentration_clients(), narrative()
│   ├── forecaster.py             ← Rolling forecast WLS — 8 composantes
│   └── data_source.py            ← Abstraction V1 Excel / V1.5 SQL / V2 API
│
├── components/
│   ├── styles.py                 ← CSS global — typographie, cards, sidebar, tables
│   ├── kpi_cards.py              ← Header 6 KPIs custom
│   ├── charts.py                 ← 11 graphiques Plotly
│   ├── formatters.py             ← M€/k€/€, badges HTML, RAG
│   └── aide.py                   ← Aide contextuelle — expanders par vue
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
├── data/                         ← Données synthétiques
├── requirements.txt
└── lancer.bat                    ← Launcher Windows
```

---

## Données synthétiques

Toutes les données sont **entièrement synthétiques** — générées par les scripts dans `generators/` (non versionnés). Aucune donnée réelle ne doit être committée.

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `treso_flux.xlsx` | 9 240 | Flux mensuels 28 mois × 30 sites × 11 catégories |
| `treso_soldes.xlsx` | 840 | Soldes bancaires + runway par site |
| `balance_client.xlsx` | 628 | Encours + aging 5 tranches + CA annuel client |
| `balance_fournisseur.xlsx` | 285 | Dettes + conditions LME + retards |
| `stock_detail.xlsx` | 3 335 | 152 références × 30 sites (ABC, DIO, dormants) |
| `ref_catalogue.xlsx` | 152 | Référentiel articles |
| `budget_treso.xlsx` | — | Budget annuel par site / mois / sous-catégorie *(optionnel)* |

---

## Tests

```bash
python -m pytest tests/ -v
# 85 tests — 100% passing
```

---

## Roadmap

- **V1.5** — Connexion SQL Server directe (Sage 100 Premium, EBP)
- **V2** — Open Banking via Powens (AISP agréé)
- **RBAC** — Réactivation authentification bcrypt DG / directeur site

---

## Contact

**Florent** — CDG × Data × IA  
Consulting FloMind · Ain · Rhône · Saône-et-Loire  
GitHub : [@FloMind](https://github.com/FloMind)

# -*- coding: utf-8 -*-
"""views/guide.py — Guide d'utilisation FloMind Trésorerie v4.1"""
import streamlit as st
from components.styles import CARD_COLORS


# ── Helpers visuels ───────────────────────────────────────────────────────────

def _vue_badge(nom, couleur, sous_titre):
    """Badge de vue sans emoji — carré coloré + typographie."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;'
        f'background:#F8FAFC;border-left:4px solid {couleur};'
        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:4px">'
        f'<div style="width:8px;height:8px;border-radius:50%;'
        f'background:{couleur};flex-shrink:0"></div>'
        f'<div>'
        f'<div style="font-size:14px;font-weight:700;color:#0F172A">{nom}</div>'
        f'<div style="font-size:12px;color:#64748B;margin-top:1px">{sous_titre}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _tip(texte, couleur="#1D4ED8", fond="#EFF6FF"):
    """Encadré conseil — barre colorée gauche, sans emoji."""
    st.markdown(
        f'<div style="border-left:3px solid {couleur};background:{fond};'
        f'border-radius:0 8px 8px 0;padding:10px 14px;margin:8px 0">'
        f'<span style="font-size:13px;color:#1E293B;line-height:1.6">{texte}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )




def _glossaire_terme(terme, formule, definition, benchmark=""):
    bench_html = (
        f'<div style="margin-top:6px;font-size:12px;color:#059669;'
        f'background:#F0FDF4;border-radius:6px;padding:6px 10px">'
        f'Benchmark — {benchmark}</div>'
    ) if benchmark else ""
    st.markdown(
        f'<div style="padding:14px 0;border-bottom:1px solid #F1F5F9">'
        f'<div style="display:flex;align-items:baseline;gap:10px;margin-bottom:6px">'
        f'<span style="font-size:14px;font-weight:700;color:#0F172A">{terme}</span>'
        f'<code style="font-size:12px;background:#F1F5F9;color:#7C3AED;'
        f'padding:2px 8px;border-radius:4px">{formule}</code>'
        f'</div>'
        f'<div style="font-size:13px;color:#374151;line-height:1.6">{definition}</div>'
        f'{bench_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _kpi_doc(nom, calcul, interpretation, seuils=None):
    seuils_html = ""
    if seuils:
        items = "".join(
            f'<div style="display:flex;gap:8px;align-items:center;margin-top:4px">'
            f'<div style="width:10px;height:10px;border-radius:50%;'
            f'background:{c};flex-shrink:0"></div>'
            f'<span style="font-size:12px;color:#374151">{label}</span></div>'
            for c, label in seuils
        )
        seuils_html = (
            f'<div style="margin-top:8px;padding:10px 12px;background:#F8FAFC;'
            f'border-radius:6px">{items}</div>'
        )
    st.markdown(
        f'<div style="padding:12px 0;border-bottom:1px solid #F1F5F9">'
        f'<span style="font-size:13px;font-weight:700;color:#0F172A">{nom}</span>'
        f'<code style="font-size:11px;background:#F1F5F9;color:#7C3AED;'
        f'padding:2px 7px;border-radius:4px;margin-left:8px">{calcul}</code>'
        f'<div style="font-size:13px;color:#374151;line-height:1.6;margin-top:4px">'
        f'{interpretation}</div>'
        f'{seuils_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Vue principale ────────────────────────────────────────────────────────────

def render(loader=None):

    # Bannière intro — sans emoji
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1E3A5F 0%,#1D4ED8 100%);'
        'border-radius:12px;padding:24px 28px;margin-bottom:20px">'
        '<div style="font-size:11px;font-weight:700;color:#93C5FD;'
        'text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px">'
        'FloMind · Dashboard Trésorerie v4.1</div>'
        '<div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.3;'
        'margin-bottom:10px">'
        'Pilotez 30 sites en 20 minutes,<br>pas en une journée de consolidation.</div>'
        '<div style="font-size:13px;color:#BAD0F5;line-height:1.6">'
        'Ce dashboard répond à une question centrale : <strong style="color:#FFFFFF">'
        "où est l'argent du réseau, qui le doit, qui va être payé, "
        'et que va-t-il se passer dans les 6 prochains mois ?</strong><br>'
        'Deux usages : présentation prospect (12–15 min) et pilotage mensuel opérationnel.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs([
        "Les 7 vues",
        "KPIs & Méthodes",
        "Glossaire",
    ])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — LES 7 VUES
    # ══════════════════════════════════════════════════════════════
    with tab1:

        st.markdown(
            '<div style="font-size:13px;color:#475569;margin-bottom:16px">'
            'Navigation via la barre latérale gauche. '
            'Le <strong>slider de période</strong> propage le mois sélectionné '
            'à toutes les vues simultanément.</div>',
            unsafe_allow_html=True,
        )

        _vue_badge("Tour de contrôle", "#1D4ED8",
                   "Vision instantanée · Soldes · Runway · Heatmap 28 mois")
        with st.container(border=True):
            st.markdown(
                "**Ce que vous voyez en premier** — 6 KPIs header (solde réseau, "
                "flux net, couverture CT, point mort, EBE cash, BFR), "
                "tableau des 30 sites classés par niveau de risque, "
                "puis heatmap sites × mois sur 28 mois."
            )
            c1, c2 = st.columns(2)
            with c1:
                _tip("Le <strong>runway</strong> = Solde / Décaissements moyens. "
                     "Critique &lt; 1 mois · Vigilance 1–3 mois · Normal &gt; 3 mois.")
            with c2:
                _tip("La <strong>heatmap</strong> révèle les patterns structurels : "
                     "un site rouge en permanence = problème de modèle économique, "
                     "pas un accident ponctuel.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _vue_badge("Flux de trésorerie", "#7C3AED",
                   "Waterfall mensuel · Évolution 28 mois · Comparaison N vs N-1")
        with st.container(border=True):
            st.markdown(
                "**Waterfall** — Décomposition des 11 postes du mois courant : "
                "barres vertes (entrées), rouges (sorties), bleue finale (flux net). "
                "**Évolution 28 mois** — Barres empilées par catégorie + courbe flux net. "
                "**Analyse annuelle** — Comparaison N vs N-1 dynamique selon le mois sélectionné."
            )
            _tip("Sélecteur en haut : basculez entre réseau consolidé et un site "
                 "spécifique pour diagnostiquer l'origine d'une anomalie.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _vue_badge("BFR", "#059669",
                   "DSO · DPO · DIO · CCC · Aging clients · Stock · Fournisseurs")
        with st.container(border=True):
            st.markdown(
                "**Ratios DSO/DPO** avec benchmarks négoce et évolution mensuelle. "
                "**Aging clients** en 5 tranches (non échu → +90 jours). "
                "**Stock ABC** — valeur et rotation par catégorie. "
                "**Fournisseurs** — encours, retards, top créanciers."
            )
            c1, c2 = st.columns(2)
            with c1:
                _tip("Pour 45 M€ de CA, chaque journée de DSO = "
                     "<strong>125 k€ immobilisés</strong>.")
            with c2:
                _tip("Stock catégorie C avec DIO &gt; 90 jours = dormant "
                     "— décision de déstockage.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _vue_badge("Alertes réseau", "#DC2626",
                   "Score de risque 0–100 · Feed chronologique · Priorités d'action")
        with st.container(border=True):
            st.markdown(
                "**Score de risque** — Agrégation logarithmique par site : "
                "chaque alerte critique +20 pts, vigilance +5 pts. "
                "**Feed d'alertes** filtrable par type, site, gravité. "
                "Chaque alerte indique le problème et la valeur chiffrée."
            )
            _tip(
                "<strong>Vue la plus percutante en réunion prospect.</strong> "
                "Question-clé : <em>\"Vos 3 sites avec le score le plus élevé — "
                "vos équipes le voient-elles aujourd'hui ?\"</em>",
                fond="#FEF2F2", couleur="#DC2626",
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _vue_badge("Budget & Pilotage", "#D97706",
                   "Budget vs Réalisé YTD · Écarts par poste · Concentration clients")
        with st.container(border=True):
            st.markdown(
                "**KPIs synthétiques** — taux de réalisation CA, écart flux YTD, "
                "nombre de postes défavorables. "
                "**Graphiques** — écarts par poste + mensuel réalisé vs budget. "
                "**Tableau** filtrable et exportable CSV. "
                "**Concentration clients** — top 1/3/10 par site + indice HHI."
            )
            _tip(
                "Un client &gt; 30% du CA d'un site = risque systémique. "
                "HHI &gt; 0,18 = marché concentré (seuil antitrust EU).",
                fond="#FFFBEB", couleur="#D97706",
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _vue_badge("Prévisionnel", "#0891B2",
                   "3 scénarios · IC 80% · Ligne budget · Décomposition par composante")
        with st.container(border=True):
            st.markdown(
                "**3 scénarios** sur 3–12 mois avec intervalle de confiance 80% : "
                "base (WLS historique), optimiste (Δ encaissements, ΔDSO), pessimiste. "
                "**Ligne budget cible** si budget_treso.xlsx présent — répond à : "
                "*\"Mon forecast atteint-il mon budget ?\"* "
                "**Décomposition** — contribution de chaque poste au flux prévisionnel."
            )
            c1, c2 = st.columns(2)
            with c1:
                _tip(
                    "<strong>vs Agicap / Fygr</strong> — ces outils extrapolent le solde global. "
                    "Ce forecast raisonne composante par composante (WLS + règles fiscales). "
                    "Défendable devant un CDG expérimenté."
                )
            with c2:
                _tip("Sliders en temps réel : +10% encaissements = effet recouvrement. "
                     "DSO +12j = ralentissement client.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _vue_badge("Guide d'utilisation", "#64748B",
                   "Documentation · KPIs & Méthodes · Glossaire")
        with st.container(border=True):
            st.markdown(
                "Cette page. "
                "(12–15 min), la documentation des KPIs et méthodes, "
                "le glossaire complet."
            )

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — KPIs & MÉTHODES
    # ══════════════════════════════════════════════════════════════
    with tab2:

        c1, c2 = st.columns(2, gap="large")

        with c1:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:12px;font-weight:700;color:#0F172A;'
                    'text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">'
                    'KPIs Header</div>',
                    unsafe_allow_html=True,
                )
                _kpi_doc(
                    "Solde réseau", "Σ soldes fin de mois",
                    "Somme consolidée des soldes bancaires de tous les sites actifs. "
                    "Affiché avec delta M-1 et comptage sites négatifs/critiques.",
                    [("#059669", "Positif et en hausse"),
                     ("#D97706", "Positif mais en baisse"),
                     ("#DC2626", "Négatif ou sites critiques")]
                )
                _kpi_doc(
                    "Couverture CT",
                    "Solde / (Dettes four. + Mensualité)",
                    "Ratio de solvabilité immédiate. Calculé depuis la balance "
                    "fournisseurs réelle + mensualité d'emprunt estimée.",
                    [("#059669", "≥ 1,5x — confortable"),
                     ("#D97706", "1,0–1,5x — acceptable"),
                     ("#DC2626", "< 1,0x — risque de défaut CT")]
                )
                _kpi_doc(
                    "Point mort trésorerie",
                    "(CF + 80% MS) / Taux MCV",
                    "CA HT mensuel minimum pour flux net ≥ 0. "
                    "Marge sur point mort = (CA mensuel − PM) / PM × 100.",
                )
                _kpi_doc(
                    "EBE cash YTD",
                    "Flux exploit. YTD / CA YTD × 100",
                    "EBE calculé sur les flux réels (hors comptabilité d'engagement, "
                    "hors CAPEX, financement, fiscal).",
                    [("#059669", "≥ 7% — excellent négoce"),
                     ("#D97706", "3–7% — benchmark sectoriel"),
                     ("#DC2626", "< 3% — sous le plancher")]
                )
                _kpi_doc(
                    "Score de risque",
                    "Log-normalisé 0–100",
                    "Critique +20 pts · Vigilance +5 pts · normalisation log "
                    "pour éviter la saturation sur sites multi-alertes.",
                    [("#059669", "0–19 : nominale"),
                     ("#D97706", "20–49 : surveillance"),
                     ("#DC2626", "50–69 : escalade · > 70 : crise")]
                )

        with c2:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:12px;font-weight:700;color:#0F172A;'
                    'text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">'
                    'Méthodes Forecast</div>',
                    unsafe_allow_html=True,
                )
                _kpi_doc(
                    "WLS Encaissements",
                    "Σ wᵢ(yᵢ−ŷᵢ)² → min, wᵢ=exp(i/n)",
                    "Weighted Least Squares à pondération exponentielle. "
                    "Correction saisonnalité N-1. "
                    "IC 80% sur résidus historiques (z=1,28), croissant avec l'horizon.",
                )
                _kpi_doc(
                    "Fournisseurs forecast",
                    "CA prév × (1 − tx_marque)",
                    "Paiements déduits du CA prévisionnel via le taux de marque "
                    "estimé sur l'historique. Plus précis que WLS car corrélé au CA.",
                )
                _kpi_doc(
                    "TVA nette",
                    "CA × 20%, décalée 1 mois",
                    "Règle fiscale CA3 : TVA collectée mois M décaissée en M+1. "
                    "Taux 20% — à ajuster si mix produit inclut taux réduits.",
                )
                _kpi_doc(
                    "CAPEX forecast",
                    "CA × 1,5% × poids_mois normalisé",
                    "Pattern saisonnier : concentration T1 (fév/mars) et T3 (août/sept). "
                    "Poids normalisés → total annuel = 1,5% CA exact.",
                )
                _kpi_doc(
                    "CCR",
                    "Flux exploit. / |EBE cash|",
                    "Cash Conversion Ratio — calculé sur flux opérationnel uniquement "
                    "(hors CAPEX, financement, fiscal). "
                    "CCR > 1 : BFR qui se contracte.",
                    [("#059669", "0,5–0,8 — sain pour le négoce"),
                     ("#D97706", "0,3–0,5 — à surveiller"),
                     ("#DC2626", "< 0,3 ou > 1,2 — anomalie")]
                )

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — GLOSSAIRE
    # ══════════════════════════════════════════════════════════════
    with tab3:

        cg, cd = st.columns(2, gap="large")

        with cg:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:12px;font-weight:700;color:#0F172A;'
                    'text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">'
                    'Ratios BFR & Trésorerie</div>',
                    unsafe_allow_html=True,
                )
                _glossaire_terme("DSO", "Créances / CA × 30",
                    "Days Sales Outstanding — délai moyen entre facturation et encaissement. "
                    "Chaque journée = CA/360 € immobilisés.",
                    "Négoce B2B France : 45–55 jours")
                _glossaire_terme("DPO", "Dettes four. / Achats × 30",
                    "Days Payable Outstanding — délai moyen de paiement fournisseur. "
                    "Plafonné à 60 jours par la LME 2008.",
                    "30–45 jours")
                _glossaire_terme("DIO", "Stock / Achats × 30",
                    "Days Inventory Outstanding — durée moyenne de rotation des stocks. "
                    "DIO > 90j sur une catégorie = stock dormant.",
                    "Négoce : 20–35 jours")
                _glossaire_terme("CCC", "DSO + DIO − DPO",
                    "Cash Conversion Cycle — durée entre décaissement des achats "
                    "et encaissement des ventes. Négatif = position idéale.",
                    "Négoce : 40–70 jours")
                _glossaire_terme("BFR", "Créances + Stocks − Dettes four.",
                    "Besoin en Fonds de Roulement — montant à financer sur fonds propres "
                    "ou dettes bancaires pour assurer le cycle d'exploitation.")
                _glossaire_terme("Runway", "Solde / Déc. moyens mensuels",
                    "Nombre de mois de trésorerie disponible sans nouveau flux entrant. "
                    "< 1 mois : action immédiate. 1–3 mois : surveillance active.")
                _glossaire_terme("Couverture CT", "Solde / (Dettes + Mensualité emprunt)",
                    "Ratio de liquidité immédiate. Mesure la capacité à honorer "
                    "les obligations CT avec la trésorerie bancaire disponible.")

        with cd:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:12px;font-weight:700;color:#0F172A;'
                    'text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">'
                    'Finance & Méthodes</div>',
                    unsafe_allow_html=True,
                )
                _glossaire_terme("EBE cash", "Encaissements − Déc. exploitation",
                    "Excédent Brut d'Exploitation calculé sur les flux réels. "
                    "Hors CAPEX, financement, fiscal.",
                    "Négoce : 3–7% du CA")
                _glossaire_terme("CCR", "Flux exploit. / |EBE cash|",
                    "Cash Conversion Ratio — part de l'EBE cash transformée "
                    "en flux net opérationnel (périmètre exploitation uniquement).",
                    "Valeur saine négoce : 0,5–0,8")
                _glossaire_terme("HHI", "Σ (part_client_i)²",
                    "Herfindahl-Hirschman Index — mesure la concentration "
                    "d'un portefeuille clients. 0 = atomisé · 1 = monopole.",
                    "Seuil antitrust EU : 0,18")
                _glossaire_terme("WLS", "Σ wᵢ(yᵢ−ŷᵢ)² → min",
                    "Weighted Least Squares — régression pondérée. "
                    "Poids exponentiels : les observations récentes comptent davantage.")
                _glossaire_terme("IC 80%", "ŷ ± 1,28 × σ_résidus",
                    "Intervalle de confiance à 80% basé sur les résidus historiques "
                    "du modèle WLS. S'élargit avec l'horizon de prévision.")
                _glossaire_terme("LME", "Loi 2008-776 du 4 août 2008",
                    "Loi de Modernisation de l'Économie — plafonne les délais de "
                    "paiement à 60 jours calendaires ou 45 jours fin de mois. "
                    "Pénalité légale : taux BCE + 10 pts.")
                _glossaire_terme("Stock ABC", "A : top 20% réf. = 80% CA",
                    "Classement Pareto : A (80% du CA) · B (15%) · C (5%). "
                    "Catégorie C avec DIO > 90j = candidate au déstockage.")

    # Footer
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="border-top:1px solid #E2E8F0;padding-top:12px;'
        'display:flex;justify-content:space-between;align-items:center">'
        '<span style="font-size:12px;color:#94A3B8">'
        'FloMind Consulting · CDG × Data × IA pour PME</span>'
        '<span style="font-size:12px;color:#94A3B8">'
        'v4.1 · Données synthétiques — usage démo uniquement</span>'
        '</div>',
        unsafe_allow_html=True,
    )

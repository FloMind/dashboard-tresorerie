# -*- coding: utf-8 -*-
"""components/aide.py — Aide contextuelle inline par vue.

Pattern : expander collapsé en bas de chaque vue.
Contenu : 3-5 blocs ciblés, formules, seuils RAG, lecture opérationnelle.
Aucun emoji — cohérence avec la charte visuelle.
"""
import streamlit as st


# ── CSS local partagé ─────────────────────────────────────────────────────────
_CSS = """
<style>
.aide-bloc {
    margin-bottom: 14px;
}
.aide-titre {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: #334155;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid #F1F5F9;
}
.aide-texte {
    font-size: 13px;
    color: #374151;
    line-height: 1.65;
    margin-bottom: 4px;
}
.aide-formule {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    background: #F1F5F9;
    color: #7C3AED;
    padding: 6px 12px;
    border-radius: 6px;
    margin: 6px 0;
    display: inline-block;
}
.aide-seuils {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 6px;
}
.aide-seuil {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #374151;
}
.aide-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
</style>
"""


def _bloc(titre: str, *lignes: str) -> str:
    contenu = "".join(f'<div class="aide-texte">{l}</div>' for l in lignes)
    return (
        f'<div class="aide-bloc">'
        f'<div class="aide-titre">{titre}</div>'
        f'{contenu}'
        f'</div>'
    )


def _formule(f: str) -> str:
    return f'<div class="aide-formule">{f}</div>'


def _seuils(*items) -> str:
    """items = liste de (couleur_hex, texte)"""
    dots = "".join(
        f'<div class="aide-seuil">'
        f'<div class="aide-dot" style="background:{c}"></div>'
        f'{t}'
        f'</div>'
        for c, t in items
    )
    return f'<div class="aide-seuils">{dots}</div>'


# ── Expanders par vue ─────────────────────────────────────────────────────────

def _aide_position() -> None:
    with st.expander("Comment lire cette vue"):
        st.markdown(_CSS, unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown(
                _bloc("Tableau des sites",
                      "Classement du plus risqué au plus sain. "
                      "La couleur de fond suit le niveau RAG (rouge / orange / vert). "
                      "Cliquez sur un site pour voir son détail dans les autres vues.")
                + _bloc("Runway",
                        "Nombre de mois pendant lesquels le site peut fonctionner "
                        "sans nouveau flux entrant.",
                        _formule("Runway = Solde fin de mois / Décaissements moyens 3 derniers mois"),
                        _seuils(
                            ("#DC2626", "Critique — runway < 1 mois"),
                            ("#D97706", "Vigilance — runway 1 à 3 mois"),
                            ("#059669", "Normal — runway > 3 mois"),
                        ))
                , unsafe_allow_html=True)
        with col2:
            st.markdown(
                _bloc("Heatmap 28 mois",
                      "Chaque cellule = solde fin de mois d'un site. "
                      "Rouge foncé = solde très négatif · Vert foncé = solde élevé. "
                      "Un site rouge sur plusieurs mois consécutifs = problème structurel, "
                      "pas un accident ponctuel.",
                      "Un site qui vire au rouge uniquement en décembre / juillet = "
                      "saisonnalité — comparer avec l'année précédente sur la même colonne.")
                + _bloc("Actions prioritaires",
                        "Site critique (rouge) : virement DG ou activation ligne de crédit. "
                        "Site en vigilance (orange) : relance recouvrement clients, "
                        "négociation décalage fournisseur. "
                        "Toujours agir avant la clôture du mois.")
                , unsafe_allow_html=True)


def _aide_flux() -> None:
    with st.expander("Comment lire cette vue"):
        st.markdown(_CSS, unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown(
                _bloc("Waterfall mensuel",
                      "Chaque barre représente un poste de flux sur le mois courant. "
                      "Barres vertes = entrées (encaissements). "
                      "Barres rouges = sorties (décaissements). "
                      "Barre bleue finale = flux net = somme de toutes les barres.",
                      "Si la barre bleue est positive : le mois génère du cash. "
                      "Si elle est négative : le mois consomme de la trésorerie. "
                      "La hauteur relative des barres montre les postes dominants.")
                + _bloc("Sélecteur site / réseau",
                        "Par défaut : réseau consolidé (30 sites). "
                        "Utilisez le sélecteur en haut pour isoler un site spécifique "
                        "et diagnostiquer l'origine d'une anomalie sur le réseau.")
                , unsafe_allow_html=True)
        with col2:
            st.markdown(
                _bloc("Évolution 28 mois",
                      "Barres empilées par catégorie : "
                      "vert (encaissements), rouge (exploitation), orange (fiscal), "
                      "violet (investissement), bleu (financement). "
                      "La courbe noire = flux net mensuel.",
                      "Tendance à surveiller : si les barres rouges grandissent "
                      "plus vite que les barres vertes, les charges absorbent "
                      "une part croissante des encaissements.")
                + _bloc("Comparaison N vs N-1",
                        "Variation en % par catégorie entre l'année courante et la précédente. "
                        "Positif sur les encaissements = bonne performance. "
                        "Positif sur les décaissements = dérive des charges. "
                        "Les années sont calculées dynamiquement depuis le mois sélectionné.")
                , unsafe_allow_html=True)


def _aide_bfr() -> None:
    with st.expander("Comment lire cette vue"):
        st.markdown(_CSS, unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown(
                _bloc("Ratios de rotation",
                      "Les 4 ratios mesurent la vitesse à laquelle le cycle "
                      "exploitation génère ou consomme du cash.",
                      _formule("DSO = Encours clients / CA × 30 jours"),
                      _formule("DPO = Encours fournisseurs / Achats × 30 jours"),
                      _formule("DIO = Valeur stock / Achats × 30 jours"),
                      _formule("CCC = DSO + DIO − DPO"),
                      _seuils(
                          ("#059669", "DSO < 45j · DPO 30–45j · DIO < 30j"),
                          ("#D97706", "DSO 45–55j · DPO > 45j · DIO 30–60j"),
                          ("#DC2626", "DSO > 55j · DPO > 60j (LME) · DIO > 60j"),
                      ))
                + _bloc("Lecture du CCC",
                        "CCC négatif = vous êtes payé avant de payer vos fournisseurs "
                        "— position idéale (ex. grande distribution). "
                        "Benchmark négoce B2B France : 40–70 jours. "
                        "Chaque journée de DSO supplémentaire = CA/360 € immobilisés.")
                , unsafe_allow_html=True)
        with col2:
            st.markdown(
                _bloc("Aging clients",
                      "Répartition des créances en 5 tranches d'ancienneté. "
                      "Non échu = factures dans les délais. "
                      "0–30j, 30–60j, 60–90j, +90j = retards par gravité croissante. "
                      "Un encours > 90 jours sans provision = risque de perte.",
                      "Action : toute tranche > 60 jours sans relance active "
                      "doit être escaladée. La LME autorise des pénalités légales "
                      "à partir de 60 jours de retard.")
                + _bloc("Stock ABC",
                        "Catégorie A = 20% des références = 80% du CA. "
                        "Catégorie B = 30% des références = 15% du CA. "
                        "Catégorie C = 50% des références = 5% du CA. "
                        "Un DIO > 90 jours sur une catégorie C = stock dormant. "
                        "Décision recommandée : déstockage ou markdown.")
                + _bloc("Fournisseurs",
                        "Retard DPO = délai réel > délai contractuel. "
                        "Causes possibles : tension trésorerie ou gestion volontaire du BFR. "
                        "Risque : pénalités de retard + blocage livraisons.")
                , unsafe_allow_html=True)


def _aide_alertes() -> None:
    with st.expander("Comment lire cette vue"):
        st.markdown(_CSS, unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown(
                _bloc("Score de risque 0–100",
                      "Agrégation logarithmique de toutes les alertes du site.",
                      _formule("Score = f(nb_critiques × 20 + nb_vigilances × 5)"),
                      "La normalisation logarithmique évite la saturation : "
                      "un site avec 10 alertes critiques ne score pas 200/100. "
                      "Le score mesure la densité de risque, pas seulement le volume.",
                      _seuils(
                          ("#059669", "0–19 : situation nominale"),
                          ("#D97706", "20–49 : surveillance active"),
                          ("#DC2626", "50–69 : escalade recommandée"),
                          ("#7C3AED", "> 70 : crise — action immédiate"),
                      ))
                , unsafe_allow_html=True)
        with col2:
            st.markdown(
                _bloc("Types d'alertes",
                      "Trésorerie : solde négatif, runway critique, couverture CT < 1. "
                      "Clients : retard encaissement, client dominant, encours > 90j. "
                      "Fournisseurs : DPO > délai LME, fournisseur stratégique en retard. "
                      "Stock : DIO excessif, rupture catégorie A.")
                + _bloc("Utilisation en réunion",
                        "Classez les sites par score décroissant. "
                        "Posez la question : les 3 premiers sites — "
                        "vos équipes terrain ont-elles un plan d'action cette semaine ? "
                        "Le feed d'alertes est filtrable par type et par site "
                        "pour isoler une problématique spécifique.")
                , unsafe_allow_html=True)


def _aide_budget() -> None:
    with st.expander("Comment lire cette vue"):
        st.markdown(_CSS, unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown(
                _bloc("Taux de réalisation CA",
                      "Mesure si le chiffre d'affaires encaissé atteint l'objectif budgété "
                      "sur la période YTD (du 1er janvier au mois courant).",
                      _formule("Taux = CA réalisé YTD / CA budget YTD × 100"),
                      _seuils(
                          ("#059669", "> 100% — dépassement d'objectif"),
                          ("#D97706", "95–100% — légèrement sous objectif"),
                          ("#DC2626", "< 95% — écart significatif à analyser"),
                      ),
                      "Attention : un taux < 100% peut venir d'un retard "
                      "d'encaissement (recouvrement) et non d'une baisse d'activité. "
                      "Comparer avec le niveau de facturation réel.")
                , unsafe_allow_html=True)
        with col2:
            st.markdown(
                _bloc("Écarts par poste",
                      "Favorable = le réalisé est meilleur que le budget : "
                      "plus encaissé ou moins dépensé que prévu. "
                      "Défavorable = réalisé moins bon que le budget. "
                      "L'écart en valeur absolue prime sur l'écart en pourcentage "
                      "pour prioriser les actions.")
                + _bloc("Concentration clients (HHI)",
                        "L'indice Herfindahl-Hirschman mesure la concentration "
                        "du portefeuille clients.",
                        _formule("HHI = Σ (part de chaque client)²"),
                        _seuils(
                            ("#059669", "HHI < 0,10 — portefeuille diversifié"),
                            ("#D97706", "HHI 0,10–0,18 — concentration modérée"),
                            ("#DC2626", "HHI > 0,18 — marché concentré (seuil EU)"),
                        ),
                        "Top 1 client > 30% du CA d'un site = risque systémique : "
                        "un retard ou une défaillance de ce client impacte "
                        "directement la trésorerie du site.")
                , unsafe_allow_html=True)


def _aide_previsionnel() -> None:
    with st.expander("Comment lire cette vue"):
        st.markdown(_CSS, unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown(
                _bloc("Les 3 scénarios",
                      "Base : prolongement de la tendance actuelle (WLS sur l'historique). "
                      "Optimiste : meilleur recouvrement clients + DSO raccourci. "
                      "Pessimiste : ralentissement encaissements + DSO allongé. "
                      "Les trois scénarios partent du même solde de départ (mois courant).")
                + _bloc("Intervalle de confiance 80%",
                        "La zone grisée autour du scénario base représente "
                        "la plage dans laquelle le solde réel a 80% de chances de se trouver. "
                        "Basé sur les résidus historiques du modèle WLS (z = 1,28). "
                        "L'intervalle s'élargit avec l'horizon : moins de certitude à 12 mois "
                        "qu'à 3 mois.")
                , unsafe_allow_html=True)
        with col2:
            st.markdown(
                _bloc("Utiliser les sliders",
                      "Chaque slider modifie un paramètre du scénario optimiste ou pessimiste "
                      "et recalcule les courbes en temps réel. "
                      "Δ encaissements +10% = effet d'une campagne de recouvrement. "
                      "ΔDSO +12 jours = ralentissement des paiements clients. "
                      "Utilisez ces simulations pour quantifier l'impact d'une décision "
                      "avant de l'engager.")
                + _bloc("Ligne budget cible",
                        "La ligne pointillée représente l'objectif de solde "
                        "issu du fichier budget (budget_treso.xlsx). "
                        "Si le scénario base est en dessous de cette ligne, "
                        "le budget ne sera pas atteint sans action corrective. "
                        "Si le scénario optimiste rejoint la ligne, "
                        "le levier est le recouvrement.")
                + _bloc("Méthode de forecast",
                        "Ce forecast n'extrapole pas le solde global — "
                        "il raisonne poste par poste : "
                        "encaissements (WLS + saisonnalité N-1), "
                        "fournisseurs (déduit du CA × taux de marque), "
                        "TVA (règle CA3 décalée d'un mois), "
                        "loyers et emprunt (montants fixes contractuels).")
                , unsafe_allow_html=True)


# ── Point d'entrée unique ─────────────────────────────────────────────────────

def aide_expander(vue: str) -> None:
    """Appel unique depuis chaque view.render() en toute fin."""
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    dispatch = {
        "position":    _aide_position,
        "flux":        _aide_flux,
        "bfr":         _aide_bfr,
        "alertes":     _aide_alertes,
        "budget":      _aide_budget,
        "previsionnel": _aide_previsionnel,
    }
    fn = dispatch.get(vue)
    if fn:
        fn()

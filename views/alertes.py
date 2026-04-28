# -*- coding: utf-8 -*-
"""views/alertes.py"""
import streamlit as st
from components.styles import section, CARD_COLORS, alert_counters, alert_item
from components.aide import aide_expander
import plotly.graph_objects as go
from components.charts import chart_score_risque
from components.formatters import fmt_eur

TYPE_LABELS = {
    "tresorerie": "Tresorerie",
    "client":     "Client",
    "stock":      "Stock",
    "fournisseur":"Fournisseur",
}

ACTIONS = {
    ("tresorerie", "rouge"):     "Virement DG ou activation ligne de credit",
    ("tresorerie", "orange"):    "Accelerer recouvrement clients en retard",
    ("client",     "rouge"):     "Mise en demeure ou passage en contentieux",
    ("client",     "orange"):    "Relance telephonique prioritaire",
    ("stock",      "rouge"):     "Reapprovisionnement d'urgence fournisseur",
    ("stock",      "orange"):    "Revue avec responsable logistique",
    ("fournisseur","rouge"):     "Negociation delai ou paiement partiel immediat",
    ("fournisseur","orange"):    "Planifier reglement sous 72h",
}


def _action_card(a) -> None:
    type_label = TYPE_LABELS.get(a.type, a.type)
    action = ACTIONS.get((a.type, a.gravite), "A traiter en priorite")
    val = f" — {a.valeur:,.0f} €" if (a.valeur and abs(a.valeur) > 100) else ""
    st.markdown(
        f'<div style="display:flex;align-items:flex-start;gap:14px;'
        f'padding:11px 14px;background:#FFF8F8;border-radius:8px;'
        f'border-left:3px solid #EF4444;margin-bottom:6px">'
        f'<div style="flex:1;min-width:0">'
        f'<div style="font-size:11px;font-weight:700;color:#1E293B;margin-bottom:3px">'
        f'{a.site_id} — {a.site_nom}'
        f'<span style="font-weight:400;color:#94A3B8;margin-left:8px">{type_label}</span>'
        f'</div>'
        f'<div style="font-size:12px;color:#475569;margin-bottom:5px;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
        f'{a.message}{val}</div>'
        f'<div style="font-size:11px;font-weight:600;color:#1D4ED8">'
        f'&rarr;&nbsp;{action}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render(loader) -> None:
    with st.container(border=True):
        fc1, fc2 = st.columns(2)
        sites    = ["Reseau complet"] + sorted(
            loader.soldes_raw["site_nom"].unique().tolist()
        )
        site_sel = fc1.selectbox("Perimetre", sites, key="alertes_site")
        site_id  = None
        if site_sel != "Reseau complet":
            site_id = (loader.soldes_raw
                       .set_index("site_nom")["site_id"]
                       .to_dict().get(site_sel))

    alertes  = loader.alertes(site_id=site_id)
    score_df = loader.score_risque()

    nb_rouge  = sum(1 for a in alertes if a.gravite == "rouge")
    nb_orange = sum(1 for a in alertes if a.gravite == "orange")

    alert_counters(
        rouge=nb_rouge, orange=nb_orange,
        gris=int((score_df["score_risque"] > 0).sum()) - nb_rouge - nb_orange,
        labels=("Critiques", "Vigilance", "Surveillance"),
    )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "Actions immediates",
        "Score de risque",
        "Toutes les alertes",
    ])

    with tab1:
        top5 = [a for a in alertes if a.gravite == "rouge"][:5]
        if not top5:
            st.success("Aucune situation critique ce mois sur ce perimetre.")
        else:
            with st.container(border=True):
                st.caption(
                    f"{nb_rouge} alerte(s) critique(s) — les {len(top5)} plus prioritaires"
                )
                for a in top5:
                    _action_card(a)

        if nb_orange > 0:
            with st.expander(f"{nb_orange} situations en vigilance"):
                for a in [a for a in alertes if a.gravite == "orange"][:15]:
                    _action_card(a)

    with tab2:
        col_bar, col_pie = st.columns([3, 2], gap="medium")
        with col_bar:
            with st.container(border=True):
                st.plotly_chart(chart_score_risque(score_df),
                                use_container_width=True, config={"displayModeBar": False})
        with col_pie:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:12px;font-weight:600;color:#374151;'
                    'text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">'
                    'Repartition par type</div>', unsafe_allow_html=True)
                from collections import Counter
                dist = Counter(a.type for a in alertes)
                palette = {
                    "tresorerie": "#1D4ED8", "client":      "#B91C1C",
                    "stock":      "#B45309", "fournisseur": "#6D28D9",
                }
                fig_d = go.Figure(go.Pie(
                    labels=[TYPE_LABELS.get(t, t) for t in dist.keys()],
                    values=list(dist.values()),
                    hole=0.55,
                    marker_colors=[palette.get(t,"#6B7280") for t in dist.keys()],
                    textinfo="label+value", textfont=dict(size=12),
                    hovertemplate="%{label}<br><b>%{value}</b> alertes<extra></extra>",
                ))
                fig_d.update_layout(
                    height=260, showlegend=False,
                    margin=dict(l=0, r=0, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, system-ui, sans-serif", size=12))
                st.plotly_chart(fig_d, use_container_width=True,
                                config={"displayModeBar": False})
                for t, n in dist.items():
                    c = palette.get(t, "#6B7280")
                    st.markdown(
                        f'<div style="font-size:12px;margin:4px 0">'
                        f'<span style="display:inline-block;width:8px;height:8px;'
                        f'border-radius:50%;background:{c};margin-right:6px"></span>'
                        f'{TYPE_LABELS.get(t,t)} — <b>{n}</b></div>',
                        unsafe_allow_html=True)

    with tab3:
        with st.container(border=True):
            fc1, fc2, _ = st.columns([1, 1, 2])
            f_grav = fc1.selectbox("Gravite",
                                   ["Toutes", "Critique (rouge)", "Vigilance (orange)"],
                                   key="alertes_grav")
            f_type = fc2.selectbox("Type",
                                   ["Tous"] + [TYPE_LABELS[t] for t in TYPE_LABELS],
                                   key="alertes_type")

        af = alertes
        if "rouge"  in f_grav: af = [a for a in af if a.gravite == "rouge"]
        elif "orange" in f_grav: af = [a for a in af if a.gravite == "orange"]
        if f_type != "Tous":
            inv = {v: k for k, v in TYPE_LABELS.items()}
            t   = inv.get(f_type, "")
            af  = [a for a in af if a.type == t]

        show_all = st.session_state.get("alertes_show_all", False)
        limit    = len(af) if show_all else 12
        for a in af[:limit]:
            val = f"{a.valeur:,.0f} €" if (a.valeur and a.valeur > 100) else ""
            alert_item(
                gravite=a.gravite,
                type_label=TYPE_LABELS.get(a.type, a.type),
                site=f"{a.site_id} {a.site_nom}",
                message=a.message,
                valeur=val,
            )
        if len(af) > 12 and not show_all:
            if st.button(f"Voir les {len(af) - 12} alertes restantes", key="alertes_voir_plus"):
                st.session_state["alertes_show_all"] = True
                st.rerun()
        elif show_all and len(af) > 12:
            if st.button("Reduire", key="alertes_reduire"):
                st.session_state["alertes_show_all"] = False
                st.rerun()

    aide_expander("alertes")

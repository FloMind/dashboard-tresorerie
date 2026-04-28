# -*- coding: utf-8 -*-
"""components/charts.py — Graphiques Plotly FloMind Tresorerie v4.1
Refonte visuelle complete :
    - Formatage Y-axis en M€ / k€ (fini le 15,000,000 €)
    - Titre + legende non superpooses (legende en dessous)
    - chart_forecast : separateur reel/previsionnel, IC realiste,
      annotations fin de courbe, legende en bas
    - Palette uniformisee, typographie Inter
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── Palette ─────────────────────────────────────────────────────────────────
C = {
    "bleu":   "#1565C0",
    "bleu_l": "#3B82F6",
    "vert":   "#0D6E4E",
    "vert_l": "#10B981",
    "rouge":  "#B91C1C",
    "rouge_l":"#EF4444",
    "orange": "#C05621",
    "violet": "#6D28D9",
    "gris":   "#475569",
    "grille": "#F1F5F9",
    "fond":   "rgba(0,0,0,0)",
    "texte":  "#1E293B",
    "muted":  "#94A3B8",
    "zero":   "#CBD5E1",
    "sep":    "#E2E8F0",
}
CAT = {
    "ENCAISSEMENTS":         C["vert"],
    "DECAISSEMENTS_EXPLOIT": C["rouge"],
    "FISCAL":                C["orange"],
    "INVESTISSEMENT":        C["violet"],
    "FINANCEMENT":           C["bleu"],
}
FONT = "Inter, system-ui, -apple-system, sans-serif"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fmt_y(val: float) -> str:
    """Formate une valeur Y pour l'affichage (M€ / k€)."""
    if abs(val) >= 1_000_000:
        return f"{val/1e6:.1f} M€"
    if abs(val) >= 10_000:
        return f"{val/1e3:.0f} k€"
    return f"{val:,.0f} €"


def _yticks(ymin: float, ymax: float, n: int = 6) -> dict:
    """
    Retourne tickvals + ticktext formates en M€ ou k€.
    Gere les plages melangees (negatif/positif).
    """
    span = ymax - ymin
    if span <= 0:
        return {}
    if span >= 800_000:        # echelle M€
        step = max(500_000, round(span / n / 500_000) * 500_000)
        lo   = int(np.floor(ymin / step)) * step
        hi   = int(np.ceil(ymax  / step)) * step + step
        vals = list(range(lo, hi, step))
        txt  = [(f"{v/1e6:.0f} M€" if v % 1_000_000 == 0 else f"{v/1e6:.1f} M€")
               if v != 0 else "0" for v in vals]
    else:                       # echelle k€
        step = max(10_000, round(span / n / 10_000) * 10_000)
        lo   = int(np.floor(ymin / step)) * step
        hi   = int(np.ceil(ymax  / step)) * step + step
        vals = list(range(lo, hi, step))
        txt  = [f"{v/1000:.0f} k€" if v != 0 else "0" for v in vals]
    return dict(tickvals=vals, ticktext=txt)


def _base(h=340, title="", ml=60, mr=30, mt=None, mb=None, legend_bottom=True, **kw):
    """
    Layout de base.
    Quand title est fourni ET legend_bottom=True : legende sous le graphique
    pour eviter le chevauchement titre/legende.
    """
    _mt = mt if mt is not None else (44 if title else 16)
    _mb = mb if mb is not None else (110 if (title and legend_bottom) else 50)

    if title and legend_bottom:
        legend = dict(
            orientation="h",
            yanchor="top", y=-0.28,   # plus bas pour eviter chevauchement labels obliques
            xanchor="center", x=0.5,
            font_size=12, bgcolor="rgba(0,0,0,0)", borderwidth=0,
        )
    else:
        legend = dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font_size=12, bgcolor="rgba(0,0,0,0)", borderwidth=0,
        )

    base = dict(
        height=h,
        margin=dict(l=ml, r=mr, t=_mt, b=_mb),
        paper_bgcolor=C["fond"], plot_bgcolor=C["fond"],
        font=dict(family=FONT, size=13, color=C["texte"]),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=12, color=C["muted"]), tickangle=-40,
            showline=False,
        ),
        yaxis=dict(
            showgrid=True, gridcolor=C["grille"], gridwidth=1,
            zeroline=True, zerolinecolor=C["zero"], zerolinewidth=1.5,
            tickfont=dict(size=12, color=C["muted"]),
            showline=False,
        ),
        legend=legend,
        hoverlabel=dict(
            font_size=13, font_family=FONT,
            bgcolor="white", bordercolor=C["sep"],
        ),
    )
    if title:
        base["title"] = dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color=C["texte"]),
            x=0, xanchor="left", y=1, yanchor="top",
        )
    # Merge xaxis/yaxis/legend au lieu de les remplacer
    for key in ("xaxis", "yaxis", "legend"):
        if key in kw:
            base[key] = {**base.get(key, {}), **kw.pop(key)}
    base.update(kw)
    return base


# ── Charts individuels ────────────────────────────────────────────────────────

def chart_evolution_solde(df: pd.DataFrame) -> go.Figure:
    reel = df[df["est_reel"] == True].sort_values("periode_idx")
    prev = df[df["est_reel"] == False].sort_values("periode_idx")

    ymin = min(reel["solde_reseau"].min(), 0)
    ymax = reel["solde_reseau"].max()

    fig = go.Figure()
    fig.add_hline(y=0, line_color=C["zero"], line_width=1.2)

    # Zone remplie
    fig.add_trace(go.Scatter(
        x=reel["mois_label"], y=reel["solde_reseau"],
        fill="tozeroy", fillcolor="rgba(21,101,192,0.07)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    # Courbe reelle
    fig.add_trace(go.Scatter(
        x=reel["mois_label"], y=reel["solde_reseau"],
        mode="lines+markers", name="Realise",
        line=dict(color=C["bleu"], width=2.5),
        marker=dict(size=3, color=C["bleu"]),
        hovertemplate="<b>%{x}</b><br>Solde : %{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in reel["solde_reseau"]],
    ))
    if len(prev):
        jct = pd.concat([reel.tail(1), prev])
        fig.add_trace(go.Scatter(
            x=jct["mois_label"], y=jct["solde_reseau"],
            mode="lines", name="Previsionnel",
            line=dict(color=C["bleu"], width=2, dash="dot"),
            hovertemplate="<b>%{x}</b><br>Prev : %{customdata}<extra></extra>",
            customdata=[_fmt_y(v) for v in jct["solde_reseau"]],
        ))

    # Annotations dynamiques : 2 pires mois reels (plus de sites negatifs ou solde le plus bas)
    candidats = reel[reel["nb_negatifs"] > 0].copy() if "nb_negatifs" in reel.columns else pd.DataFrame()
    if len(candidats) >= 1:
        pires = candidats.nsmallest(2, "solde_reseau")
        cols_annot = [C["rouge"], C["orange"]]
        for (_, row), col in zip(pires.iterrows(), cols_annot):
            n = int(row["nb_negatifs"])
            label = f"<b>{n} site{'s' if n > 1 else ''} negatif{'s' if n > 1 else ''}</b>"
            fig.add_annotation(
                x=row["mois_label"], y=row["solde_reseau"],
                text=label,
                showarrow=True, arrowhead=2, arrowwidth=1.5, arrowcolor=col,
                font=dict(size=12, color=col), bgcolor="white",
                bordercolor=col, borderwidth=1, borderpad=4, ax=0, ay=-40,
            )

    yt = _yticks(ymin * 1.1, ymax * 1.1)
    mois_debut = df["mois_label"].iloc[0]  if len(df) else ""
    mois_fin   = df["mois_label"].iloc[-1] if len(df) else ""
    titre_dyn  = f"Solde reseau consolide — {mois_debut} → {mois_fin}"
    fig.update_layout(**_base(
        h=420, title=titre_dyn, mb=110,
        yaxis=dict(showgrid=True, gridcolor=C["grille"], tickfont=dict(size=12, color=C["muted"]),
                   zeroline=True, zerolinecolor=C["zero"], zerolinewidth=1.5, **yt),
    ))
    return fig


def chart_heatmap_soldes(df: pd.DataFrame) -> go.Figure:
    pivot = df.pivot(index="site_nom", columns="mois_label", values="solde_fin")
    cols  = df.sort_values("periode_idx")["mois_label"].unique().tolist()
    pivot = pivot.reindex(columns=cols)
    fig   = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[
            [0.00, "#7F1D1D"], [0.30, "#EF4444"],
            [0.45, "#FEF9C3"], [0.55, "#FEF9C3"],
            [0.70, "#4ADE80"], [1.00, "#14532D"],
        ],
        zmid=0,
        hovertemplate="<b>%{y}</b><br>%{x}<br><b>%{customdata}</b><extra></extra>",
        customdata=[[_fmt_y(v) for v in row] for row in pivot.values],
        colorbar=dict(
            title=dict(text="Solde", font_size=12),
            thickness=10, len=0.65, tickfont=dict(size=11),
        ),
    ))
    # 1 label X sur 2 pour reduire la densite (28 mois -> 14 labels)
    visible_cols = cols[::2]
    fig.update_layout(**_base(
        h=630, title="Heatmap soldes — sites x mois (28 mois)",
        ml=180, mr=80, mb=120, legend_bottom=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=11), tickangle=-40,
                   tickvals=visible_cols, ticktext=visible_cols),
        yaxis=dict(showgrid=False, tickfont=dict(size=12), zeroline=False),
    ))
    return fig


def chart_waterfall(df: pd.DataFrame) -> go.Figure:
    LABELS = {
        "Encaissements clients": "Clients",
        "Paiements fournisseurs": "Fournis.",
        "Masse salariale": "Salaires",
        "Charges d'exploitation": "Charges",
        "Loyers et charges locatives": "Loyers",
        "Remboursement emprunt": "Emprunt",
        "Frais financiers": "Frais fin.",
        "TVA nette": "TVA",
        "Impots et taxes": "Impots",
        "Capex": "Capex",
        "Autres produits": "Autres",
    }
    df = df.sort_values("montant").copy()
    df["label"] = df["sous_categorie"].map(LABELS).fillna(df["sous_categorie"])
    total = df["montant"].sum()
    df = pd.concat([df, pd.DataFrame([{"label": "Flux net", "montant": total}])],
                   ignore_index=True)

    # Masquer les labels pour les barres < 10 k€ (evite "0k€" et debordements)
    wf_texts = [
        (f"{v/1e3:+.0f} k€" if abs(v) >= 10_000 else "")
        for v in df["montant"]
    ]
    fig = go.Figure(go.Waterfall(
        x=df["label"], y=df["montant"],
        measure=["relative"] * (len(df) - 1) + ["total"],
        text=wf_texts,
        textposition="outside", textfont=dict(size=12, color=C["texte"]),
        connector=dict(line=dict(color=C["sep"], width=0.8, dash="dot")),
        increasing=dict(marker_color=C["vert"],  marker_line_width=0),
        decreasing=dict(marker_color=C["rouge"], marker_line_width=0),
        totals=dict(marker_color=C["bleu"],       marker_line_width=0),
        hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in df["montant"]],
    ))
    yt = _yticks(df["montant"].min() * 1.15, df["montant"].max() * 1.15)
    fig.update_layout(**_base(
        h=440, title="Waterfall — composition du flux mensuel",
        showlegend=False, mb=100,
        xaxis=dict(showgrid=False, tickfont=dict(size=12), tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor=C["grille"],
                   tickfont=dict(size=12, color=C["muted"]),
                   zeroline=True, zerolinecolor=C["zero"], **yt),
    ))
    return fig


def chart_flux_mensuel(df: pd.DataFrame) -> go.Figure:
    NOMS = {
        "ENCAISSEMENTS":         "Encaissements",
        "DECAISSEMENTS_EXPLOIT": "Exploitation",
        "FISCAL":                "Fiscal",
        "INVESTISSEMENT":        "Investissement",
        "FINANCEMENT":           "Financement",
    }
    fig = go.Figure()

    all_vals = []
    for cat, color in CAT.items():
        sub = (df[df["categorie"] == cat]
               .groupby(["periode_idx","mois_label"])["montant"]
               .sum().reset_index().sort_values("periode_idx"))
        all_vals.extend(sub["montant"].tolist())
        fig.add_trace(go.Bar(
            x=sub["mois_label"], y=sub["montant"],
            name=NOMS.get(cat, cat), marker_color=color, marker_line_width=0,
            hovertemplate=f"<b>{NOMS.get(cat,'')}</b><br>%{{x}}<br>%{{customdata}}<extra></extra>",
            customdata=[_fmt_y(v) for v in sub["montant"]],
        ))

    fn = (df.groupby(["periode_idx","mois_label"])["montant"]
           .sum().reset_index().sort_values("periode_idx"))
    all_vals.extend(fn["montant"].tolist())
    fig.add_trace(go.Scatter(
        x=fn["mois_label"], y=fn["montant"], name="Flux net",
        mode="lines", line=dict(color="#0F172A", width=2.5),
        hovertemplate="<b>Flux net</b><br>%{x}<br>%{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in fn["montant"]],
    ))

    if all_vals:
        yt = _yticks(min(all_vals) * 1.1, max(all_vals) * 1.1)
    else:
        yt = {}

    fig.update_layout(**_base(
        h=420, mb=120, title="Flux par categorie — 28 mois", barmode="relative",
        yaxis=dict(showgrid=True, gridcolor=C["grille"],
                   tickfont=dict(size=11, color=C["muted"]),
                   zeroline=True, zerolinecolor=C["zero"], **yt),
        legend=dict(orientation="h", yanchor="top", y=-0.28,
                    xanchor="center", x=0.5,
                    font_size=11, bgcolor="rgba(0,0,0,0)", borderwidth=0),
    ))
    return fig


def chart_aging_donut(aging: dict) -> go.Figure:
    colors = ["#14532D", "#4ADE80", "#FDE047", "#F97316", "#7F1D1D"]
    labels = list(aging.keys())
    values = list(aging.values())
    total  = sum(values)
    retard = sum(v for k, v in aging.items() if k != "Non echu")

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker_colors=colors, textinfo="percent",
        textfont=dict(size=12), sort=False,
        hovertemplate="<b>%{label}</b><br>%{customdata}  (%{percent})<extra></extra>",
        customdata=[_fmt_y(v) for v in values],
    ))
    fig.add_annotation(
        text=(f"<b>{_fmt_y(total)}</b><br>"
              f"<span style='font-size:12px;color:{C['muted']}'>"
              f"{retard/total*100:.0f}% en retard</span>" if total > 0 else "Vide"),
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color=C["texte"]), align="center",
    )
    fig.update_layout(**_base(
        h=380, title="Aging encours clients",
        ml=10, mr=150, mt=44, mb=10,
        legend_bottom=False,
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5, font_size=12),
    ))
    return fig


def chart_bfr_evolution(df_flux: pd.DataFrame) -> go.Figure:
    TVA = 0.20
    enc = (df_flux[df_flux["sous_categorie"] == "Encaissements clients"]
           .groupby(["periode_idx","mois_label","est_reel"])["montant"].sum()
           .reset_index().sort_values("periode_idx"))
    pmt = (df_flux[df_flux["sous_categorie"] == "Paiements fournisseurs"]
           .groupby("periode_idx")["montant"].sum().abs().reset_index())
    merged = enc.merge(pmt, on="periode_idx", how="left", suffixes=("_enc","_pmt"))
    merged["ca_ht"]  = merged["montant_enc"].abs() / (1 + TVA)
    merged["ach_ht"] = merged["montant_pmt"].fillna(0) / (1 + TVA)
    merged["bfr_est"] = (merged["ca_ht"]  * 47/30
                        + merged["ach_ht"] * 28/30
                        - merged["ach_ht"] * 38/30)
    reel = merged[merged["est_reel"] == True]
    prev = merged[merged["est_reel"] == False]

    ymin = reel["bfr_est"].min()
    ymax = reel["bfr_est"].max()
    yt   = _yticks(ymin * 0.9, ymax * 1.1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=reel["mois_label"], y=reel["bfr_est"],
        fill="tozeroy", fillcolor="rgba(13,110,78,0.07)",
        mode="lines", name="BFR estime (reel)",
        line=dict(color=C["vert"], width=2.5),
        hovertemplate="<b>%{x}</b><br>BFR : %{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in reel["bfr_est"]],
    ))
    if len(prev):
        fig.add_trace(go.Scatter(
            x=prev["mois_label"], y=prev["bfr_est"],
            mode="lines", name="BFR estime (prev)",
            line=dict(color=C["vert"], width=2, dash="dot"),
        ))
    fig.update_layout(**_base(
        h=360,
        mb=110,
        title="Evolution BFR estime — reseau",
        yaxis=dict(showgrid=True, gridcolor=C["grille"],
                   tickfont=dict(size=11, color=C["muted"]),
                   zeroline=True, zerolinecolor=C["zero"], **yt),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.28,
            xanchor="center", x=0.5,
            font_size=11,
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
    ))
    return fig


def chart_score_risque(df: pd.DataFrame) -> go.Figure:
    df     = df.head(12).sort_values("score_risque").copy()
    colors = [C["rouge"] if s >= 50 else C["orange"] if s >= 20 else C["vert_l"]
              for s in df["score_risque"]]
    hover_data = [
        f"{r.nb_rouge} critique(s) · {r.nb_orange} vigilance(s)"
        for _, r in df.iterrows()
    ]
    fig = go.Figure(go.Bar(
        x=df["score_risque"], y=df["site_nom"],
        orientation="h",
        marker=dict(color=colors, line_width=0),
        text=[f"  {s}/100" for s in df["score_risque"]],
        textposition="outside", textfont=dict(size=11),
        customdata=hover_data,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score : <b>%{x}/100</b><br>"
            "%{customdata}<extra></extra>"
        ),
    ))
    # Lignes de seuil : 30 = Surveillance, 50 = Escalade
    fig.add_vline(x=30, line_width=1, line_dash="dot", line_color="#D97706")
    fig.add_annotation(x=30, y=1, yref="paper", text="Surveil.", showarrow=False,
                       font=dict(size=11, color="#D97706"), xanchor="left", yanchor="bottom")
    fig.add_vline(x=50, line_width=1, line_dash="dot", line_color="#B91C1C")
    fig.add_annotation(x=50, y=1, yref="paper", text="Escalade", showarrow=False,
                       font=dict(size=11, color="#B91C1C"), xanchor="left", yanchor="bottom")
    fig.update_layout(**_base(
        h=400, title="Score de risque — top 12 sites",
        showlegend=False, ml=170, mr=80,
        xaxis=dict(range=[0, 120], showgrid=True, gridcolor=C["grille"],
                   tickfont=dict(size=11, color=C["muted"]), zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color=C["texte"]),
                   zeroline=False),
    ))
    return fig


def chart_forecast(evo_reel, fc_base, fc_opt, fc_pess,
                   budget_mensuel: "pd.DataFrame | None" = None) -> go.Figure:
    """
    Forecast 3 scenarios.
    Palette distincte : realise = bleu nuit / base = ardoise / opt = vert / pess = rouge.
    Legende sous le graphique, axe Y en M€, IC discret, annotations inline.

    Parametre optionnel :
        budget_mensuel : DataFrame avec colonnes mois_label + solde_budget_cumul
                         Si fourni, trace une ligne budget cible en pointilles gold.
    """
    # ── Couleurs sans ambiguite ──────────────────────────────────────────────
    COL_REEL   = "#1E3A5F"   # bleu nuit — realise (reference historique)
    COL_BASE   = "#64748B"   # ardoise  — scenario neutre
    COL_OPT    = "#059669"   # vert     — scenario favorable
    COL_PESS   = "#B91C1C"   # rouge    — scenario adverse
    COL_BUDGET = "#B45309"   # ambre    — objectif budget

    fig    = go.Figure()
    dernier = evo_reel.sort_values("periode_idx").iloc[-1]

    # ── Zone forecast : fond tres leger ──────────────────────────────────────
    fig.add_vrect(
        x0=dernier["mois_label"],
        x1=fc_base["mois_label"].iloc[-1],
        fillcolor="rgba(241,245,249,0.7)",
        layer="below", line_width=0,
    )
    # Separateur
    fig.add_vline(
        x=dernier["mois_label"],
        line_width=1, line_dash="dot", line_color="#94A3B8",
    )

    # ── IC 80% — bande grise discrete (pas bleu, pas confondable) ────────────
    x_ic = list(fc_base["mois_label"]) + list(fc_base["mois_label"])[::-1]
    y_ic = list(fc_base["solde_ic_hi"]) + list(fc_base["solde_ic_lo"])[::-1]
    fig.add_trace(go.Scatter(
        x=x_ic, y=y_ic, fill="toself",
        fillcolor="rgba(148,163,184,0.15)",
        line=dict(color="rgba(148,163,184,0.3)", width=0.8),
        name="IC 80%", hoverinfo="skip",
    ))

    # ── Ligne realisee ───────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=evo_reel["mois_label"], y=evo_reel["solde_reseau"],
        mode="lines", name="Realise",
        line=dict(color=COL_REEL, width=3),
        hovertemplate="<b>%{x}</b><br>Solde : %{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in evo_reel["solde_reseau"]],
    ))
    fig.add_hline(y=0, line_color="#CBD5E1", line_width=1)

    # ── 3 scenarios ──────────────────────────────────────────────────────────
    x0 = [dernier["mois_label"]]
    y0 = [float(dernier["solde_reseau"])]

    SCENARIOS = [
        (fc_base, "Base",       COL_BASE, "dash",  2.0),
        (fc_opt,  "Optimiste",  COL_OPT,  "solid", 1.8),
        (fc_pess, "Pessimiste", COL_PESS, "solid", 1.8),
    ]
    for df_sc, nom, col, dash, lw in SCENARIOS:
        xvals = x0 + list(df_sc["mois_label"])
        yvals = y0 + list(df_sc["solde"])
        fig.add_trace(go.Scatter(
            x=xvals, y=yvals,
            mode="lines", name=nom,
            line=dict(color=col, width=lw, dash=dash),
            hovertemplate=f"<b>{nom}</b> %{{x}}<br>%{{customdata}}<extra></extra>",
            customdata=["—"] + [_fmt_y(v) for v in df_sc["solde"]],
        ))
        # Etiquette valeur finale — directement sur la courbe
        val_fin = float(df_sc["solde"].iloc[-1])
        fig.add_annotation(
            x=df_sc["mois_label"].iloc[-1], y=val_fin,
            text=f" {_fmt_y(val_fin)}",
            font=dict(size=12, color=col, family="Inter, sans-serif"),
            showarrow=False, xanchor="left", yanchor="middle",
        )

    # ── Ligne budget cible (optionnelle) ─────────────────────────────────────
    if budget_mensuel is not None and len(budget_mensuel) > 0:
        fig.add_trace(go.Scatter(
            x=budget_mensuel["mois_label"],
            y=budget_mensuel["solde_budget_cumul"],
            mode="lines+markers",
            name="Objectif budget",
            line=dict(color=COL_BUDGET, width=1.8, dash="longdash"),
            marker=dict(symbol="diamond", size=5, color=COL_BUDGET),
            hovertemplate="<b>Budget</b> %{x}<br>%{customdata}<extra></extra>",
            customdata=[_fmt_y(v) for v in budget_mensuel["solde_budget_cumul"]],
        ))

    # ── Axe Y en M€ ─────────────────────────────────────────────────────────
    all_y = (list(evo_reel["solde_reseau"])
             + list(fc_base["solde_ic_lo"]) + list(fc_base["solde_ic_hi"])
             + list(fc_opt["solde"]) + list(fc_pess["solde"]))
    if budget_mensuel is not None and len(budget_mensuel) > 0:
        all_y += list(budget_mensuel["solde_budget_cumul"])
    yt = _yticks(min(all_y) * 1.08, max(all_y) * 1.12)

    # Ordre chronologique explicite : realise (Jan 2024→Mar 2026) puis forecast
    ordered_x = list(evo_reel.sort_values("periode_idx")["mois_label"])
    ordered_x += [m for m in list(fc_base["mois_label"]) if m not in ordered_x]

    fig.update_layout(
        height=460,
        margin=dict(l=70, r=100, t=44, b=115),
        paper_bgcolor=C["fond"], plot_bgcolor=C["fond"],
        font=dict(family=FONT, size=13, color=C["texte"]),
        title=dict(
            text="<b>Forecast solde reseau</b>",
            font=dict(size=14, color=C["texte"]),
            x=0, xanchor="left",
        ),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.24,
            xanchor="center", x=0.5,
            font=dict(size=12, family=FONT),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            traceorder="normal",
        ),
        xaxis=dict(
            categoryorder="array",
            categoryarray=ordered_x,
            showgrid=False, zeroline=False,
            tickfont=dict(size=12, color=C["muted"], family=FONT),
            tickangle=-40,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#EEF2F7", gridwidth=1,
            zeroline=False,
            tickfont=dict(size=12, color=C["muted"], family=FONT),
            **yt,
        ),
        hoverlabel=dict(
            font_size=13, font_family=FONT,
            bgcolor="white", bordercolor="#E2E8F0",
        ),
    )
    return fig


def chart_forecast_composantes(df: pd.DataFrame) -> go.Figure:
    # 6 postes au lieu de 9 : Salaires + Charges + Loyers = Charges fixes
    # (reduire le nombre de couleurs simultanees ameliore la lisibilite)
    df = df.copy()
    ch_fixes_cols = ["masse_salariale", "charges_exploitation", "loyers"]
    ch_fixes_present = [c for c in ch_fixes_cols if c in df.columns]
    if ch_fixes_present:
        df["charges_fixes"] = df[ch_fixes_present].sum(axis=1)

    COMPS = [
        ("enc_clients",    "Encaissements",  C["vert"]),
        ("pmt_fournisseurs","Fournisseurs",  C["rouge"]),
        ("charges_fixes",  "Charges fixes",  "#92400E"),
        ("tva_nette",      "TVA",            C["orange"]),
        ("remb_emprunt",   "Emprunt",        C["bleu"]),
        ("capex",          "Capex",          C["violet"]),
        ("impots_taxes",   "Impots",         "#7C3AED"),
    ]
    fig = go.Figure()
    all_y = []
    for col, nom, color in COMPS:
        if col in df.columns:
            all_y.extend(df[col].tolist())
            fig.add_trace(go.Bar(
                x=df["mois_label"], y=df[col],
                name=nom, marker_color=color, marker_line_width=0,
                hovertemplate=f"<b>{nom}</b><br>%{{x}}<br>%{{customdata}}<extra></extra>",
                customdata=[_fmt_y(v) for v in df[col]],
            ))
    all_y.extend(df["flux_net"].tolist())
    fig.add_trace(go.Scatter(
        x=df["mois_label"], y=df["flux_net"],
        name="Flux net", mode="lines+markers",
        line=dict(color="#0F172A", width=2.5), marker=dict(size=5),
        hovertemplate="<b>Flux net</b><br>%{x}<br>%{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in df["flux_net"]],
    ))

    if all_y:
        yt = _yticks(min(all_y) * 1.1, max(all_y) * 1.1)
    else:
        yt = {}

    fig.update_layout(**_base(
        h=440, mb=145, title="Decomposition forecast — par composante",
        barmode="relative",
        yaxis=dict(showgrid=True, gridcolor=C["grille"],
                   tickfont=dict(size=11, color=C["muted"]),
                   zeroline=True, zerolinecolor=C["zero"], **yt),
        legend=dict(orientation="h", yanchor="top", y=-0.38,
                    xanchor="center", x=0.5,
                    font_size=11, bgcolor="rgba(0,0,0,0)", borderwidth=0),
    ))
    return fig


def chart_budget_ecart(df: pd.DataFrame) -> go.Figure:
    """
    Barres horizontales de l'ecart budget vs realise par sous-categorie.
    Vert = favorable (plus encaisse ou moins depense que prevu).
    Rouge = defavorable.
    """
    df = df[df["sous_categorie"] != "Autres produits"].copy()
    df = df.sort_values("ecart")

    LABELS = {
        "Encaissements clients": "Clients",
        "Paiements fournisseurs": "Fournis.",
        "Masse salariale": "Salaires",
        "Charges d'exploitation": "Charges",
        "Loyers et charges locatives": "Loyers",
        "Remboursement emprunt": "Emprunt",
        "Frais financiers": "Frais fin.",
        "TVA nette": "TVA",
        "Impots et taxes": "Impots",
        "Capex": "Capex",
    }
    df["label"] = df["sous_categorie"].map(LABELS).fillna(df["sous_categorie"])
    colors = [C["vert"] if v else C["rouge"] for v in df["favorable"]]
    hover  = [
        f"<b>{row.label}</b><br>"
        f"Realise : {_fmt_y(row.reel)}<br>"
        f"Budget  : {_fmt_y(row.budget)}<br>"
        f"Ecart   : {_fmt_y(row.ecart)} ({row.ecart_pct:+.1f}%)"
        for _, row in df.iterrows()
    ]
    fig = go.Figure(go.Bar(
        x=df["ecart"], y=df["label"],
        orientation="h",
        marker=dict(color=colors, line_width=0),
        text=[f" {_fmt_y(v)} ({p:+.0f}%)" for v, p in zip(df["ecart"], df["ecart_pct"])],
        textposition="outside", textfont=dict(size=12),
        customdata=hover,
        hovertemplate="%{customdata}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=1.5, line_color=C["zero"])
    xmax = df["ecart"].abs().max() * 1.5 if len(df) else 1
    yt   = _yticks(-xmax, xmax)
    fig.update_layout(**_base(
        h=440, title="Ecart budget vs realise — par poste",
        showlegend=False, ml=110, mr=90,
        xaxis=dict(range=[-xmax, xmax], showgrid=True,
                   gridcolor=C["grille"], zeroline=False,
                   tickfont=dict(size=12, color=C["muted"]), **yt),
        yaxis=dict(showgrid=False, tickfont=dict(size=12, color=C["texte"]),
                   zeroline=False),
    ))
    return fig


def chart_budget_mensuel(df_mois: pd.DataFrame) -> go.Figure:
    """
    Deux lignes : flux net realise vs flux net budget par mois.
    """
    ymin = min(df_mois[["flux_reel","flux_budget"]].min())
    ymax = max(df_mois[["flux_reel","flux_budget"]].max())
    yt   = _yticks(ymin * 1.1, ymax * 1.1)

    fig = go.Figure()
    fig.add_hline(y=0, line_color=C["zero"], line_width=1.2)
    fig.add_trace(go.Scatter(
        x=df_mois["mois_label"], y=df_mois["flux_budget"],
        mode="lines", name="Budget",
        line=dict(color="#94A3B8", width=2, dash="dot"),
        hovertemplate="<b>%{x}</b> Budget<br>%{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in df_mois["flux_budget"]],
    ))
    fig.add_trace(go.Bar(
        x=df_mois["mois_label"], y=df_mois["ecart"],
        name="Ecart",
        marker_color=[C["vert"] if v >= 0 else C["rouge"] for v in df_mois["ecart"]],
        marker_line_width=0, opacity=0.35,
        hovertemplate="<b>%{x}</b> Ecart<br>%{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in df_mois["ecart"]],
    ))
    fig.add_trace(go.Scatter(
        x=df_mois["mois_label"], y=df_mois["flux_reel"],
        mode="lines+markers", name="Realise",
        line=dict(color=C["bleu"], width=2.5),
        marker=dict(size=4),
        hovertemplate="<b>%{x}</b> Realise<br>%{customdata}<extra></extra>",
        customdata=[_fmt_y(v) for v in df_mois["flux_reel"]],
    ))
    fig.update_layout(**_base(
        h=400, title="Flux net mensuel — realise vs budget",
        mb=110, barmode="overlay",
        yaxis=dict(showgrid=True, gridcolor=C["grille"],
                   tickfont=dict(size=12, color=C["muted"]),
                   zeroline=True, zerolinecolor=C["zero"], **yt),
    ))
    return fig

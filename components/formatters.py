# -*- coding: utf-8 -*-
"""components/formatters.py -- FloMind Dashboard Tresorerie"""
from config.settings import RAG

def fmt_eur(val: float, unit: str = "auto", sign: bool = False) -> str:
    """Formate un montant en M€ / k€ / €."""
    prefix = "+" if (sign and val > 0) else ""
    if unit == "auto":
        if   abs(val) >= 1_000_000: unit = "M"
        elif abs(val) >= 10_000:    unit = "k"
        else:                        unit = ""
    if   unit == "M": return f"{prefix}{val/1e6:.2f} M€"
    elif unit == "k": return f"{prefix}{val/1e3:.0f} k€"
    else:             return f"{prefix}{val:,.0f} €"

def fmt_pct(val: float, sign: bool = True) -> str:
    prefix = "+" if (sign and val > 0) else ""
    return f"{prefix}{val:.1f}%"

def fmt_jours(val: float) -> str:
    return f"{val:.0f}j"

def rag_color(val, seuil_rouge, seuil_orange, inverse: bool = False) -> str:
    """Retourne la couleur RAG. inverse=True si valeur basse = bon."""
    if inverse:
        if   val <= seuil_rouge:  return RAG["rouge"]
        elif val <= seuil_orange: return RAG["orange"]
        else:                      return RAG["vert"]
    else:
        if   val >= seuil_rouge:  return RAG["rouge"]
        elif val >= seuil_orange: return RAG["orange"]
        else:                      return RAG["vert"]

def rag_solde(solde: float, runway: float) -> str:
    if solde < 0 or runway < 1:    return "rouge"
    if solde < 15_000 or runway < 3: return "orange"
    return "vert"

def badge_html(texte: str, couleur: str) -> str:
    """Badge HTML inline pour Streamlit (st.markdown unsafe_allow_html)."""
    return (f'''<span style="background:{couleur}22;color:{couleur};'''
            f'''border:1px solid {couleur}44;border-radius:4px;'''
            f'''padding:1px 7px;font-size:12px;font-weight:500">{texte}</span>''')

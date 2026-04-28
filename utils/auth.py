# -*- coding: utf-8 -*-
"""
utils/auth.py -- FloMind Dashboard Tresorerie
=============================================
Authentification simple (mode demo : mot de passe unique).
En production : remplacer par RBAC bcrypt DG/directeur site
(meme pattern que dashboard-budget-pilotage).

Usage dans app.py :
    from utils.auth import check_auth
    if not check_auth(): st.stop()
"""
import streamlit as st


DEMO_PASSWORD = "flomind2026"


def check_auth() -> bool:
    """
    Retourne True si l'utilisateur est authentifie.
    En mode demo : mot de passe unique.
    Pour desactiver : retourner True directement.
    """
    # Demo sans auth (portfolio public) -- decommenter pour activer
    return True

    # --- Auth activee (commenter la ligne ci-dessus) ---
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("## 💰 FloMind Trésorerie")
    st.markdown("*Accès sécurisé — demo portfolio*")
    pwd = st.text_input("Mot de passe", type="password", key="login_pwd")
    if st.button("Connexion"):
        try:
            expected = st.secrets.get("auth", {}).get("demo_password", DEMO_PASSWORD)
        except Exception:
            expected = DEMO_PASSWORD
        if pwd == expected:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
    return False

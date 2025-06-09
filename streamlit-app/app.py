# apes_streamlit_app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime
from urllib.parse import quote, urlparse
from collections import Counter

# Qui va incollata la definizione completa delle classi EnhancedGoogleCSE e AdvancedFootballScout
# Come già sviluppate nel messaggio precedente, senza modifiche ulteriori

# A scopo dimostrativo in questo codice finale mettiamo direttamente il main aggiornato

def main():
    st.set_page_config(page_title="APES Football Scout", layout="wide")
    st.title("🧠 APES – Hybrid Scouting Lens")
    st.caption("Cognitive Football Intelligence powered by Enhanced Google Search & Web Scraping")

    st.markdown("---")

    # Sidebar – Esempi rapidi
    st.sidebar.title("🎓 Esempi rapidi")
    examples = [
        "Lionel Messi", 
        "Khvicha Kvaratskhelia", 
        "trequartista argentino U17", 
        "difensore centrale Serie C"
    ]
    for example in examples:
        if st.sidebar.button(f"🔍 {example}"):
            st.session_state["query"] = example

    st.sidebar.markdown("---")
    st.sidebar.info("Inserisci una query nella barra centrale per cercare profili calcistici.")

    # Main input
    query = st.text_input("✏️ Inserisci nome del giocatore o criterio di scouting", 
                          value=st.session_state.get("query", ""), 
                          placeholder="Es. Victor Osimhen, centrocampista spagnolo U20")

    if st.button("🚀 Avvia Ricerca") and query.strip():
        with st.spinner("Analisi in corso..."):
            search_engine = EnhancedGoogleCSE()
            scout = AdvancedFootballScout(search_engine)
            report = scout.run_scouting(query)

            st.success(f"✅ Report generato con decisione finale: **{report['decision']}**")

            st.markdown("### 📝 Report Sintetico")
            st.markdown(report["markdown"])

            with st.expander("📦 Dati Consolidati (JSON)"):
                st.code(report["json"], language="json")

            with st.expander("📊 Dati in CSV"):
                st.download_button("⬇️ Scarica CSV", data=report["csv"], file_name="scouting_report.csv")

            with st.expander("🌐 Fonti Utilizzate"):
                for r in report["consolidated_data"].get("source_counts", {}).keys():
                    st.markdown(f"- 🔗 [{r}](https://{r})")

    st.markdown("---")
    st.caption("Powered by APES 🧬 – Data-enhanced football intelligence.")

if __name__ == "__main__":
    main()

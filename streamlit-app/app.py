# apes_streamlit_app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime
from urllib.parse import quote

class EnhancedGoogleCSE:
    """Motore di ricerca e scraping avanzato con Google CSE"""

    def __init__(self):
        self.api_key = st.secrets.get("GOOGLE_CSE_API_KEY", "")
        self.cse_id = "c12f53951c8884cfd"  # ID del motore CSE

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Pattern specifici per calcio (divisi per sito)
        self.extraction_patterns = {
            'transfermarkt': {
                'age': [r'Age:\s*(\d{1,2})', r'(\d{1,2})\s*years old'],
                'position': [r'Position:\s*([^,\n]+)', r'Main position:\s*([^,\n]+)'],
                'market_value': [r'Market value:\s*€([\d.]+)m', r'€([\d.]+)\s*million'],
                'goals': [r'Goals:\s*(\d+)', r'(\d+)\s*goals?'],
                'assists': [r'Assists:\s*(\d+)', r'(\d+)\s*assists?'],
                'club': [r'Club:\s*([^,\n]+)', r'Current club:\s*([^,\n]+)']
            },
            'whoscored': {
                'rating': [r'Rating:\s*([\d.]+)', r'([\d.]+)\s*rating'],
                'goals': [r'Goals:\s*(\d+)', r'(\d+)\s*goals?'],
                'assists': [r'Assists:\s*(\d+)', r'(\d+)\s*assists?'],
                'position': [r'Position:\s*([^,\n]+)', r'Plays as\s*([^,\n]+)']
            },
            'generic': {
                'age': [r'(\d{1,2})\s*(?:years old|age|anni)', r'Age:?\s*(\d{1,2})'],
                'goals': [r'(\d+)\s*goals?', r'Goals:?\s*(\d+)', r'scored\s*(\d+)'],
                'assists': [r'(\d+)\s*assists?', r'Assists:?\s*(\d+)'],
                'market_value': [r'€([\d.]+)(?:\s*(?:million|m))?', r'worth\s*€([\d.]+)'],
                'position': [r'Position:?\s*([^,\n]+)', r'plays as\s*([^,\n]+)'],
                'club': [r'(?:club|team):?\s*([A-Z][^,\n]+)', r'plays for\s*([A-Z][^,\n]+)']
            }
        }
    def search_and_scrape(self, query: str, max_results: int = 10) -> list:
        """Esegue una ricerca CSE e effettua scraping sui risultati"""
        try:
            urls = self._google_cse_search(query, max_results)
            results = []

            for url in urls:
                scraped = self._scrape_url(url)
                results.append({
                    'url': url,
                    'scraped_data': scraped.get('scraped_data', {}),
                    'scraping_success': scraped.get('scraping_success', False),
                    'page_size': scraped.get('page_size', 0),
                    'error': scraped.get('scraping_error', '')
                })

            return results

        except Exception as e:
            st.error(f"Errore in search_and_scrape: {e}")
            return []

    def _google_cse_search(self, query: str, max_results: int):
        """Effettua ricerca tramite Google Custom Search API"""
        try:
            query = quote(query)
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": max_results
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return self._parse_search_results(data)
            elif response.status_code == 429:
                st.warning("⚠️ Search quota exceeded")
                return []
            else:
                st.error(f"Search API error: {response.status_code}")
                return []

        except Exception as e:
            st.error(f"Search failed: {e}")
            return []
    def _scrape_url(self, url: str) -> dict:
        """Scarica e analizza contenuto della pagina"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'scraping_success': False, 'scraping_error': 'HTTP error'}

            soup = BeautifulSoup(response.content, 'html.parser')
            site_type = self._detect_site_type(url)

            extracted_data = self._extract_structured_data(soup, site_type)
            text_data = self._extract_from_text(soup.get_text(), site_type)
            extracted_data.update(text_data)

            return {
                'scraped_data': extracted_data,
                'scraping_success': True,
                'page_size': len(response.content)
            }

        except Exception as e:
            return {'scraping_success': False, 'scraping_error': str(e)}

    def _detect_site_type(self, url: str) -> str:
        """Determina il tipo di sito"""
        url = url.lower()
        if 'transfermarkt' in url:
            return 'transfermarkt'
        elif 'whoscored' in url:
            return 'whoscored'
        elif 'fotmob' in url:
            return 'fotmob'
        elif 'espn' in url:
            return 'espn'
        else:
            return 'generic'

    def _extract_structured_data(self, soup: BeautifulSoup, site_type: str) -> dict:
        """Estrae dati strutturati dal contenuto della pagina"""
        data = {}

        if site_type == 'transfermarkt':
            market_value_elem = soup.find('span', {'class': re.compile(r'.*market.*value.*', re.I)})
            if market_value_elem:
                value_text = market_value_elem.get_text()
                value_match = re.search(r'€([\d.]+)m?', value_text)
                if value_match:
                    data['market_value'] = f"€{value_match.group(1)}M"

            age_elem = soup.find('span', string=re.compile(r'Age:'))
            if age_elem:
                next_elem = age_elem.find_next()
                if next_elem:
                    age_text = next_elem.get_text()
                    age_match = re.search(r'(\d{1,2})', age_text)
                    if age_match:
                        data['age'] = int(age_match.group(1))

            position_elem = soup.find('dd', {'class': re.compile(r'.*position.*', re.I)})
            if position_elem:
                data['position'] = position_elem.get_text().strip()

        elif site_type == 'whoscored':
            rating_elem = soup.find('span', {'class': re.compile(r'.*rating.*', re.I)})
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    data['whoscored_rating'] = float(rating_match.group(1))

        json_ld = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_ld:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, dict) and json_data.get('@type') == 'Person':
                    data['structured_name'] = json_data.get('name', '')
                    data['structured_age'] = json_data.get('age', '')
            except:
                continue

        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            data['meta_description'] = meta_desc.get('content', '')

        return data

    def _extract_from_text(self, text: str, site_type: str) -> dict:
        """Estrae dati grezzi da testo pagina con regex"""
        data = {}
        patterns = self.extraction_patterns.get(site_type, self.extraction_patterns['generic'])

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if field in ['age', 'goals', 'assists']:
                        try:
                            data[field] = int(value)
                        except:
                            continue
                    elif field == 'market_value':
                        try:
                            data[field] = f"€{float(value):.2f}M"
                        except:
                            continue
                    else:
                        data[field] = value
                    break

        return data

    def _parse_search_results(self, data: dict) -> list:
        """Estrae link utili dai risultati CSE"""
        if "items" not in data:
            return []

        urls = []
        for item in data["items"]:
            link = item.get("link")
            if link:
                urls.append(link)
        return urls


# === ADVANCED SCOUT CLASS ===

class AdvancedFootballScout:
    """Motore centrale per scouting e analisi"""

    def __init__(self, search_engine: EnhancedGoogleCSE):
        self.search_engine = search_engine

    def run_scouting(self, query: str, max_results: int = 12) -> dict:
        st.info(f"🚀 Ricerca attiva per: **{query}**")
        urls = self.search_engine._google_cse_search(query, max_results)

        scraped_results = []
        for url in urls:
            scrape_result = self.search_engine._scrape_url(url)
            scrape_result["source_url"] = url
            scraped_results.append(scrape_result)

        consolidated = self._consolidate_data(scraped_results)
        report = self._generate_report(consolidated, scraped_results, query)

        return report

    def _consolidate_data(self, results: list) -> dict:
        """Unisce i dati da fonti multiple"""
        consolidated = {}
        counter = Counter()

        for result in results:
            if result.get("scraping_success"):
                data = result.get("scraped_data", {})
                for key, value in data.items():
                    if value:
                        if key not in consolidated:
                            consolidated[key] = value
                            counter[key] = 1
                        else:
                            # override solo se valore migliore
                            if isinstance(value, (int, float)) and value > float(consolidated.get(key, 0)):
                                consolidated[key] = value
                            elif isinstance(value, str) and len(value) > len(consolidated.get(key, '')):
                                consolidated[key] = value
                            counter[key] += 1

        consolidated['source_counts'] = dict(counter)
        consolidated['success_rate'] = round(
            100 * len([r for r in results if r.get("scraping_success")]) / max(1, len(results)), 1)
        consolidated['pages_scraped'] = len(results)

        return consolidated
    def _generate_report(self, consolidated: dict, results: list, query: str) -> dict:
        """Crea un report completo con i dati estratti e raccomandazione"""

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        goals = consolidated.get("goals", 0)
        assists = consolidated.get("assists", 0)
        age = consolidated.get("age", 0)
        market_value = consolidated.get("market_value", "N/A")
        position = consolidated.get("position", "Unknown")
        club = consolidated.get("club", "Unknown")

        total_contrib = goals + assists if isinstance(goals, int) and isinstance(assists, int) else 0
        age_score = round(100 - (age * 2), 1) if isinstance(age, int) and age < 40 else 0
        quality_score = int(consolidated.get("success_rate", 0))
        final_score = int((age_score + total_contrib + quality_score) / 3)

        decision = "NO_ACTION"
        if final_score > 70:
            decision = "ACQUIRE_TARGET"
        elif final_score > 50:
            decision = "FURTHER_ANALYSIS"

        markdown_report = f"""
# ⚽ APES Football Scout Report: {query} 

**Generated:** {now}  
**System:** APES Football Scout v3.0 (Enhanced Scraping)  
**Data Quality Score:** {quality_score}/100

## 📒 Search Analysis
- **Query Type:** Specific Player
- **Total Sources:** {len(results)}
- **Pages Scraped:** {consolidated.get('pages_scraped', 0)}
- **Success Rate:** {quality_score}%

## 🧤 Player Profile

**Basic Information:**
- **Age:** {age}
- **Position:** {position}
- **Current Club:** {club}

**Performance (2024):**
- **Goals:** {goals}
- **Assists:** {assists}
- **Total Contributions:** {total_contrib}
- **Age-Adjusted Score:** {age_score}

**Market Intelligence:**
- **Market Value:** {market_value}

## 🎯 Scouting Recommendation
**Decision:** {decision}  
**Reasoning:** {self._reasoning(decision, total_contrib, quality_score)}  
**Confidence Score:** {final_score}%

## 📚 Data Sources
""" + "\n".join([f"- 🔍 **{urlparse(r['source_url']).netloc}** - {urlparse(r['source_url']).path}" for r in results if r.get("source_url")])

        json_report = json.dumps(consolidated, indent=2)
        csv_report = pd.DataFrame([consolidated]).to_csv(index=False)

        return {
            "markdown": markdown_report,
            "json": json_report,
            "csv": csv_report,
            "score": final_score,
            "decision": decision,
            "consolidated_data": consolidated
        }

    def _reasoning(self, decision: str, contrib: int, quality: int) -> str:
        if decision == "ACQUIRE_TARGET":
            return "High contributions and strong data consistency"
        elif decision == "FURTHER_ANALYSIS":
            return "Limited statistical output or insufficient data"
        else:
            return "Insufficient impact or weak data confidence"

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
            scout = AdvancedFootballScout()
            results = scout.search(query)
            consolidated = scout.consolidate(results)
            report = scout._generate_report(consolidated, results, query)

            st.success(f"✅ Report generato con decisione finale: **{report['decision']}**")

            # Output principale
            st.markdown("### 📝 Report Sintetico")
            st.markdown(report["markdown"])

            # Espansori avanzati
            with st.expander("📦 Dati Consolidati (JSON)"):
                st.code(report["json"], language="json")

            with st.expander("📊 Dati in CSV"):
                st.download_button("⬇️ Scarica CSV", data=report["csv"], file_name="scouting_report.csv")

            with st.expander("🌐 Fonti Utilizzate"):
                for r in results:
                    if r.get("source_url"):
                        st.markdown(f"- 🔗 [{urlparse(r['source_url']).netloc}]({r['source_url']})")

    st.markdown("---")
    st.caption("Powered by APES 🧬 – Data-enhanced football intelligence.")

if __name__ == "__main__":
    main()



    

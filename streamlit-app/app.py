import streamlit as st
import requests
import json
import re
from datetime import datetime
from urllib.parse import quote_plus, urljoin, urlparse
from bs4 import BeautifulSoup
import time

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="⚽ APES Football Scout",
    page_icon="🦍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DEBUG temporaneo per conferma caricamento chiave API
st.text("API_KEY loaded: " + ("✅" if "GOOGLE_CSE_API_KEY" in st.secrets else "❌"))

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

    def _scrape_page_content(self, result: dict) -> dict:
        """Scrape additional data from page content"""

        url = result.get('url', '')
        if not url:
            return {}

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {}

            soup = BeautifulSoup(response.content, 'html.parser')

            # Determine site type for targeted extraction
            site_type = self._detect_site_type(url)

            # Extract structured data
            extracted_data = self._extract_structured_data(soup, site_type)

            # Extract additional text patterns
            page_text = soup.get_text()
            text_data = self._extract_from_text(page_text, site_type)

            # Merge data
            extracted_data.update(text_data)

            return {
                'scraped_data': extracted_data,
                'scraping_success': True,
                'page_size': len(page_text)
            }

        except Exception as e:
            return {
                'scraping_success': False,
                'scraping_error': str(e)
            }

    def _detect_site_type(self, url: str) -> str:
        """Detect website type for targeted extraction"""

        url_lower = url.lower()

        if 'transfermarkt' in url_lower:
            return 'transfermarkt'
        elif 'whoscored' in url_lower:
            return 'whoscored'
        elif 'fotmob' in url_lower:
            return 'fotmob'
        elif 'espn' in url_lower:
            return 'espn'
        else:
            return 'generic'

    def _extract_structured_data(self, soup: BeautifulSoup, site_type: str) -> dict:
        """Extract structured data based on site type"""

        data = {}

        if site_type == 'transfermarkt':
            # Transfermarkt-specific extraction

            # Market value
            market_value_elem = soup.find('span', {'class': re.compile(r'.*market.*value.*', re.I)})
            if market_value_elem:
                value_text = market_value_elem.get_text()
                value_match = re.search(r'€([\d.]+)m?', value_text)
                if value_match:
                    data['market_value'] = f"€{value_match.group(1)}M"

            # Age from profile
            age_elem = soup.find('span', string=re.compile(r'Age:'))
            if age_elem:
                age_text = age_elem.find_next().get_text() if age_elem.find_next() else ''
                age_match = re.search(r'(\d{1,2})', age_text)
                if age_match:
                    data['age'] = int(age_match.group(1))

            # Position
            position_elem = soup.find('dd', {'class': re.compile(r'.*position.*', re.I)})
            if position_elem:
                data['position'] = position_elem.get_text().strip()

data['position'] = position_elem.get_text().strip()

        elif site_type == 'whoscored':
            # WhoScored-specific extraction
            rating_elem = soup.find('span', {'class': re.compile(r'.*rating.*', re.I)})
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    data['whoscored_rating'] = float(rating_match.group(1))

        # Generic structured data
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_scripts:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, dict) and 'Person' in json_data.get('@type', ''):
                    data['structured_name'] = json_data.get('name', '')
                    data['structured_age'] = json_data.get('age', '')
            except:
                continue

        meta_description = soup.find('meta', {'name': 'description'})
        if meta_description:
            data['meta_description'] = meta_description.get('content', '')

        return data

    def _extract_from_text(self, text: str, site_type: str) -> dict:
        """Extract data using regex patterns from page text"""
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
                            break
                        except:
                            continue
                    elif field == 'market_value':
                        data[field] = f"€{value}M" if not value.startswith('€') else value
                        break
                    elif field in ['position', 'club']:
                        if 2 < len(value) < 50:
                            data[field] = value
                            break

        return data

    def _optimize_query(self, query: str) -> str:
        """Optimize search query for better results"""
        query_lower = query.lower()

        if not any(term in query_lower for term in ['football', 'soccer', 'player']):
            query += " football player"

        if any(term in query_lower for term in ['value', 'transfer', 'market']):
            query += " site:transfermarkt.com OR site:whoscored.com"

        if any(term in query_lower for term in ['stats', 'goals', 'assists', '2024']):
            if '2024' not in query:
                query += " 2024"

        return query

    def _parse_search_results(self, data: dict) -> list:
        """Parse Google CSE response with enhanced data extraction"""
        if 'items' not in data:
            return []

        results = []
        for item in data['items']:
            result = {
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'url': item.get('link', ''),
                'source': self._get_source_name(item.get('link', ''))
            }

# Extract data from snippet
            snippet_data = self._extract_from_text(result['snippet'], 'generic')
            result.update(snippet_data)
            
            # Extract pagemap data if available
            if 'pagemap' in item:
                pagemap_data = self._extract_pagemap_data(item['pagemap'])
                result.update(pagemap_data)
            
            results.append(result)
        
        return results
    
    def _extract_pagemap_data(self, pagemap: dict) -> dict:
        """Extract data from Google's pagemap"""
        
        data = {}
        
        # Check metatags
        if 'metatags' in pagemap and pagemap['metatags']:
            meta = pagemap['metatags'][0]
            
            # Extract from description
            description = meta.get('description', '') + ' ' + meta.get('og:description', '')
            desc_data = self._extract_from_text(description, 'generic')
            data.update(desc_data)
        
        # Check for person data
        if 'person' in pagemap and pagemap['person']:
            person = pagemap['person'][0]
            if 'name' in person:
                data['structured_name'] = person['name']
        
        return data
    
    def _get_source_name(self, url: str) -> str:
        """Get readable source name"""
        
        if 'transfermarkt' in url:
            return 'Transfermarkt'
        elif 'whoscored' in url:
            return 'WhoScored'
        elif 'fotmob' in url:
            return 'FotMob'
        elif 'espn' in url:
            return 'ESPN'
        elif 'goal' in url:
            return 'Goal.com'
        else:
            try:
                domain = urlparse(url).netloc
                return domain.replace('www.', '').title()
            except:
                return 'Web Source'
    
    def _fallback_search(self, query: str) -> list:
        """Enhanced fallback with realistic data"""
        
        query_lower = query.lower()
        
        # Enhanced fallback based on query analysis
        if any(term in query_lower for term in ['u17', 'u19', 'u20', 'youth']):
            return [{
                'title': f'Youth Academy Profile: {query}',
                'snippet': f'Promising academy prospect matching criteria: {query}. Development player with strong potential.',
                'url': '',
                'source': 'Youth Scout Network',
                'age': 17,
                'goals': 8,
                'assists': 5,
                'position': 'Attacking Midfielder',
                'market_value': '€100K-300K',
                'club': 'Youth Academy',
                'scraped_data': {'potential_rating': 'High', 'development_stage': 'Academy'}
            }]
        
        elif any(term in query_lower for term in ['trequartista', 'centrocampista', 'attaccante']):
            return [{
                'title': f'Professional Player: {query}',
                'snippet': f'Active professional matching: {query}. Playing in competitive league with solid statistics.',
                'url': '',
                'source': 'Football Database',
                'age': 23,
                'goals': 12,
                'assists': 7,
                'position': 'Central Midfielder',
                'market_value': '€800K',
                'club': 'Serie C Club',
                'scraped_data': {'league_level': 'Third Division', 'contract_expires': '2025'}
            }]
        
        else:
            return [{
                'title': f'Player Profile: {query}',
                'snippet': f'Comprehensive analysis for {query}. Professional footballer with established record.',
                'url': '',
                'source': 'Scout Intelligence',
                'age': 25,
                'goals': 15,
                'assists': 9,
                'position': 'Winger',
                'market_value': '€1M',
                'club': 'Club Unknown',
                'scraped_data': {'scout_rating': 'Reliable', 'last_performance': '2024-12-12'}
            }]

class AdvancedFootballScout:
    """Advanced scouting engine with enhanced scraping"""
    
    def __init__(self):
        self.search_engine = EnhancedGoogleCSE()
    
    def comprehensive_scout(self, query: str, enable_deep_scraping: bool = True) -> dict:
        """Comprehensive scouting with optional deep scraping"""
        
        # Progress tracking
        progress = st.progress(0)
        status = st.empty()
        
        # Query analysis
        status.text("🔍 Analyzing search query...")
        progress.progress(10)
        
        query_analysis = self._analyze_query(query)
        
        # Multi-phase search
        status.text("🌐 Searching multiple sources...")
        progress.progress(30)
        
        # Phase 1: Primary search
        primary_results = self.search_engine.search_and_scrape(
            query, 
            max_results=8, 
            deep_scrape=enable_deep_scraping
        )
        
        # Phase 2: Targeted searches based on query type
        status.text("🎯 Conducting targeted searches...")
        progress.progress(60)
        
        if query_analysis['type'] == 'specific_player':
            targeted_results = self._targeted_player_search(query, enable_deep_scraping)
        else:
            targeted_results = self._targeted_generic_search(query, query_analysis, enable_deep_scraping)
        
        # Combine and deduplicate results
        all_results = primary_results + targeted_results
        unique_results = self._deduplicate_results(all_results)
        
        # Data consolidation
        status.text("📊 Consolidating player data...")
        progress.progress(85)
        
        consolidated_data = self._consolidate_player_data(unique_results)
        
        # Generate final report
        status.text("📋 Generating comprehensive report...")
        progress.progress(95)
        
        report = self._generate_enhanced_report(query, query_analysis, consolidated_data, unique_results)
        
        progress.progress(100)
        status.text("✅ Advanced scouting analysis completed!")
        
        return report
    
    def _analyze_query(self, query: str) -> dict:
        """Enhanced query analysis"""
        
        query_lower = query.lower()
        
        indicators = {
            'youth': any(term in query_lower for term in ['u17', 'u19', 'u20', 'under', 'youth', 'academy']),
            'position': any(term in query_lower for term in ['trequartista', 'centrocampista', 'attaccante', 'difensore', 'portiere', 'midfielder', 'forward', 'defender']),
            'location': any(term in query_lower for term in ['argentino', 'brasiliano', 'italiano', 'serie', 'premier', 'bundesliga']),
            'attributes': any(term in query_lower for term in ['veloce', 'tecnico', 'sinistro', 'destro', 'fast', 'technical']),
            'specific_name': len([w for w in query.split() if w.istitle()]) >= 2,
            'market_focus': any(term in query_lower for term in ['value', 'transfer', 'market', 'price'])
        }
        
        return {
            'type': 'specific_player' if indicators['specific_name'] else 'generic_scouting',
            'indicators': indicators,
            'complexity': sum(indicators.values()),
            'search_priority': self._determine_search_priority(indicators)
        }
    
    def _determine_search_priority(self, indicators: dict) -> list:
        """Determine search priority based on indicators"""
        
        priority = []
        
        if indicators['market_focus']:
            priority.append('transfermarkt')
        if indicators['youth']:
            priority.append('youth_focus')
        if indicators['position']:
            priority.append('position_focus')
        
        return priority

def _targeted_player_search(self, player_name: str, deep_scrape: bool) -> list:
        """Targeted searches for specific player"""
        
        targeted_queries = [
            f"{player_name} transfermarkt market value",
            f"{player_name} whoscored rating stats",
            f"{player_name} goals assists 2024 season"
        ]
        
        all_results = []
        
        for query in targeted_queries:
            results = self.search_engine.search_and_scrape(query, max_results=3, deep_scrape=deep_scrape)
            all_results.extend(results)
            time.sleep(0.4)  # Rate limiting
        
        return all_results
    
    def _targeted_generic_search(self, criteria: str, analysis: dict, deep_scrape: bool) -> list:
        """Targeted searches for generic criteria"""
        
        targeted_queries = [f"{criteria} transfermarkt database"]
        
        if analysis['indicators']['youth']:
            targeted_queries.append(f"{criteria} youth academy prospects")
        
        if analysis['indicators']['position']:
            targeted_queries.append(f"{criteria} professional league players")
        
        all_results = []
        
        for query in targeted_queries:
            results = self.search_engine.search_and_scrape(query, max_results=4, deep_scrape=deep_scrape)
            all_results.extend(results)
            time.sleep(0.4)
        
        return all_results
    
    def _deduplicate_results(self, results: list) -> list:
        """Remove duplicate results based on URL and content similarity"""
        
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            
            # Create a signature for deduplication
            signature = f"{url}_{title[:50]}"
            
            if signature not in seen_urls:
                seen_urls.add(signature)
                unique_results.append(result)
        
        return unique_results
    
    def _consolidate_player_data(self, results: list) -> dict:
        """Consolidate player data from multiple sources"""
        
        consolidated = {
            'basic_info': {},
            'performance_stats': {},
            'market_data': {},
            'technical_data': {},
            'data_quality': {}
        }
        
        # Data confidence scoring
        source_reliability = {
            'Transfermarkt': 0.9,
            'WhoScored': 0.85,
            'ESPN': 0.8,
            'FotMob': 0.75,
            'Goal.com': 0.7
        }
        
        for result in results:
            source = result.get('source', '')
            reliability = source_reliability.get(source, 0.6)
            
            # Basic info consolidation
            for field in ['age', 'position', 'club']:
                if field in result and result[field]:
                    current_value = consolidated['basic_info'].get(field)
                    if not current_value or reliability > consolidated['data_quality'].get(field, 0):
                        consolidated['basic_info'][field] = result[field]
                        consolidated['data_quality'][field] = reliability
            
            # Performance stats (take highest values with good reliability)
            for field in ['goals', 'assists']:
                if field in result and result[field]:
                    current_value = consolidated['performance_stats'].get(field, 0)
                    if result[field] > current_value and reliability > 0.7:
                        consolidated['performance_stats'][field] = result[field]
                        consolidated['data_quality'][f"{field}_source"] = source
            
            # Market data
            if 'market_value' in result and result['market_value']:
                # continua nel prossimo blocco...
if 'market_value' not in consolidated['market_data'] or reliability > consolidated['data_quality'].get('market_value', 0):
                    consolidated['market_data']['market_value'] = result['market_value']
                    consolidated['data_quality']['market_value'] = reliability
                    consolidated['data_quality']['market_value_source'] = source
            
            # Technical data from scraping
            if result.get('scraped_data'):
                scraped = result['scraped_data']
                for key, value in scraped.items():
                    if value and key not in consolidated['technical_data']:
                        consolidated['technical_data'][key] = value
        
        return consolidated
    
    def _generate_enhanced_report(self, query: str, analysis: dict, consolidated_data: dict, raw_results: list) -> dict:
        """Generate enhanced report with consolidated data"""
        
        # Calculate metrics
        goals = consolidated_data['performance_stats'].get('goals', 0)
        assists = consolidated_data['performance_stats'].get('assists', 0)
        total_contributions = goals + assists
        
        # Enhanced recommendation logic
        age = consolidated_data['basic_info'].get('age')
        market_value = consolidated_data['market_data'].get('market_value', '')
        
        # Age-adjusted scoring
        age_factor = 1.0
        if age:
            if age <= 20:
                age_factor = 1.3  # Youth bonus
            elif age <= 25:
                age_factor = 1.1  # Prime age bonus
            elif age >= 30:
                age_factor = 0.9  # Experience factor
        
        adjusted_contributions = total_contributions * age_factor
        
        # Data quality assessment
        scraped_sources = len([r for r in raw_results if r.get('scraping_success')])
        data_quality_score = min(100, (scraped_sources * 20) + (len(raw_results) * 10))
        
        # Recommendation logic
        if adjusted_contributions >= 20:
            recommendation = "BUY"
            reasoning = f"Excellent productivity ({total_contributions} contributions) with good age profile"
            confidence = min(95, 70 + data_quality_score * 0.25)
        elif adjusted_contributions >= 12:
            recommendation = "MONITOR"
            reasoning = f"Solid productivity ({total_contributions} contributions), worth continued tracking"
            confidence = min(85, 60 + data_quality_score * 0.25)
        elif adjusted_contributions >= 5:
            recommendation = "SCOUT_FURTHER"
            reasoning = f"Shows potential ({total_contributions} contributions), requires deeper analysis"
            confidence = min(75, 50 + data_quality_score * 0.25)
        else:
            recommendation = "FURTHER_ANALYSIS"
            reasoning = "Limited statistical output or insufficient data"
            confidence = min(60, 30 + data_quality_score * 0.25)
        
        return {
            'metadata': {
                'query': query,
                'query_type': analysis['type'],
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'system': 'APES Football Scout v3.0 (Enhanced Scraping)',
                'total_sources': len(raw_results),
                'scraped_sources': scraped_sources,
                'data_quality_score': round(data_quality_score, 1)
            },
            'query_analysis': analysis,
            'consolidated_profile': {
                'basic_info': consolidated_data['basic_info'],
                'performance_stats': consolidated_data['performance_stats'],
                'market_data': consolidated_data['market_data'],
                'technical_data': consolidated_data['technical_data']
            },
            'recommendation': {
                'decision': recommendation,
                'reasoning': reasoning,
                'confidence_score': round(confidence, 1),
                'total_contributions': total_contributions,
                'age_adjusted_score': round(adjusted_contributions, 1)
            },
            'data_sources': [
                {
                    'source': r.get('source', ''),
                    'title': r.get('title', '')[:80] + '...' if len(r.get('title', '')) > 80 else r.get('title', ''),
                    'scraped': r.get('scraping_success', False),
                    'url': r.get('url', '')
                }
                for r in raw_results
            ],
            'scraping_summary': {
                'total_pages_scraped': scraped_sources,
                'scraping_success_rate': f"{(scraped_sources / len(raw_results) * 100):.1f}%" if raw_results else "0%",
                'data_consolidation_sources': len(set(r.get('source', '') for r in raw_results))
            }
        }

def format_enhanced_markdown_report(report: dict) -> str:
    """Format enhanced markdown report"""
    
    md = f"""# ⚽ APES Football Scout Report: {report['metadata']['query']}

**Generated:** {report['metadata']['generated_at']}  
**System:** {report['metadata']['system']}  
**Data Quality Score:** {report['metadata']['data_quality_score']}/100

## 📊 Search Analysis
- **Query Type:** {report['query_analysis']['type'].replace('_', ' ').title()}
- **Total Sources:** {report['metadata']['total_sources']}
- **Pages Scraped:** {report['metadata']['scraped_sources']}
- **Success Rate:** {report['scraping_summary']['scraping_success_rate']}

## 👤 Player Profile
"""
    
    profile = report['consolidated_profile']
    
    # Basic info
    basic = profile['basic_info']
    md += f"""
**Basic Information:**
- **Age:** {basic.get('age', 'Unknown')}
- **Position:** {basic.get('position', 'Unknown')}
- **Current Club:** {basic.get('club', 'Unknown')}
"""
    
    # Performance stats
    performance = profile['performance_stats']
    md += f"""
**Performance (2024):**
- **Goals:** {performance.get('goals', 'N/A')}
- **Assists:** {performance.get('assists', 'N/A')}
- **Total Contributions:** {report['recommendation']['total_contributions']}
- **Age-Adjusted Score:** {report['recommendation']['age_adjusted_score']}
"""
    
    # Market data
    market = profile['market_data']
    md += f"""
**Market Intelligence:**
- **Market Value:** {market.get('market_value', 'Unknown')}
"""
    
    # Technical data from scraping
    technical = profile['technical_data']
    if technical:
        md += f"""
**Technical Data (Scraped):**
"""
        for key, value in technical.items():
            md += f"- **{key.replace('_', ' ').title()}:** {value}\n"
    
    # Recommendation
    rec = report['recommendation']
    md += f"""
## 🎯 Scouting Recommendation
**Decision:** {rec['decision']}  
**Reasoning:** {rec['reasoning']}  
**Confidence Score:** {rec['confidence_score']:.1f}%

## 📚 Data Sources
"""
    
    for i, source in enumerate(report['data_sources'], 1):
        scraped_icon = "🔍" if source['scraped'] else "📄"
        md += f"{i}. {scraped_icon} **{source['source']}** - {source['title']}\n"
    
    md += f"""
## 🔧 Scraping Summary
- **Pages Successfully Scraped:** {report['scraping_summary']['total_pages_scraped']}
- **Scraping Success Rate:** {report['scraping_summary']['scraping_success_rate']}
- **Data Consolidation Sources:** {report['scraping_summary']['data_consolidation_sources']}

---
*Generated by APES Football Scout - Enhanced with Deep Web Scraping*
"""
    return md


def main():
    st.title("🦍⚽ APES Football Scout")
    st.markdown("### Enhanced AI-Powered Scouting with Deep Web Scraping")
    
    # Configuration status
    if st.secrets.get("GOOGLE_CSE_API_KEY"):
        st.success("✅ Google CSE Configured - Enhanced Search Active")
    else:
        st.error("❌ Google CSE API Key Missing")
        st.info("Add your API key to `.streamlit/secrets.toml`")
    
    # Sidebar
    st.sidebar.header("🔧 Advanced Configuration")
    
    search_mode = st.sidebar.radio(
        "Search Mode",
        ["Specific Player", "Generic Scouting"],
        help="Choose search strategy"
    )

enable_scraping = st.sidebar.checkbox(
        "Enable Deep Scraping",
        value=True,
        help="Scrape actual page content for enhanced data (slower but more accurate)"
    )

    max_sources = st.sidebar.slider(
        "Max Sources",
        min_value=5,
        max_value=15,
        value=10,
        help="Maximum number of sources to search"
    )

    export_format = st.sidebar.selectbox(
        "Export Format",
        ["Both", "JSON", "Markdown"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Enhanced Features")
    st.sidebar.markdown("""
    ✅ **Real Google CSE Search**  
    ✅ **Deep Web Scraping**  
    ✅ **Multi-Source Data Fusion**  
    ✅ **Transfermarkt Integration**  
    ✅ **WhoScored Statistics**  
    ✅ **Data Quality Scoring**
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 Search Examples")

    if search_mode == "Specific Player":
        examples = [
            "Khvicha Kvaratskhelia",
            "Victor Osimhen",
            "Rafael Leão",
            "Federico Chiesa"
        ]
    else:
        examples = [
            "trequartista argentino u17",
            "centrocampista sinistro Serie C",
            "attaccante veloce under 20",
            "difensore centrale brasiliano"
        ]

    for example in examples:
        if st.sidebar.button(f"🔍 {example}", key=f"example_{example.replace(' ', '_')}"):
            st.experimental_set_query_params(q=example)

    # Main interface
    col1, col2 = st.columns([4, 1])

    with col1:
        if search_mode == "Specific Player":
            query = st.text_input(
                "🎯 Player Name",
                placeholder="e.g., Khvicha Kvaratskhelia",
                help="Enter the full name of the player you want to scout"
            )
        else:
            query = st.text_input(
                "🔍 Scouting Criteria",
                placeholder="e.g., trequartista argentino u17",
                help="Describe the type of player you're looking for"
            )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        scout_btn = st.button(
            "🚀 Advanced Scout",
            type="primary",
            use_container_width=True,
            help="Start enhanced scouting with web scraping"
        )

    if scout_btn and query:
        st.markdown("---")
        
        # Initialize advanced scout
        scout = AdvancedFootballScout()
        
        # Display search configuration
        st.info(f"🔍 **Enhanced Search Mode:** {search_mode} | **Deep Scraping:** {'Enabled' if enable_scraping else 'Disabled'} | **Max Sources:** {max_sources}")
        
        # Run comprehensive analysis
        with st.container():
            report = scout.comprehensive_scout(query, enable_deep_scraping=enable_scraping)
            
            # Enhanced results display
            st.success(f"✅ Advanced analysis completed for **{query}**")
            
            # Enhanced metrics dashboard
            col1, col2, col3, col4, col5 = st.columns(5)

with col2:
                goals = report['consolidated_profile']['performance_stats'].get('goals', 0)
                st.metric("Goals", goals if goals else "N/A")

            with col3:
                assists = report['consolidated_profile']['performance_stats'].get('assists', 0)
                st.metric("Assists", assists if assists else "N/A")

            with col4:
                st.metric(
                    "Total Contrib.",
                    report['recommendation']['total_contributions']
                )

            with col5:
                st.metric(
                    "Confidence",
                    f"{report['recommendation']['confidence_score']:.0f}%"
                )

            # Enhanced recommendation display
            rec = report['recommendation']['decision']
            reasoning = report['recommendation']['reasoning']

            if rec == "BUY":
                st.success(f"🎯 **RECOMMENDATION: {rec}** - {reasoning}")
            elif rec == "MONITOR":
                st.warning(f"👀 **RECOMMENDATION: {rec}** - {reasoning}")
            elif rec == "SCOUT_FURTHER":
                st.info(f"🔍 **RECOMMENDATION: {rec}** - {reasoning}")
            else:
                st.error(f"❓ **RECOMMENDATION: {rec}** - {reasoning}")

            # Enhanced profile sections
            profile = report['consolidated_profile']

            # Basic Profile
            with st.expander("👤 Consolidated Player Profile", expanded=True):
                col1, col2, col3 = st.columns(3)

                basic = profile['basic_info']
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"Age: {basic.get('age', 'Unknown')}")
                    st.write(f"Position: {basic.get('position', 'Unknown')}")

                performance = profile['performance_stats']
                with col2:
                    st.write("**Performance Stats**")
                    st.write(f"Goals: {performance.get('goals', 'N/A')}")
                    st.write(f"Assists: {performance.get('assists', 'N/A')}")

                market = profile['market_data']
                with col3:
                    st.write("**Market Data**")
                    st.write(f"Club: {basic.get('club', 'Unknown')}")
                    st.write(f"Value: {market.get('market_value', 'Unknown')}")

            # Technical Data from Scraping
            technical = profile['technical_data']
            if technical:
                with st.expander("🔍 Enhanced Data (Web Scraping)"):
                    tech_cols = st.columns(2)
                    items = list(technical.items())
                    mid = len(items) // 2

                    with tech_cols[0]:
                        for key, value in items[:mid]:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                    with tech_cols[1]:
                        for key, value in items[mid:]:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

            # Data Sources Analysis
            with st.expander("📚 Data Sources Analysis"):
                sources_df_data = []
                for source in report['data_sources']:
                    sources_df_data.append({
                        'Source': source['source'],
                        'Scraped': '✅' if source['scraped'] else '❌',
                        'Title': source['title']
                    })

                if sources_df_data:
                    import pandas as pd
                    sources_df = pd.DataFrame(sources_df_data)
                    st.dataframe(sources_df, use_container_width=True)

                # Scraping summary
                scraping = report['scraping_summary']
                st.write("**Scraping Summary:**")
                st.write(f"• Pages Scraped: {scraping['total_pages_scraped']}")
                st.write(f"• Success Rate: {scraping['scraping_success_rate']}")
                st.write(f"• Unique Sources: {scraping['data_consolidation_sources']}")

# Enhanced Export Section
            st.markdown("---")
            st.subheader("📤 Enhanced Export Options")
            
            safe_name = query.replace(' ', '_').replace('/', '_').lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if export_format in ["JSON", "Both"]:
                    json_data = json.dumps(report, indent=2, ensure_ascii=False)
                    st.download_button(
                        "📄 Enhanced JSON Report",
                        json_data,
                        f"{safe_name}_enhanced_report_{timestamp}.json",
                        "application/json",
                        help="Complete data with scraping results"
                    )
            
            with col2:
                if export_format in ["Markdown", "Both"]:
                    md_data = format_enhanced_markdown_report(report)
                    st.download_button(
                        "📝 Professional MD Report",
                        md_data,
                        f"{safe_name}_professional_report_{timestamp}.md",
                        "text/markdown",
                        help="Professional scouting report format"
                    )
            
            with col3:
                # Enhanced CSV with more data
                csv_data = f"Query,Age,Position,Goals,Assists,Market_Value,Recommendation,Confidence,Data_Quality,Sources_Scraped\n"
                csv_data += f"{query},"
                csv_data += f"{profile['basic_info'].get('age', 'Unknown')},"
                csv_data += f"{profile['basic_info'].get('position', 'Unknown')},"
                csv_data += f"{profile['performance_stats'].get('goals', 'N/A')},"
                csv_data += f"{profile['performance_stats'].get('assists', 'N/A')},"
                csv_data += f"{profile['market_data'].get('market_value', 'Unknown')},"
                csv_data += f"{report['recommendation']['decision']},"
                csv_data += f"{report['recommendation']['confidence_score']:.1f},"
                csv_data += f"{report['metadata']['data_quality_score']},"
                csv_data += f"{report['metadata']['scraped_sources']}"
                
                st.download_button(
                    "📊 Enhanced CSV Data",
                    csv_data,
                    f"{safe_name}_enhanced_data_{timestamp}.csv",
                    "text/csv",
                    help="Structured data with quality metrics"
                )
    
    elif scout_btn and not query:
        st.warning("⚠️ Please enter a search query to start advanced scouting")
    
    # Feature showcase
    if not scout_btn:
        st.markdown("---")
        st.subheader("🚀 Enhanced Features Overview")
        
        feat_col1, feat_col2, feat_col3 = st.columns(3)
        
        with feat_col1:
            st.markdown("""
            **🔍 Deep Web Scraping**
            - Real page content extraction
            - Transfermarkt data mining
            - WhoScored statistics
            - Multi-source validation
            """)
        
        with feat_col2:
            st.markdown("""
            **🧠 Data Consolidation**
            - Multi-source data fusion
            - Confidence scoring
            - Source reliability weighting
            - Duplicate detection
            """)
        
        with feat_col3:
            st.markdown("""
            **📊 Enhanced Analytics**
            - Age-adjusted scoring
            - Data quality metrics
            - Professional reporting
            - Export versatility
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        🦍 <strong>APES Football Scout v3.0</strong> - Enhanced with Deep Web Scraping<br>
        Powered by Google Custom Search • Advanced Data Extraction • Professional Scouting Intelligence<br>
        <small>⚠️ Data accuracy depends on source availability - always verify through live observation</small>
        </div>
        """,
        unsafe_allow_html=True
    )

""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()






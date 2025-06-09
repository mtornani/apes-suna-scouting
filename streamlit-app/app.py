import streamlit as st
import requests
import json
import re
from datetime import datetime
from urllib.parse import quote_plus, urljoin, urlparse
from bs4 import BeautifulSoup
import time
import pandas as pd
from collections import defaultdict

# Configure page
st.set_page_config(
    page_title="⚽ APES Football Scout",
    page_icon="🦍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if API key is loaded
if "GOOGLE_CSE_API_KEY" in st.secrets:
    st.success("✅ API Key loaded successfully")
else:
    st.error("❌ API Key not found in secrets")

class EnhancedGoogleCSE:
    """Enhanced Google CSE with advanced scraping and search strategies"""
    
    def __init__(self):
        self.api_key = st.secrets.get("GOOGLE_CSE_API_KEY", "")
        self.cse_id = "c12f53951c8884cfd"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Enhanced patterns for youth and unknown players
        self.extraction_patterns = {
            'transfermarkt': {
                'age': [r'Age:\s*(\d{1,2})', r'(\d{1,2})\s*years old', r'Born:.*\((\d{1,2})\)'],
                'position': [r'Position:\s*([^,\n]+)', r'Main position:\s*([^,\n]+)'],
                'market_value': [r'Market value:\s*€([\d.]+)m', r'€([\d.]+)\s*million', r'Value:\s*€([\d.]+)'],
                'goals': [r'Goals:\s*(\d+)', r'(\d+)\s*goals?', r'Scored:\s*(\d+)'],
                'assists': [r'Assists:\s*(\d+)', r'(\d+)\s*assists?'],
                'club': [r'Club:\s*([^,\n]+)', r'Current club:\s*([^,\n]+)', r'Team:\s*([^,\n]+)'],
                'league': [r'League:\s*([^,\n]+)', r'Competition:\s*([^,\n]+)']
            },
            'youth': {
                'age': [r'U(\d{2})', r'Under[- ]?(\d{2})', r'(\d{1,2})\s*(?:years old|age|anni)'],
                'team': [r'Academy:\s*([^,\n]+)', r'Youth team:\s*([^,\n]+)', r'Primavera\s*([^,\n]+)'],
                'goals': [r'(\d+)\s*goals?\s*(?:this season|in \d+ matches)', r'Scored:\s*(\d+)'],
                'appearances': [r'(\d+)\s*appearances', r'(\d+)\s*matches', r'(\d+)\s*games'],
                'position': [r'Position:\s*([^,\n]+)', r'Plays as:\s*([^,\n]+)']
            },
            'generic': {
                'age': [r'(\d{1,2})\s*(?:years old|age|anni)', r'Age:?\s*(\d{1,2})', r'nato\s*(?:nel\s*)?\d{4}\s*\((\d{1,2})', r'born\s*\d{4}\s*\((\d{1,2})'],
                'goals': [r'(\d+)\s*(?:goals?|gol)', r'Goals:?\s*(\d+)', r'scored\s*(\d+)', r'(\d+)\s*reti'],
                'assists': [r'(\d+)\s*assists?', r'Assists:?\s*(\d+)', r'(\d+)\s*assist'],
                'market_value': [r'€([\d.]+)(?:\s*(?:million|m|mil))?', r'worth\s*€([\d.]+)', r'valore\s*€([\d.]+)'],
                'position': [r'Position:?\s*([^,\n]+)', r'plays as\s*([^,\n]+)', r'ruolo:?\s*([^,\n]+)'],
                'club': [r'(?:club|team|squadra):?\s*([A-Z][^,\n]+)', r'plays for\s*([A-Z][^,\n]+)', r'gioca\s*(?:per|nel)?\s*([A-Z][^,\n]+)']
            }
        }
        
        # Youth and lower league specific sites
        self.specialized_sites = {
            'youth': ['nextgenseries.com', 'scoutedftbl.com', 'footballtalentscout.net'],
            'italian': ['tuttomercatoweb.com', 'calciomercato.com', 'violanews.com'],
            'stats': ['fbref.com', 'sofascore.com', 'flashscore.com'],
            'video': ['wyscout.com', 'instatscout.com']
        }
    
    def search_and_scrape(self, query: str, max_results: int = 10, deep_scrape: bool = True, search_type: str = 'general'):
        """Enhanced search with multiple strategies for finding unknown players"""
        
        all_results = []
        
        # Strategy 1: Direct search
        direct_results = self._google_cse_search(query, max_results // 2)
        all_results.extend(direct_results)
        
        # Strategy 2: Context-enhanced search for youth/unknown players
        if search_type in ['youth', 'unknown']:
            context_queries = self._generate_context_queries(query, search_type)
            for context_query in context_queries[:2]:  # Limit to avoid quota
                context_results = self._google_cse_search(context_query, 3)
                all_results.extend(context_results)
                time.sleep(0.3)
        
        # Strategy 3: Site-specific search
        if len(all_results) < max_results // 2:
            site_results = self._site_specific_search(query, search_type)
            all_results.extend(site_results)
        
        # Remove duplicates
        unique_results = self._deduplicate_results(all_results)
        
        # Deep scraping if enabled
        if deep_scrape and unique_results:
            enhanced_results = []
            for idx, result in enumerate(unique_results[:5]):
                try:
                    scraped_data = self._scrape_page_content(result)
                    result.update(scraped_data)
                    enhanced_results.append(result)
                    
                    # Extract player names from content
                    if scraped_data.get('extracted_names'):
                        result['potential_matches'] = scraped_data['extracted_names']
                    
                    time.sleep(0.5)
                except Exception as e:
                    enhanced_results.append(result)
            
            enhanced_results.extend(unique_results[5:])
            return enhanced_results[:max_results]
        
        return unique_results[:max_results]
    
    def _generate_context_queries(self, base_query: str, search_type: str) -> list:
        """Generate context-enhanced queries for better results"""
        
        queries = []
        
        if search_type == 'youth':
            # Youth-specific contexts
            contexts = [
                f"{base_query} youth academy primavera",
                f"{base_query} under 19 goals assists",
                f"{base_query} giovani calciatori talenti",
                f"{base_query} nextgen series uefa youth"
            ]
            queries.extend(contexts)
        
        elif search_type == 'unknown':
            # Unknown player contexts
            contexts = [
                f"{base_query} goals scored statistics",
                f"{base_query} football player profile",
                f"{base_query} calcio giocatore statistiche",
                f"{base_query} transfermarkt wyscout"
            ]
            queries.extend(contexts)
        
        # Add league/category specific terms
        if 'serie' in base_query.lower():
            queries.append(f"{base_query} italian football league")
        if 'primavera' in base_query.lower():
            queries.append(f"{base_query} italy youth championship")
            
        return queries
    
    def _site_specific_search(self, query: str, search_type: str) -> list:
        """Search specific sites based on query type"""
        
        results = []
        sites = []
        
        # Select relevant sites
        if search_type == 'youth':
            sites = self.specialized_sites['youth']
        elif 'italia' in query.lower() or 'serie' in query.lower():
            sites = self.specialized_sites['italian']
        else:
            sites = self.specialized_sites['stats']
        
        # Search each site
        for site in sites[:2]:  # Limit to avoid quota
            site_query = f"{query} site:{site}"
            site_results = self._google_cse_search(site_query, 2)
            results.extend(site_results)
        
        return results
    
    def _google_cse_search(self, query: str, max_results: int):
        """Core Google CSE search with improved error handling"""
        
        if not self.api_key:
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            
            # Optimize query
            optimized_query = self._optimize_query(query)
            
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': optimized_query,
                'num': min(max_results, 10),
                'fields': 'items(title,snippet,link,pagemap)'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_search_results(data)
            elif response.status_code == 429:
                st.warning("⚠️ Search quota exceeded. Using cached data...")
                return self._get_cached_results(query)
            else:
                return []
                
        except Exception as e:
            return []
    
    def _scrape_page_content(self, result: dict) -> dict:
        """Enhanced scraping with name extraction"""
        
        url = result.get('url', '')
        if not url:
            return {}
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            site_type = self._detect_site_type(url)
            
            # Extract structured data
            extracted_data = self._extract_structured_data(soup, site_type)
            
            # Extract page text
            page_text = soup.get_text()
            
            # Extract names (for youth/unknown players)
            extracted_names = self._extract_player_names(page_text)
            if extracted_names:
                extracted_data['extracted_names'] = extracted_names
            
            # Extract stats from text
            text_data = self._extract_from_text(page_text, site_type)
            extracted_data.update(text_data)
            
            # Extract from tables
            table_data = self._extract_from_tables(soup)
            extracted_data.update(table_data)
            
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
    
    def _extract_player_names(self, text: str) -> list:
        """Extract potential player names from text"""
        
        names = []
        
        # Pattern for Italian/Latin names
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'
        
        # Common contexts where names appear
        contexts = [
            r'(?:scorer|marcatore|goalscorer):\s*' + name_pattern,
            r'(?:player|giocatore|calciatore)\s+' + name_pattern,
            name_pattern + r'\s*\(\d{1,2}\)',  # Name (age)
            name_pattern + r'\s*-\s*\d+\s*goals?'  # Name - X goals
        ]
        
        for context in contexts:
            matches = re.findall(context, text, re.MULTILINE)
            names.extend(matches)
        
        # Clean and deduplicate
        cleaned_names = []
        for name in names:
            if isinstance(name, tuple):
                name = name[0]
            name = name.strip()
            # Filter out common false positives
            if (len(name.split()) >= 2 and 
                not any(word in name.lower() for word in ['the', 'and', 'for', 'with'])):
                cleaned_names.append(name)
        
        return list(set(cleaned_names))[:5]  # Return top 5 unique names
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> dict:
        """Extract data from HTML tables"""
        
        data = {}
        tables = soup.find_all('table')
        
        for table in tables:
            # Look for stats tables
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            if any(stat in headers for stat in ['goals', 'assists', 'gol', 'reti']):
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:5]:  # Limit to first 5 rows
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Try to extract player stats
                        for i, header in enumerate(headers):
                            if i < len(cells):
                                if 'goal' in header or 'gol' in header:
                                    try:
                                        data['table_goals'] = int(cells[i].get_text().strip())
                                    except:
                                        pass
                                elif 'assist' in header:
                                    try:
                                        data['table_assists'] = int(cells[i].get_text().strip())
                                    except:
                                        pass
        
        return data
    
    def _optimize_query(self, query: str) -> str:
        """Optimize query for better results"""
        
        query_lower = query.lower()
        
        # Don't add "football player" if searching for teams or specific categories
        if not any(term in query_lower for term in ['primavera', 'u17', 'u19', 'under']):
            if not any(term in query_lower for term in ['football', 'soccer', 'calcio', 'player']):
                query += " football"
        
        # Add current year for stats
        current_year = datetime.now().year
        if 'stats' in query_lower or 'statistics' in query_lower:
            query += f" {current_year}"
        
        # Add language hints for Italian searches
        if any(term in query_lower for term in ['trequartista', 'centrocampista', 'attaccante']):
            query += " OR calcio"
        
        return query
    
    def _get_cached_results(self, query: str) -> list:
        """Return cached/example results when API quota is exceeded"""
        
        # This would ideally load from a cache, but for now return examples
        return [{
            'title': f'Cached Result: {query}',
            'snippet': 'API quota exceeded. Showing cached example data.',
            'url': '',
            'source': 'Cache',
            'cached': True
        }]
    
    def _deduplicate_results(self, results: list) -> list:
        """Remove duplicate results"""
        
        seen = set()
        unique = []
        
        for result in results:
            # Create signature from URL and title
            sig = f"{result.get('url', '')}_{result.get('title', '')[:30]}"
            if sig not in seen:
                seen.add(sig)
                unique.append(result)
        
        return unique
    
    def _detect_site_type(self, url: str) -> str:
        """Detect website type for targeted extraction"""
        
        url_lower = url.lower()
        
        if 'transfermarkt' in url_lower:
            return 'transfermarkt'
        elif 'whoscored' in url_lower:
            return 'whoscored'
        elif any(site in url_lower for site in ['nextgen', 'youth', 'primavera', 'giovanili']):
            return 'youth'
        elif 'tuttomercatoweb' in url_lower or 'calciomercato' in url_lower:
            return 'italian'
        else:
            return 'generic'
    
    def _extract_structured_data(self, soup: BeautifulSoup, site_type: str) -> dict:
        """Extract structured data based on site type"""
        
        data = {}
        
        # Try to extract JSON-LD data first
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_scripts:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, dict):
                    if json_data.get('@type') in ['Person', 'SportsTeam']:
                        data.update(self._parse_json_ld(json_data))
            except:
                continue
        
        # Site-specific extraction
        if site_type == 'transfermarkt':
            data.update(self._extract_transfermarkt_data(soup))
        elif site_type == 'youth':
            data.update(self._extract_youth_data(soup))
        
        return data
    
    def _extract_transfermarkt_data(self, soup: BeautifulSoup) -> dict:
        """Extract data from Transfermarkt pages"""
        
        data = {}
        
        # Market value
        value_elem = soup.find('div', {'class': 'dataMarktwert'})
        if value_elem:
            value_text = value_elem.get_text()
            match = re.search(r'€([\d.,]+)(?:m|Mio)', value_text)
            if match:
                data['market_value'] = f"€{match.group(1)}M"
        
        # Player data table
        info_table = soup.find('table', {'class': 'auflistung'})
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                label = row.find('th')
                value = row.find('td')
                if label and value:
                    label_text = label.get_text().strip().lower()
                    value_text = value.get_text().strip()
                    
                    if 'age' in label_text or 'alter' in label_text:
                        age_match = re.search(r'(\d+)', value_text)
                        if age_match:
                            data['age'] = int(age_match.group(1))
                    elif 'position' in label_text:
                        data['position'] = value_text
        
        return data
    
    def _extract_youth_data(self, soup: BeautifulSoup) -> dict:
        """Extract data from youth football sites"""
        
        data = {}
        
        # Look for common youth data patterns
        # Age categories
        for elem in soup.find_all(text=re.compile(r'U\d{2}|Under[- ]?\d{2}')):
            match = re.search(r'U(\d{2})|Under[- ]?(\d{2})', elem)
            if match:
                age = match.group(1) or match.group(2)
                data['youth_category'] = f"U{age}"
                data['estimated_age'] = int(age) - 1  # Approximate age
        
        return data
    
    def _parse_json_ld(self, json_data: dict) -> dict:
        """Parse JSON-LD structured data"""
        
        data = {}
        
        if json_data.get('name'):
            data['structured_name'] = json_data['name']
        if json_data.get('birthDate'):
            # Calculate age from birthdate
            try:
                birth_year = int(json_data['birthDate'][:4])
                data['age'] = datetime.now().year - birth_year
            except:
                pass
        
        return data
    
    def _extract_from_text(self, text: str, site_type: str) -> dict:
        """Extract data using regex patterns"""
        
        data = {}
        
        # Choose appropriate patterns
        if site_type == 'youth':
            patterns = self.extraction_patterns['youth']
        elif site_type in ['transfermarkt', 'whoscored']:
            patterns = self.extraction_patterns.get(site_type, self.extraction_patterns['generic'])
        else:
            patterns = self.extraction_patterns['generic']
        
        # Apply patterns
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    
                    # Process based on field type
                    if field in ['age', 'goals', 'assists', 'appearances']:
                        try:
                            data[field] = int(value)
                            break
                        except:
                            continue
                    elif field == 'market_value':
                        # Standardize market value format
                        data[field] = self._standardize_market_value(value)
                        break
                    else:
                        if 2 < len(value) < 50:  # Reasonable length
                            data[field] = value
                            break
        
        return data
    
    def _standardize_market_value(self, value: str) -> str:
        """Standardize market value format"""
        
        # Extract numeric value
        match = re.search(r'([\d.,]+)', value)
        if match:
            num = match.group(1).replace(',', '.')
            try:
                num_float = float(num)
                if num_float < 100:  # Assume millions
                    return f"€{num}M"
                else:  # Assume thousands
                    return f"€{num_float/1000:.1f}M"
            except:
                return f"€{value}"
        return f"€{value}"
    
    def _parse_search_results(self, data: dict) -> list:
        """Parse Google CSE response"""
        
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
        
        # Metatags
        if 'metatags' in pagemap and pagemap['metatags']:
            meta = pagemap['metatags'][0]
            description = meta.get('description', '') + ' ' + meta.get('og:description', '')
            if description:
                desc_data = self._extract_from_text(description, 'generic')
                data.update(desc_data)
        
        # Person data
        if 'person' in pagemap and pagemap['person']:
            person = pagemap['person'][0]
            if person.get('name'):
                data['structured_name'] = person['name']
            if person.get('url'):
                data['profile_url'] = person['url']
        
        # Sports data
        if 'sportsathlete' in pagemap and pagemap['sportsathlete']:
            athlete = pagemap['sportsathlete'][0]
            if athlete.get('name'):
                data['athlete_name'] = athlete['name']
        
        return data
    
    def _get_source_name(self, url: str) -> str:
        """Get readable source name"""
        
        if not url:
            return 'Unknown'
            
        domain_map = {
            'transfermarkt': 'Transfermarkt',
            'whoscored': 'WhoScored',
            'fotmob': 'FotMob',
            'espn': 'ESPN',
            'goal.com': 'Goal.com',
            'tuttomercatoweb': 'TuttoMercatoWeb',
            'calciomercato': 'Calciomercato',
            'nextgen': 'NextGen Series',
            'fbref': 'FBref',
            'sofascore': 'SofaScore'
        }
        
        url_lower = url.lower()
        for key, name in domain_map.items():
            if key in url_lower:
                return name
        
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '').split('.')[0].title()
        except:
            return 'Web Source'

class AdvancedFootballScout:
    """Advanced scouting engine with enhanced search strategies"""
    
    def __init__(self):
        self.search_engine = EnhancedGoogleCSE()
    
    def comprehensive_scout(self, query: str, search_mode: str = "auto", enable_deep_scraping: bool = True) -> dict:
        """Comprehensive scouting with intelligent search strategies"""
        
        # Progress tracking
        progress = st.progress(0)
        status = st.empty()
        
        # Step 1: Query analysis
        status.text("🔍 Analyzing search query...")
        progress.progress(10)
        
        query_analysis = self._analyze_query(query)
        search_type = self._determine_search_type(query, query_analysis, search_mode)
        
        # Step 2: Multi-strategy search
        status.text("🌐 Executing multi-strategy search...")
        progress.progress(30)
        
        all_results = []
        
        # Primary search
        primary_results = self.search_engine.search_and_scrape(
            query, 
            max_results=10, 
            deep_scrape=enable_deep_scraping,
            search_type=search_type
        )
        all_results.extend(primary_results)
        
        # If few results, try alternative strategies
        if len(primary_results) < 5:
            status.text("🎯 Expanding search with alternative strategies...")
            progress.progress(50)
            
            # Try broader searches
            if search_type == 'youth':
                alt_results = self._youth_alternative_search(query, query_analysis)
                all_results.extend(alt_results)
            elif search_type == 'unknown':
                alt_results = self._unknown_player_search(query, query_analysis)
                all_results.extend(alt_results)
        
        # Step 3: Data consolidation
        status.text("📊 Consolidating and analyzing data...")
        progress.progress(70)
        
        # Remove duplicates
        unique_results = self._deduplicate_comprehensive(all_results)
        
        # Extract potential player profiles
        player_profiles = self._extract_player_profiles(unique_results, query)
        
        # Step 4: Generate report
        status.text("📋 Generating comprehensive report...")
        progress.progress(90)
        
        report = self._generate_enhanced_report(
            query, 
            query_analysis, 
            player_profiles, 
            unique_results,
            search_type
        )
        
        progress.progress(100)
        status.text("✅ Advanced scouting analysis completed!")
        
        # Clean up
        time.sleep(0.5)
        progress.empty()
        status.empty()
        
        return report
    
    def _analyze_query(self, query: str) -> dict:
        """Deep query analysis"""
        
        query_lower = query.lower()
        
        # Extract components
        indicators = {
            'youth': any(term in query_lower for term in ['u17', 'u19', 'u20', 'under', 'youth', 'primavera', 'giovanili']),
            'position': {
                'found': any(term in query_lower for term in ['trequartista', 'centrocampista', 'attaccante', 'difensore', 'portiere', 'midfielder', 'forward', 'defender', 'goalkeeper']),
                'type': self._extract_position(query_lower)
            },
            'nationality': {
                'found': any(term in query_lower for term in ['argentino', 'brasiliano', 'italiano', 'spagnolo', 'francese']),
                'type': self._extract_nationality(query_lower)
            },
            'league': {
                'found': any(term in query_lower for term in ['serie', 'premier', 'bundesliga', 'liga', 'ligue']),
                'type': self._extract_league(query_lower)
            },
            'attributes': self._extract_attributes(query_lower),
            'is_specific_name': self._is_specific_name(query),
            'year_mentioned': self._extract_year(query)
        }
        
        # Determine search difficulty
        search_difficulty = self._assess_search_difficulty(indicators)
        
        return {
            'indicators': indicators,
            'search_difficulty': search_difficulty,
            'query_type': 'specific_player' if indicators['is_specific_name'] else 'criteria_based',
            'original_query': query
        }
    
    def _extract_position(self, query: str) -> str:
        """Extract position from query"""
        
        positions = {
            'trequartista': 'Attacking Midfielder',
            'centrocampista': 'Midfielder',
            'attaccante': 'Forward',
            'difensore': 'Defender',
            'portiere': 'Goalkeeper',
            'midfielder': 'Midfielder',
            'forward': 'Forward',
            'striker': 'Forward',
            'winger': 'Winger',
            'ala': 'Winger',
            'terzino': 'Fullback',
            'mediano': 'Defensive Midfielder',
            'regista': 'Deep-lying Playmaker'
        }
        
        for term, position in positions.items():
            if term in query:
                return position
        return ''
    
    def _extract_nationality(self, query: str) -> str:
        """Extract nationality from query"""
        
        nationalities = {
            'argentino': 'Argentina',
            'brasiliano': 'Brazil',
            'italiano': 'Italy',
            'spagnolo': 'Spain',
            'francese': 'France',
            'tedesco': 'Germany',
            'inglese': 'England',
            'portoghese': 'Portugal'
        }
        
        for term, nation in nationalities.items():
            if term in query:
                return nation
        return ''
    
    def _extract_league(self, query: str) -> str:
        """Extract league from query"""
        
        leagues = {
            'serie a': 'Serie A',
            'serie b': 'Serie B',
            'serie c': 'Serie C',
            'primavera': 'Primavera',
            'premier': 'Premier League',
            'bundesliga': 'Bundesliga',
            'la liga': 'La Liga',
            'ligue 1': 'Ligue 1'
        }
        
        for term, league in leagues.items():
            if term in query:
                return league
        return ''
    
    def _extract_attributes(self, query: str) -> list:
        """Extract player attributes from query"""
        
        attributes = []
        
        attribute_map = {
            'veloce': 'fast',
            'tecnico': 'technical',
            'sinistro': 'left-footed',
            'destro': 'right-footed',
            'forte': 'strong',
            'rapido': 'quick',
            'alto': 'tall',
            'giovane': 'young'
        }
        
        for ita, eng in attribute_map.items():
            if ita in query:
                attributes.append(eng)
        
        return attributes
    
    def _is_specific_name(self, query: str) -> bool:
        """Check if query contains a specific player name"""
        
        words = query.split()
        capitalized_words = [w for w in words if w[0].isupper() if w]
        
        # Likely a name if 2+ capitalized words
        if len(capitalized_words) >= 2:
            # Filter out common football terms
            non_terms = [w for w in capitalized_words if w.lower() not in 
                        ['serie', 'premier', 'league', 'united', 'real', 'milan']]
            return len(non_terms) >= 2
        
        return False
    
    def _extract_year(self, query: str) -> int:
        """Extract year from query"""
        
        year_match = re.search(r'20\d{2}', query)
        if year_match:
            return int(year_match.group())
        return 0
    
    def _assess_search_difficulty(self, indicators: dict) -> str:
        """Assess how difficult the search will be"""
        
        if indicators['is_specific_name']:
            return 'easy'
        elif indicators['youth'] and not indicators['league']['found']:
            return 'hard'  # Youth without specific league is hard
        elif indicators['position']['found'] and indicators['nationality']['found']:
            return 'medium'
        else:
            return 'hard'
    
    def _determine_search_type(self, query: str, analysis: dict, mode: str) -> str:
        """Determine the search type"""
        
        if mode != "auto":
            return mode
        
        indicators = analysis['indicators']
        
        if indicators['youth']:
            return 'youth'
        elif indicators['is_specific_name']:
            return 'specific'
        elif analysis['search_difficulty'] == 'hard':
            return 'unknown'
        else:
            return 'general'
    
    def _youth_alternative_search(self, query: str, analysis: dict) -> list:
        """Alternative search strategies for youth players"""
        
        results = []
        
        # Strategy 1: Search youth tournaments
        tournament_queries = [
            f"{query} viareggio cup",
            f"{query} youth league uefa",
            f"{query} campionato primavera"
        ]
        
        for t_query in tournament_queries[:2]:
            results.extend(self.search_engine.search_and_scrape(t_query, 3, deep_scrape=False))
            time.sleep(0.3)
        
        # Strategy 2: Search by team if league is mentioned
        if analysis['indicators']['league']['found']:
            league = analysis['indicators']['league']['type']
            team_query = f"{league} youth academy {query}"
            results.extend(self.search_engine.search_and_scrape(team_query, 3, deep_scrape=False))
        
        return results
    
    def _unknown_player_search(self, query: str, analysis: dict) -> list:
        """Search strategies for unknown players"""
        
        results = []
        
        # Extract key terms
        position = analysis['indicators']['position']['type']
        nationality = analysis['indicators']['nationality']['type']
        
        # Build contextual searches
        if position and nationality:
            # Search by position and nationality
            context_query = f"{nationality} {position} football players statistics"
            results.extend(self.search_engine.search_and_scrape(context_query, 5, deep_scrape=False))
        
        # Search recent match reports
        if analysis['indicators']['year_mentioned']:
            year = analysis['indicators']['year_mentioned']
            match_query = f"{query} match report {year} goals"
            results.extend(self.search_engine.search_and_scrape(match_query, 3, deep_scrape=False))
        
        return results
    
    def _deduplicate_comprehensive(self, results: list) -> list:
        """Advanced deduplication"""
        
        unique_results = []
        seen_signatures = set()
        
        for result in results:
            # Create multiple signatures for better deduplication
            url_sig = result.get('url', '')
            title_sig = result.get('title', '')[:50]
            content_sig = result.get('snippet', '')[:50]
            
            combined_sig = f"{url_sig}_{title_sig}_{content_sig}"
            
            if combined_sig not in seen_signatures:
                seen_signatures.add(combined_sig)
                unique_results.append(result)
        
        return unique_results
    
    def _extract_player_profiles(self, results: list, original_query: str) -> list:
        """Extract distinct player profiles from results"""
        
        profiles = []
        profile_map = defaultdict(lambda: {
            'names': [],
            'data_points': [],
            'sources': [],
            'confidence': 0
        })
        
        for result in results:
            # Check if result contains player data
            has_player_data = any(result.get(field) for field in ['age', 'goals', 'assists', 'position'])
            
            if has_player_data:
                # Try to identify the player
                player_key = self._identify_player_key(result, original_query)
                
                profile = profile_map[player_key]
                profile['sources'].append(result.get('source', ''))
                
                # Aggregate data
                for field in ['age', 'goals', 'assists', 'position', 'club', 'market_value']:
                    if result.get(field):
                        profile['data_points'].append({
                            'field': field,
                            'value': result[field],
                            'source': result.get('source', '')
                        })
                
                # Add extracted names
                if result.get('scraped_data', {}).get('extracted_names'):
                    profile['names'].extend(result['scraped_data']['extracted_names'])
                
                # Update confidence
                if result.get('scraping_success'):
                    profile['confidence'] += 20
                else:
                    profile['confidence'] += 10
        
        # Convert to list and consolidate
        for key, profile in profile_map.items():
            consolidated = self._consolidate_profile(profile)
            consolidated['search_key'] = key
            profiles.append(consolidated)
        
        # Sort by confidence
        profiles.sort(key=lambda x: x['confidence'], reverse=True)
        
        return profiles[:5]  # Return top 5 profiles
    
    def _identify_player_key(self, result: dict, query: str) -> str:
        """Create a key to identify unique players"""
        
        # Try to extract player name
        if result.get('structured_name'):
            return result['structured_name'].lower()
        
        # Use extracted names
        if result.get('scraped_data', {}).get('extracted_names'):
            names = result['scraped_data']['extracted_names']
            if names:
                return names[0].lower()
        
        # Use combination of age + position as fallback
        age = result.get('age', 'unknown')
        position = result.get('position', 'unknown')
        return f"{age}_{position}_{query[:20]}"
    
    def _consolidate_profile(self, profile_data: dict) -> dict:
        """Consolidate player profile from multiple sources"""
        
        consolidated = {
            'confidence': min(profile_data['confidence'], 100),
            'sources': list(set(profile_data['sources'])),
            'source_count': len(set(profile_data['sources']))
        }
        
        # Determine most likely name
        if profile_data['names']:
            name_counts = defaultdict(int)
            for name in profile_data['names']:
                name_counts[name] += 1
            consolidated['name'] = max(name_counts.items(), key=lambda x: x[1])[0]
        else:
            consolidated['name'] = 'Unknown Player'
        
        # Aggregate data points
        field_values = defaultdict(list)
        for dp in profile_data['data_points']:
            field_values[dp['field']].append({
                'value': dp['value'],
                'source': dp['source']
            })
        
        # Select best value for each field
        for field, values in field_values.items():
            if field in ['goals', 'assists', 'age']:
                # For numeric fields, take the maximum from reliable sources
                numeric_values = []
                for v in values:
                    try:
                        numeric_values.append(int(v['value']))
                    except:
                        pass
                if numeric_values:
                    consolidated[field] = max(numeric_values)
            else:
                # For text fields, take the most common
                value_counts = defaultdict(int)
                for v in values:
                    value_counts[v['value']] += 1
                if value_counts:
                    consolidated[field] = max(value_counts.items(), key=lambda x: x[1])[0]
        
        return consolidated
    
    def _generate_enhanced_report(self, query: str, analysis: dict, profiles: list, raw_results: list, search_type: str) -> dict:
        """Generate comprehensive scouting report"""
        
        # Calculate overall data quality
        scraped_count = len([r for r in raw_results if r.get('scraping_success')])
        data_quality = min(100, (scraped_count * 15) + (len(raw_results) * 5) + (len(profiles) * 10))
        
        # Generate recommendations for each profile
        recommendations = []
        for profile in profiles:
            rec = self._generate_recommendation(profile)
            recommendations.append({
                'player': profile.get('name', 'Unknown'),
                'decision': rec['decision'],
                'reasoning': rec['reasoning'],
                'confidence': rec['confidence'],
                'profile': profile
            })
        
        # Summary statistics
        total_sources = len(raw_results)
        unique_sources = len(set(r.get('source', '') for r in raw_results))
        
        report = {
            'metadata': {
                'query': query,
                'search_type': search_type,
                'query_analysis': analysis,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'system': 'APES Football Scout v4.0 (Enhanced Unknown Player Search)',
                'total_sources': total_sources,
                'unique_sources': unique_sources,
                'scraped_sources': scraped_count,
                'data_quality_score': round(data_quality, 1)
            },
            'player_profiles': profiles,
            'recommendations': recommendations,
            'search_summary': {
                'difficulty': analysis['search_difficulty'],
                'profiles_found': len(profiles),
                'search_strategies_used': self._get_search_strategies(search_type),
                'data_coverage': self._assess_data_coverage(profiles)
            },
            'raw_results': raw_results[:10]  # Limit for display
        }
        
        return report
    
    def _generate_recommendation(self, profile: dict) -> dict:
        """Generate recommendation for a player profile"""
        
        # Base scoring
        goals = profile.get('goals', 0)
        assists = profile.get('assists', 0)
        age = profile.get('age', 25)
        confidence = profile.get('confidence', 0)
        
        # Calculate performance score
        total_contributions = goals + assists
        
        # Age factor
        if age <= 20:
            age_factor = 1.3
        elif age <= 25:
            age_factor = 1.1
        else:
            age_factor = 0.9
        
        # Adjusted score
        performance_score = total_contributions * age_factor
        
        # Confidence adjustment
        confidence_factor = confidence / 100
        final_score = performance_score * (0.7 + 0.3 * confidence_factor)
        
        # Generate recommendation
        if final_score >= 20 and confidence >= 60:
            decision = "STRONG BUY"
            reasoning = f"Excellent output ({total_contributions} contributions) with good data confidence"
        elif final_score >= 15 and confidence >= 50:
            decision = "BUY"
            reasoning = f"Strong performance ({total_contributions} contributions) justifies acquisition"
        elif final_score >= 10 or confidence >= 40:
            decision = "MONITOR"
            reasoning = f"Promising profile ({total_contributions} contributions) worth tracking"
        elif confidence >= 30:
            decision = "SCOUT FURTHER"
            reasoning = "Interesting profile but needs more detailed analysis"
        else:
            decision = "INSUFFICIENT DATA"
            reasoning = "Limited information available for proper assessment"
        
        return {
            'decision': decision,
            'reasoning': reasoning,
            'confidence': round(confidence_factor * 100, 1),
            'performance_score': round(final_score, 1)
        }
    
    def _get_search_strategies(self, search_type: str) -> list:
        """Get list of search strategies used"""
        
        strategies = {
            'youth': ['Youth tournament search', 'Academy database search', 'Age category filtering'],
            'unknown': ['Context-enhanced search', 'Multi-site aggregation', 'Name extraction'],
            'specific': ['Direct player search', 'Stats aggregation', 'Transfer market analysis'],
            'general': ['Broad criteria search', 'League filtering', 'Position-based search']
        }
        
        return strategies.get(search_type, ['Standard search'])
    
    def _assess_data_coverage(self, profiles: list) -> str:
        """Assess how complete the data coverage is"""
        
        if not profiles:
            return "No profiles found"
        
        # Check data completeness for top profile
        top_profile = profiles[0] if profiles else {}
        fields = ['name', 'age', 'position', 'goals', 'assists', 'club']
        covered = sum(1 for f in fields if top_profile.get(f))
        
        coverage_pct = (covered / len(fields)) * 100
        
        if coverage_pct >= 80:
            return "Excellent"
        elif coverage_pct >= 60:
            return "Good"
        elif coverage_pct >= 40:
            return "Moderate"
        else:
            return "Limited"

def format_enhanced_report(report: dict) -> str:
    """Format report in markdown with better structure"""
    
    md = f"""# ⚽ APES Football Scout Report

**Query:** {report['metadata']['query']}  
**Search Type:** {report['metadata']['search_type'].title()}  
**Generated:** {report['metadata']['generated_at']}  
**Data Quality:** {report['metadata']['data_quality_score']}/100

## 📊 Search Summary
- **Search Difficulty:** {report['search_summary']['difficulty'].title()}
- **Profiles Found:** {report['search_summary']['profiles_found']}
- **Data Coverage:** {report['search_summary']['data_coverage']}
- **Total Sources:** {report['metadata']['total_sources']}
- **Sources Scraped:** {report['metadata']['scraped_sources']}

## 🎯 Player Recommendations
"""
    
    if report['recommendations']:
        for i, rec in enumerate(report['recommendations'], 1):
            profile = rec['profile']
            md += f"""
### {i}. {rec['player']}
**Decision:** {rec['decision']}  
**Confidence:** {rec['confidence']}%  
**Reasoning:** {rec['reasoning']}

**Profile Details:**
- **Age:** {profile.get('age', 'Unknown')}
- **Position:** {profile.get('position', 'Unknown')}
- **Club:** {profile.get('club', 'Unknown')}
- **Goals:** {profile.get('goals', 'N/A')}
- **Assists:** {profile.get('assists', 'N/A')}
- **Market Value:** {profile.get('market_value', 'Unknown')}
- **Sources:** {', '.join(profile.get('sources', [])[:3])}

---
"""
    else:
        md += """
*No specific player profiles could be extracted from the search results.*

### 🔍 Search Strategies Used:
"""
        for strategy in report['search_summary']['search_strategies_used']:
            md += f"- {strategy}\n"
    
    # Add query analysis insights
    analysis = report['metadata']['query_analysis']
    if analysis['indicators']['youth']:
        md += "\n### 🎓 Youth Player Search\n"
        md += "Focused on youth academies and development leagues.\n"
    
    if analysis['indicators']['position']['found']:
        md += f"\n### 📍 Position Focus: {analysis['indicators']['position']['type']}\n"
    
    if analysis['indicators']['nationality']['found']:
        md += f"\n### 🌍 Nationality: {analysis['indicators']['nationality']['type']}\n"
    
    md += """
---
*Generated by APES Football Scout v4.0 - Specialized in finding unknown talents*
"""
    
    return md

def display_player_card(profile: dict, recommendation: dict):
    """Display a player card with visual formatting"""
    
    # Determine card color based on recommendation
    color_map = {
        'STRONG BUY': '#28a745',
        'BUY': '#17a2b8',
        'MONITOR': '#ffc107',
        'SCOUT FURTHER': '#fd7e14',
        'INSUFFICIENT DATA': '#6c757d'
    }
    
    color = color_map.get(recommendation['decision'], '#6c757d')
    
    # Create styled card
    st.markdown(f"""
    <div style="border: 2px solid {color}; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: rgba(255,255,255,0.05);">
        <h3 style="color: {color}; margin: 0;">{profile.get('name', 'Unknown Player')}</h3>
        <p style="color: {color}; font-weight: bold; margin: 5px 0;">{recommendation['decision']} - {recommendation['confidence']}% confidence</p>
        <hr style="border-color: {color}; opacity: 0.3;">
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
            <div><strong>Age:</strong> {profile.get('age', 'Unknown')}</div>
            <div><strong>Position:</strong> {profile.get('position', 'Unknown')}</div>
            <div><strong>Goals:</strong> {profile.get('goals', 'N/A')}</div>
            <div><strong>Assists:</strong> {profile.get('assists', 'N/A')}</div>
            <div><strong>Club:</strong> {profile.get('club', 'Unknown')}</div>
            <div><strong>Value:</strong> {profile.get('market_value', 'Unknown')}</div>
        </div>
        <p style="margin-top: 10px; font-style: italic;">{recommendation['reasoning']}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.title("🦍⚽ APES Football Scout v4.0")
    st.markdown("### AI-Powered Scout Specialized in Finding Unknown Talents")
    
    # Check API configuration
    api_configured = bool(st.secrets.get("GOOGLE_CSE_API_KEY"))
    
    if api_configured:
        st.success("✅ Google CSE API Configured")
    else:
        st.error("❌ Google CSE API Key Missing")
        st.info("""
        To use this app, add your Google Custom Search API key to `.streamlit/secrets.toml`:
        ```
        GOOGLE_CSE_API_KEY = "your-api-key-here"
        ```
        """)
        st.stop()
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Scout Configuration")
    
    search_mode = st.sidebar.radio(
        "Search Mode",
        ["Auto-Detect", "Specific Player", "Youth Academy", "Unknown Talent"],
        help="Choose how to approach the search"
    )
    
    search_type_map = {
        "Auto-Detect": "auto",
        "Specific Player": "specific",
        "Youth Academy": "youth",
        "Unknown Talent": "unknown"
    }
    
    enable_deep_scraping = st.sidebar.checkbox(
        "Enable Deep Scraping",
        value=True,
        help="Extract more data by analyzing page content (slower but more accurate)"
    )
    
    export_format = st.sidebar.selectbox(
        "Export Format",
        ["Markdown", "JSON", "Both"]
    )
    
    # Feature showcase
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Enhanced Features")
    st.sidebar.info("""
    **v4.0 Improvements:**
    - 🔍 Multi-strategy search for unknown players
    - 🎯 Youth academy database integration
    - 📊 Player name extraction from articles
    - 🧠 Context-aware search expansion
    - 💎 Profile consolidation from multiple sources
    """)
    
    # Search examples
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 Search Examples")
    
    if search_mode == "Youth Academy":
        examples = [
            "Primavera Inter attaccante",
            "Milan U19 trequartista",
            "Juventus youth striker 2024",
            "Roma academy midfielder goals"
        ]
    elif search_mode == "Unknown Talent":
        examples = [
            "centrocampista argentino Serie C gol",
            "young Brazilian striker Italy",
            "attaccante veloce Primavera 2024",
            "left footed midfielder Serie B"
        ]
    else:
        examples = [
            "Federico Chiesa",
            "Khvicha Kvaratskhelia stats",
            "Victor Osimhen market value",
            "Rafael Leão 2024 performance"
        ]
    
    # Example buttons
    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = None
    
    for example in examples:
        if st.sidebar.button(f"🔍 {example}", key=f"ex_{example.replace(' ', '_')}"):
            st.session_state.selected_example = example
    
    # Main search interface
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        default_value = st.session_state.selected_example if st.session_state.selected_example else ""
        
        query = st.text_input(
            "🔍 Search Query",
            value=default_value,
            placeholder="Enter player name or search criteria...",
            help="Be specific: include position, age category, nationality, or league"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button(
            "🚀 Scout",
            type="primary",
            use_container_width=True
        )
    
    # Search execution
    if search_button and query:
        st.markdown("---")
        
        # Initialize scout
        scout = AdvancedFootballScout()
        
        # Show search configuration
        st.info(f"""
        🔍 **Search Configuration**  
        Mode: {search_mode} | Deep Scraping: {'Enabled' if enable_deep_scraping else 'Disabled'}
        """)
        
        # Execute search
        with st.container():
            report = scout.comprehensive_scout(
                query,
                search_mode=search_type_map[search_mode],
                enable_deep_scraping=enable_deep_scraping
            )
            
            # Display results
            st.success(f"✅ Analysis completed for: **{query}**")
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Data Quality",
                    f"{report['metadata']['data_quality_score']}/100"
                )
            
            with col2:
                st.metric(
                    "Profiles Found",
                    report['search_summary']['profiles_found']
                )
            
            with col3:
                st.metric(
                    "Sources Analyzed",
                    report['metadata']['total_sources']
                )
            
            with col4:
                st.metric(
                    "Data Coverage",
                    report['search_summary']['data_coverage']
                )
            
            # Player recommendations
            if report['recommendations']:
                st.markdown("### 🎯 Player Recommendations")
                
                for rec in report['recommendations']:
                    display_player_card(rec['profile'], rec)
            else:
                st.warning("""
                ⚠️ No specific player profiles found. This could mean:
                - The player is very unknown or plays in lower leagues
                - Try adding more context (team, league, nationality)
                - The search terms might be too generic
                """)
                
                # Show what was searched
                st.markdown("### 🔍 Search Strategies Used")
                for strategy in report['search_summary']['search_strategies_used']:
                    st.write(f"- {strategy}")
            
            # Advanced details
            with st.expander("📊 Detailed Search Analysis"):
                # Query analysis
                analysis = report['metadata']['query_analysis']
                
                st.markdown("#### Query Understanding")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Indicators Found:**")
                    indicators = analysis['indicators']
                    if indicators['youth']:
                        st.write("- 🎓 Youth player search")
                    if indicators['position']['found']:
                        st.write(f"- 📍 Position: {indicators['position']['type']}")
                    if indicators['nationality']['found']:
                        st.write(f"- 🌍 Nationality: {indicators['nationality']['type']}")
                    if indicators['league']['found']:
                        st.write(f"- 🏆 League: {indicators['league']['type']}")
                
                with col2:
                    st.write("**Search Analysis:**")
                    st.write(f"- Difficulty: {analysis['search_difficulty'].title()}")
                    st.write(f"- Query Type: {analysis['query_type'].replace('_', ' ').title()}")
                    if indicators['attributes']:
                        st.write(f"- Attributes: {', '.join(indicators['attributes'])}")
            
            # Raw results sample
            with st.expander("🔗 Source Documents"):
                for i, result in enumerate(report['raw_results'][:5], 1):
                    st.markdown(f"""
                    **{i}. {result.get('source', 'Unknown')}**  
                    {result.get('title', 'No title')}  
                    *{result.get('snippet', 'No snippet available')}*
                    """)
                    if result.get('url'):
                        st.markdown(f"[View Source]({result['url']})")
                    st.markdown("---")
            
            # Export section
            st.markdown("### 📤 Export Report")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"apes_scout_{query.replace(' ', '_')}_{timestamp}"
            
            col1, col2 = st.columns(2)
            
            with col1:
                if export_format in ["Markdown", "Both"]:
                    md_report = format_enhanced_report(report)
                    st.download_button(
                        "📝 Download Markdown Report",
                        md_report,
                        f"{filename_base}.md",
                        "text/markdown"
                    )
            
            with col2:
                if export_format in ["JSON", "Both"]:
                    json_report = json.dumps(report, indent=2, ensure_ascii=False)
                    st.download_button(
                        "📊 Download JSON Data",
                        json_report,
                        f"{filename_base}.json",
                        "application/json"
                    )
    
    elif search_button and not query:
        st.warning("⚠️ Please enter a search query")
    
    # Help section
    if not search_button:
        st.markdown("---")
        st.markdown("### 📚 How to Find Unknown Players")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎯 Be Specific**
            - Include position + nationality
            - Add age category (U19, Primavera)
            - Mention league or level
            - Include year for recent stats
            """)
        
        with col2:
            st.markdown("""
            **🔍 Search Tips**
            - Use Italian terms for Italian leagues
            - Combine multiple attributes
            - Try team + position combos
            - Add "goals" or "assists" for stats
            """)
        
        with col3:
            st.markdown("""
            **📊 Best Practices**
            - Enable deep scraping for unknowns
            - Try multiple search variations
            - Check youth tournaments
            - Look for match reports
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
        <strong>🦍 APES Football Scout v4.0</strong><br>
        Enhanced Unknown Player Discovery • Multi-Strategy Search • Advanced Data Extraction<br>
        <small>Specialized in finding hidden talents in youth academies and lower leagues</small>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

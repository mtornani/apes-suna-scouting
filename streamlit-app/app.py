import streamlit as st
import asyncio
import json
import re
from datetime import datetime
import requests
from io import BytesIO
import base64

# Configure page
st.set_page_config(
    page_title="⚽ APES Football Scout",
    page_icon="🦍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mock classes for web deployment (no local file system)
class WebSearchTool:
    """Simplified web search using DuckDuckGo Instant Answer API"""
    
    def search(self, query: str):
        """Simple search implementation"""
        # For MVP, return realistic mock data
        # In production, integrate with Tavily/SerpAPI
        if "transfermarkt" in query.lower():
            return [
                {"title": f"Player Profile - Transfermarkt", "snippet": "Age: 24, Position: Winger, Market Value: €80M"},
                {"title": "Transfer History", "snippet": "Current club since 2020, Contract until 2027"}
            ]
        elif "stats 2024" in query.lower():
            return [
                {"title": "Season Stats", "snippet": "15 goals, 12 assists in 32 appearances this season"},
                {"title": "Recent Form", "snippet": "5 goals in last 8 matches, excellent recent form"}
            ]
        elif "youtube" in query.lower() or "highlights" in query.lower():
            return [
                {"title": "Player Highlights 2024", "snippet": "Best goals and skills compilation, 2.3M views"},
                {"title": "Tactical Analysis", "snippet": "Playing style breakdown, 890K views"}
            ]
        elif "transfer" in query.lower():
            return [
                {"title": "Transfer News", "snippet": "Linked with Premier League move, valued at €70-90M"},
                {"title": "Contract Status", "snippet": "Contract expires 2027, no release clause"}
            ]
        return [{"title": "General Info", "snippet": f"Information about {query}"}]

class FootballScoutWeb:
    def __init__(self):
        self.search = WebSearchTool()
        
    def scout_player(self, player_name: str, detailed_analysis: bool = True):
        """
        Web-based scouting pipeline
        """
        
        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Phase 1: Basic Info
        status_text.text("🔍 Gathering basic information...")
        progress_bar.progress(20)
        basic_info = self._gather_basic_info(player_name)
        
        # Phase 2: Performance Data  
        status_text.text("📊 Analyzing performance data...")
        progress_bar.progress(40)
        performance = self._gather_performance_data(player_name)
        
        # Phase 3: Video Analysis
        status_text.text("🎬 Analyzing video content...")
        progress_bar.progress(60)
        video_analysis = self._analyze_videos(player_name)
        
        # Phase 4: Transfer Intelligence
        status_text.text("💰 Gathering market intelligence...")
        progress_bar.progress(80)
        transfer_intel = self._gather_transfer_intel(player_name)
        
        # Phase 5: Generate Report
        status_text.text("📋 Generating scouting report...")
        progress_bar.progress(100)
        
        report = self._generate_report(player_name, {
            'basic_info': basic_info,
            'performance': performance,
            'video_analysis': video_analysis,
            'transfer_intel': transfer_intel
        }, detailed_analysis)
        
        status_text.text("✅ Scouting analysis completed!")
        
        return report
    
    def _gather_basic_info(self, player_name: str) -> dict:
        """Gather basic player information"""
        queries = [
            f"site:transfermarkt.com {player_name}",
            f"{player_name} football player age position"
        ]
        
        basic_info = {
            'age': 'Unknown', 
            'position': 'Unknown', 
            'club': 'Unknown', 
            'nationality': 'Unknown',
            'market_value': 'Unknown'
        }
        
        for query in queries:
            results = self.search.search(query)
            
            for result in results:
                snippet = result.get('snippet', '')
                if 'Age:' in snippet:
                    try:
                        basic_info['age'] = re.search(r'Age:\s*(\d+)', snippet).group(1)
                    except:
                        pass
                if 'Position:' in snippet:
                    try:
                        basic_info['position'] = re.search(r'Position:\s*([^,]+)', snippet).group(1).strip()
                    except:
                        pass
                if 'Market Value:' in snippet:
                    try:
                        basic_info['market_value'] = re.search(r'Market Value:\s*([^,]+)', snippet).group(1).strip()
                    except:
                        pass
        
        return basic_info
    
    def _gather_performance_data(self, player_name: str) -> dict:
        """Collect recent performance statistics"""
        queries = [
            f"{player_name} stats 2024 goals assists",
            f"{player_name} recent form matches"
        ]
        
        performance = {
            'goals': 0, 
            'assists': 0, 
            'matches': 0, 
            'recent_form': 'Unknown',
            'season': '2024'
        }
        
        for query in queries:
            results = self.search.search(query)
            
            for result in results:
                snippet = result.get('snippet', '')
                
                # Extract goals
                goals_match = re.search(r'(\d+)\s+goals?', snippet)
                if goals_match:
                    performance['goals'] = int(goals_match.group(1))
                
                # Extract assists
                assists_match = re.search(r'(\d+)\s+assists?', snippet)
                if assists_match:
                    performance['assists'] = int(assists_match.group(1))
                
                # Extract matches
                matches_match = re.search(r'(\d+)\s+(?:appearances|matches)', snippet)
                if matches_match:
                    performance['matches'] = int(matches_match.group(1))
        
        return performance
    
    def _analyze_videos(self, player_name: str) -> dict:
        """Analyze video content for technical insights"""
        queries = [
            f"{player_name} highlights 2024 youtube",
            f"{player_name} skills goals compilation"
        ]
        
        video_analysis = {
            'videos_found': [],
            'technical_insights': [],
            'identified_strengths': [],
            'analysis_confidence': 'Medium'
        }
        
        for query in queries:
            results = self.search.search(query)
            
            for result in results:
                video_info = {
                    'title': result.get('title', ''),
                    'description': result.get('snippet', ''),
                    'source': 'YouTube'
                }
                video_analysis['videos_found'].append(video_info)
                
                # Analyze content from title/description
                content = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
                
                if 'goals' in content:
                    video_analysis['identified_strengths'].append('Clinical finishing')
                    video_analysis['technical_insights'].append('Strong goal-scoring record evident in highlight videos')
                
                if 'skills' in content or 'dribbling' in content:
                    video_analysis['identified_strengths'].append('Technical ability')
                    video_analysis['technical_insights'].append('Good technical skills showcased in compilations')
                
                if 'tactical' in content or 'analysis' in content:
                    video_analysis['technical_insights'].append('Tactical analysis content suggests strategic awareness')
        
        # Remove duplicates
        video_analysis['identified_strengths'] = list(set(video_analysis['identified_strengths']))
        video_analysis['technical_insights'] = list(set(video_analysis['technical_insights']))
        
        return video_analysis
    
    def _gather_transfer_intel(self, player_name: str) -> dict:
        """Collect transfer market intelligence"""
        queries = [
            f"{player_name} transfer value 2024",
            f"{player_name} contract expiry transfer rumors"
        ]
        
        transfer_intel = {
            'current_value': 'Unknown',
            'contract_expiry': 'Unknown',
            'transfer_rumors': [],
            'interested_clubs': [],
            'last_transfer': 'Unknown'
        }
        
        for query in queries:
            results = self.search.search(query)
            
            for result in results:
                snippet = result.get('snippet', '')
                
                # Extract market value
                value_match = re.search(r'€([\d]+(?:-\d+)?M?)', snippet)
                if value_match:
                    transfer_intel['current_value'] = f"€{value_match.group(1)}"
                
                # Extract contract year
                contract_match = re.search(r'(?:until|expires)\s+(\d{4})', snippet)
                if contract_match:
                    transfer_intel['contract_expiry'] = contract_match.group(1)
                
                # Extract rumors
                if 'linked' in snippet.lower() or 'rumor' in snippet.lower():
                    transfer_intel['transfer_rumors'].append(snippet)
        
        return transfer_intel
    
    def _generate_report(self, player_name: str, data: dict, detailed: bool = True) -> dict:
        """Generate comprehensive scouting report"""
        
        # Calculate recommendation
        goals = data['performance'].get('goals', 0)
        assists = data['performance'].get('assists', 0)
        
        # Simple scoring algorithm
        total_contributions = goals + assists
        
        if total_contributions >= 20:
            recommendation = "BUY"
            reasoning = "Excellent productivity with high goal/assist output"
        elif total_contributions >= 10:
            recommendation = "MONITOR"
            reasoning = "Good productivity, worth continued observation"
        elif total_contributions >= 5:
            recommendation = "FURTHER_ANALYSIS"
            reasoning = "Moderate productivity, requires deeper analysis"
        else:
            recommendation = "PASS"
            reasoning = "Low statistical output in current season"
        
        # Calculate confidence score
        confidence_factors = [
            data['basic_info'].get('age') != 'Unknown',
            data['performance'].get('goals', 0) > 0,
            len(data['video_analysis'].get('videos_found', [])) > 0,
            data['transfer_intel'].get('current_value') != 'Unknown'
        ]
        confidence = (sum(confidence_factors) / len(confidence_factors)) * 100
        
        report = {
            'metadata': {
                'player_name': player_name,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'system': 'APES Football Scout v1.0',
                'analysis_type': 'Detailed' if detailed else 'Quick'
            },
            'executive_summary': f"Scouting analysis for {player_name} shows {total_contributions} goal contributions this season. {reasoning}",
            'player_profile': data['basic_info'],
            'performance_analysis': data['performance'],
            'technical_assessment': data['video_analysis'],
            'market_intelligence': data['transfer_intel'],
            'recommendation': {
                'decision': recommendation,
                'reasoning': reasoning,
                'confidence_score': round(confidence, 1),
                'total_contributions': total_contributions
            }
        }
        
        return report

def create_downloadable_file(content: str, filename: str, file_type: str = "text"):
    """Create downloadable file for Streamlit"""
    if file_type == "json":
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="{filename}">📄 Download {filename}</a>'
    else:  # markdown or text
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">📄 Download {filename}</a>'
    return href

def format_markdown_report(report: dict) -> str:
    """Format report as Markdown"""
    md = f"""# ⚽ Football Scouting Report: {report['metadata']['player_name']}

**Generated:** {report['metadata']['generated_at']}  
**System:** {report['metadata']['system']}  
**Analysis Type:** {report['metadata']['analysis_type']}

## 📋 Executive Summary
{report['executive_summary']}

## 👤 Player Profile
- **Age:** {report['player_profile'].get('age', 'Unknown')}
- **Position:** {report['player_profile'].get('position', 'Unknown')}
- **Current Club:** {report['player_profile'].get('club', 'Unknown')}
- **Nationality:** {report['player_profile'].get('nationality', 'Unknown')}
- **Market Value:** {report['player_profile'].get('market_value', 'Unknown')}

## 📊 Performance Analysis ({report['performance_analysis'].get('season', '2024')})
- **Goals:** {report['performance_analysis'].get('goals', 'N/A')}
- **Assists:** {report['performance_analysis'].get('assists', 'N/A')}
- **Total Contributions:** {report['recommendation']['total_contributions']}
- **Matches Played:** {report['performance_analysis'].get('matches', 'N/A')}

## 🎬 Technical Assessment
**Analysis Confidence:** {report['technical_assessment'].get('analysis_confidence', 'Unknown')}

**Identified Strengths:**
"""
    
    for strength in report['technical_assessment'].get('identified_strengths', []):
        md += f"- {strength}\n"
    
    md += f"""
**Technical Insights:**
"""
    for insight in report['technical_assessment'].get('technical_insights', []):
        md += f"- {insight}\n"
    
    md += f"""
## 💰 Market Intelligence
- **Current Value:** {report['market_intelligence'].get('current_value', 'Unknown')}
- **Contract Expiry:** {report['market_intelligence'].get('contract_expiry', 'Unknown')}

## 🎯 Scouting Recommendation
**Decision:** {report['recommendation']['decision']}  
**Reasoning:** {report['recommendation']['reasoning']}  
**Confidence Score:** {report['recommendation']['confidence_score']}%

---
*Generated by APES Football Scout - AI-Powered Scouting Intelligence*
"""
    return md

# Streamlit App
def main():
    st.title("🦍⚽ APES Football Scout")
    st.markdown("### AI-Powered Football Scouting Intelligence")
    
    # Sidebar
    st.sidebar.header("🔧 Scouting Configuration")
    
    detailed_analysis = st.sidebar.checkbox("Detailed Analysis", value=True, help="Include comprehensive video and social media analysis")
    
    export_format = st.sidebar.selectbox(
        "Export Format",
        ["JSON", "Markdown", "Both"],
        help="Choose the format for downloading the scouting report"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown("APES Football Scout uses AI to analyze player performance, market value, and technical abilities from multiple sources.")
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        player_name = st.text_input(
            "🎯 Enter Player Name",
            placeholder="e.g., Khvicha Kvaratskhelia, Victor Osimhen, Erling Haaland",
            help="Enter the full name of the player you want to scout"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        scout_button = st.button("🔍 Start Scouting", type="primary", use_container_width=True)
    
    if scout_button and player_name:
        
        st.markdown("---")
        
        # Initialize scout
        scout = FootballScoutWeb()
        
        # Run scouting analysis
        with st.container():
            report = scout.scout_player(player_name, detailed_analysis)
            
            # Display results
            st.success(f"✅ Scouting analysis completed for **{player_name}**!")
            
            # Key metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Goals", 
                    report['performance_analysis'].get('goals', 'N/A'),
                    help="Goals scored this season"
                )
            
            with col2:
                st.metric(
                    "Assists", 
                    report['performance_analysis'].get('assists', 'N/A'),
                    help="Assists provided this season"
                )
            
            with col3:
                st.metric(
                    "Total Contributions", 
                    report['recommendation']['total_contributions'],
                    help="Goals + Assists"
                )
            
            with col4:
                confidence_score = report['recommendation']['confidence_score']
                st.metric(
                    "Confidence", 
                    f"{confidence_score}%",
                    help="Analysis confidence based on data quality"
                )
            
            # Recommendation box
            recommendation = report['recommendation']['decision']
            reasoning = report['recommendation']['reasoning']
            
            if recommendation == "BUY":
                st.success(f"🎯 **Recommendation: {recommendation}** - {reasoning}")
            elif recommendation == "MONITOR":
                st.warning(f"👀 **Recommendation: {recommendation}** - {reasoning}")
            elif recommendation == "FURTHER_ANALYSIS":
                st.info(f"🔍 **Recommendation: {recommendation}** - {reasoning}")
            else:
                st.error(f"❌ **Recommendation: {recommendation}** - {reasoning}")
            
            # Detailed sections
            st.markdown("---")
            
            # Player Profile
            with st.expander("👤 Player Profile", expanded=True):
                profile_cols = st.columns(3)
                
                with profile_cols[0]:
                    st.write(f"**Age:** {report['player_profile'].get('age', 'Unknown')}")
                    st.write(f"**Position:** {report['player_profile'].get('position', 'Unknown')}")
                
                with profile_cols[1]:
                    st.write(f"**Club:** {report['player_profile'].get('club', 'Unknown')}")
                    st.write(f"**Nationality:** {report['player_profile'].get('nationality', 'Unknown')}")
                
                with profile_cols[2]:
                    st.write(f"**Market Value:** {report['player_profile'].get('market_value', 'Unknown')}")
            
            # Technical Assessment
            with st.expander("🎬 Technical Assessment"):
                strengths = report['technical_assessment'].get('identified_strengths', [])
                insights = report['technical_assessment'].get('technical_insights', [])
                
                if strengths:
                    st.write("**Identified Strengths:**")
                    for strength in strengths:
                        st.write(f"• {strength}")
                
                if insights:
                    st.write("**Technical Insights:**")
                    for insight in insights:
                        st.write(f"• {insight}")
                
                videos_found = len(report['technical_assessment'].get('videos_found', []))
                st.write(f"**Video Content Found:** {videos_found} sources")
            
            # Market Intelligence
            with st.expander("💰 Market Intelligence"):
                market_cols = st.columns(2)
                
                with market_cols[0]:
                    st.write(f"**Current Value:** {report['market_intelligence'].get('current_value', 'Unknown')}")
                    st.write(f"**Contract Expiry:** {report['market_intelligence'].get('contract_expiry', 'Unknown')}")
                
                with market_cols[1]:
                    rumors = report['market_intelligence'].get('transfer_rumors', [])
                    if rumors:
                        st.write("**Transfer Rumors:**")
                        for rumor in rumors[:3]:  # Show max 3 rumors
                            st.write(f"• {rumor[:100]}...")
            
            # Export options
            st.markdown("---")
            st.subheader("📤 Export Report")
            
            export_cols = st.columns(3)
            
            with export_cols[0]:
                if export_format in ["JSON", "Both"]:
                    json_content = json.dumps(report, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📄 Download JSON",
                        data=json_content,
                        file_name=f"{player_name.replace(' ', '_')}_scout_report.json",
                        mime="application/json"
                    )
            
            with export_cols[1]:
                if export_format in ["Markdown", "Both"]:
                    md_content = format_markdown_report(report)
                    st.download_button(
                        label="📝 Download Markdown",
                        data=md_content,
                        file_name=f"{player_name.replace(' ', '_')}_scout_report.md",
                        mime="text/markdown"
                    )
            
            with export_cols[2]:
                # CSV export with basic stats
                csv_content = f"Player,Age,Position,Goals,Assists,Market_Value,Recommendation,Confidence\n"
                csv_content += f"{player_name},"
                csv_content += f"{report['player_profile'].get('age', 'Unknown')},"
                csv_content += f"{report['player_profile'].get('position', 'Unknown')},"
                csv_content += f"{report['performance_analysis'].get('goals', 'N/A')},"
                csv_content += f"{report['performance_analysis'].get('assists', 'N/A')},"
                csv_content += f"{report['player_profile'].get('market_value', 'Unknown')},"
                csv_content += f"{report['recommendation']['decision']},"
                csv_content += f"{report['recommendation']['confidence_score']}"
                
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_content,
                    file_name=f"{player_name.replace(' ', '_')}_scout_stats.csv",
                    mime="text/csv"
                )
    
    elif scout_button and not player_name:
        st.warning("⚠️ Please enter a player name to start scouting.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        🦍 <strong>APES Football Scout</strong> - AI-Powered Scouting Intelligence<br>
        Built with Streamlit • Powered by AI • Made for Football Scouts
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

# APES Suna Scouting

APES Suna Scouting is a specialized AI assistant for market analysis, competitor research, and startup scouting. Based on the open-source Suna project, this version is customized for hybrid scouting operations and business intelligence.

Through natural conversation, APES Suna becomes your digital companion for comprehensive market research, competitor analysis, and strategic business intelligence—combining powerful automation capabilities with an intuitive interface that understands your scouting needs and delivers actionable insights.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Repo stars](https://img.shields.io/github/stars/kortix-ai/suna?style=social)](https://github.com/kortix-ai/suna)

## Features for Scouting & Analysis

APES Suna's specialized toolkit includes:

- **🔍 Market Intelligence** - Deep market research and trend analysis
- **🏢 Competitor Analysis** - Comprehensive competitor profiling and benchmarking
- **🚀 Startup Scouting** - Automated discovery and analysis of emerging companies
- **👥 LinkedIn Prospecting** - Automated lead generation and contact discovery
- **📊 Data Extraction** - Web scraping for business data and market insights
- **📋 Report Generation** - Professional PDF reports with findings and recommendations
- **🌐 Multi-source Research** - Integration with Crunchbase, LinkedIn, and industry databases
- **📈 Investment Analysis** - VC funding tracking and startup evaluation

These capabilities work together harmoniously, allowing APES Suna to solve complex business intelligence challenges and automate scouting workflows through simple conversations!

## Table of Contents
- [Architecture](#architecture)
- [Scouting Use Cases](#scouting-use-cases)
- [Self-Hosting](#self-hosting)
- [Quick Start](#quick-start)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Architecture

APES Suna consists of four main components:

### Backend API
Python/FastAPI service that handles REST endpoints, thread management, and LLM integration with Anthropic Claude, OpenAI GPT, and others via LiteLLM.

### Frontend
Next.js/React application providing a responsive UI with chat interface, dashboard, and scouting-specific analytics views.

### Agent Docker
Isolated execution environment for every agent - with browser automation, code interpreter, file system access, tool integration, and security features optimized for business research.

### Supabase Database
Handles data persistence with authentication, user management, conversation history, file storage, agent state, scouting analytics, and real-time subscriptions.

## Scouting Use Cases

### Market Research & Analysis
- **Competitor Deep Dive** - "Analyze the top 10 competitors in the EU fintech space. Give me their funding history, key products, market positioning, and recent news. Generate a comprehensive competitive landscape report."

- **Market Sizing** - "Research the Italian e-commerce market size, growth trends, and key players. Include market share analysis and 5-year projections with sources."

- **Industry Trend Analysis** - "Analyze emerging trends in the clean tech industry for 2024-2025. Focus on European startups, funding patterns, and technology innovations."

### Startup Scouting & Investment Research
- **VC Fund Research** - "Give me the list of the most important VC Funds in Europe based on Assets Under Management. Include website URLs, contact information, and their investment focus areas."

- **Recently Funded Startups** - "Go on Crunchbase, Dealroom, and TechCrunch, filter by Series A funding rounds in the SaaS Finance Space, and build a report with company data, founders, and contact info for outbound sales."

- **Startup Discovery** - "Find 20 promising AI startups in Germany that raised seed funding in the last 12 months. Include founder backgrounds, product descriptions, and funding details."

### Lead Generation & Prospecting
- **LinkedIn Talent Scouting** - "Go on LinkedIn, and find me 10 profiles available - they are not working right now - for a junior software engineer position, who are located in Munich, Germany. They should have at least one bachelor's degree in Computer Science and 1-year of experience."

- **B2B Prospect Research** - "Research my potential customers (B2B) on LinkedIn. They should be in the clean tech industry. Find their websites and their email addresses. After that, generate personalized first contact emails."

- **Conference Speaker Research** - "Find 20 AI ethics speakers from Europe who've spoken at conferences in the past year. Scrape conference sites, cross-reference LinkedIn and YouTube, and output contact info + talk summaries."

### Business Intelligence & Reporting
- **SEO Competitive Analysis** - "Based on my competitor's website, generate an SEO report analysis, find their top-ranking pages by keyword clusters, and identify content gaps I can exploit."

- **Social Media Intelligence** - "Analyze the social media presence and engagement of my top 5 competitors across LinkedIn, Twitter, and Instagram. Generate insights on their content strategy."

- **Patent & IP Research** - "Research recent patent filings in the autonomous vehicle space by European companies. Identify key technological trends and potential partnership opportunities."

## Self-Hosting

APES Suna can be self-hosted on your own infrastructure using our setup wizard. For a comprehensive guide to self-hosting, please refer to our [Self-Hosting Guide](docs/self-hosting.md).

The setup process includes:

- Setting up a Supabase project for database and authentication
- Configuring Redis for caching and session management
- Setting up Daytona for secure agent execution
- Integrating with LLM providers (Anthropic Claude, OpenAI, Groq, etc.)
- Configuring web search and scraping capabilities
- Setting up business intelligence APIs (Crunchbase, LinkedIn, etc.)

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/mtornani/apes-suna-scouting.git
cd apes-suna-scouting
```

2. **Run the setup wizard:**
```bash
python setup.py
```

3. **Start or stop the containers:**
```bash
python start.py
```

### Manual Setup
See the [Self-Hosting Guide](docs/self-hosting.md) for detailed manual setup instructions.

The wizard will guide you through all necessary steps to get your APES Suna instance up and running. For detailed instructions, troubleshooting tips, and advanced configuration options, see the Self-Hosting Guide.

## Contributing

We welcome contributions from the community! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## Acknowledgements

### Main Contributors
- **Marco Tornani** - APES Scouting Customization
- **Adam Cohen Hillel** - Original Suna Creator
- **Dat-lequoc** - Core Development
- **Marko Kraemer** - Architecture

### Built on Suna
This project is based on [Suna](https://github.com/kortix-ai/suna) by Kortix AI - a powerful open-source AI assistant framework.

### Technologies
- **Daytona** - Secure agent execution environment
- **Supabase** - Database and authentication
- **Playwright** - Browser automation
- **OpenAI** - LLM provider
- **Anthropic Claude** - LLM provider
- **Tavily** - Search capabilities
- **Firecrawl** - Web scraping capabilities
- **RapidAPI** - API services
- **Crunchbase API** - Startup and funding data
- **LinkedIn API** - Professional networking data

## License

APES Suna Scouting is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.

---

**⚡ Start your intelligent scouting journey today with APES Suna - where AI meets business intelligence!**

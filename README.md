# 🐋 WhaleFlow Intelligence

**AI-Powered Cryptocurrency Investment Platform**

WhaleFlow Intelligence is an advanced crypto investment analysis platform that leverages artificial intelligence to track whale traders, validate market conditions, and forecast performance. The platform uses a sophisticated multi-agent system to provide comprehensive investment insights for Bitcoin (BTC), Ethereum (ETH), Solana (SOL), and HYPE tokens.

![WhaleFlow Intelligence](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Features

### 🧠 Multi-Agent AI System
- **Agent 1: Whale Detector** - Identifies top-performing whale traders for specific cryptocurrencies
- **Agent 2: Market Validator** - Provides dual-timeframe analysis (short-term technical + long-term whale patterns)
- **Agent 3: Performance Forecaster** - Generates detailed forecasts with conversational investment guidance

### 📊 Real-Time Market Analysis
- Live technical indicator analysis via MCP (Model Context Protocol) integration
- RSI, MACD, Moving Averages, Support/Resistance levels
- Volume analysis and Bollinger Bands positioning
- Stochastic oscillator readings

### 🏟️ Arena Playground
- Interactive whale trading simulator
- Real-time market scenarios for skill building
- Performance tracking and skill level progression
- Educational feedback on trading decisions

### 🎯 Investment Intelligence
- Short-term (1-4 weeks) and long-term (3-12 months) forecasts
- Whale trading pattern analysis
- Risk assessment and position sizing recommendations
- Performance visualization with interactive charts

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Jenius MCP Token (for real-time market data)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/whaleflow-intelligence.git
cd whaleflow-intelligence
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MCP Server Configuration (for real-time market data)
JENIUS_MCP_TOKEN=your_jenius_mcp_token_here
```

### 4. Prepare Whale Data
Ensure you have a whale trading data file named `data - Sheet1.csv` in the root directory with the following columns:

| Column Name | Description | Type |
|-------------|-------------|------|
| Whale ID | Unique identifier for whale trader | String |
| Wallet Address | Blockchain wallet address | String |
| Whale Name | Display name for whale | String |
| Total Portfolio ($) | Total portfolio value | Numeric |
| Asset | Cryptocurrency symbol (BTC, ETH, SOL, HYPE) | String |
| Direction | Trading direction (Long/Short) | String |
| Position Size ($) | Current position value | Numeric |
| Amount | Amount of tokens held | Numeric |
| PnL ($) | Profit/Loss in dollars | Numeric |
| PnL % | Profit/Loss percentage | Numeric |
| Leverage | Leverage multiplier | String/Numeric |
| Entry Price | Entry price for position | Numeric |
| Current Price | Current market price | Numeric |
| Weekly PnL ($) | Weekly profit/loss | Numeric |
| Win Rate (%) | Historical win percentage | Numeric |
| Avg Trade Size ($) | Average trade size | Numeric |
| Risk Score | Risk assessment (1-10) | Numeric |
| Last Active | Last activity timestamp | String |
| Confidence | Confidence level (0-100) | Numeric |

### 5. Custom Styling (Optional)
Create a `style.css` file for custom styling or use the default Streamlit theme.

## 🚀 Running the Application

### Start the Application
```bash
streamlit run main.py
```

The application will be available at `http://localhost:8501`

### Command Line Options
```bash
# Run on specific port
streamlit run main.py --server.port 8502

# Run with custom configuration
streamlit run main.py --server.headless true --server.enableCORS false
```

## 📖 Usage Guide

### 🔍 Whale Analysis Tab

#### 1. Investment Query
Ask natural language questions about cryptocurrency investments:
- "Should I invest in BTC?"
- "What about ETH for long term?"
- "Is SOL good for short term trading?"
- "Tell me about HYPE investment potential"

#### 2. Timeframe Specification
Specify your investment timeframe for targeted analysis:
- **Short-term**: "BTC short term analysis"
- **Long-term**: "ETH long term investment"
- **Both**: "Complete analysis of SOL" (default)

#### 3. Agent Workflow
1. **Agent 1** identifies the best-performing whale for your chosen asset
2. **Agent 2** provides market validation based on your timeframe preference
3. **Agent 3** generates performance forecasts and conversational guidance

### 🏟️ Arena Playground Tab

#### 1. Skill Development
- Select a cryptocurrency (BTC, ETH, SOL, HYPE)
- Click "Start New Scenario" to begin
- Answer trading scenarios based on real market data
- Receive immediate feedback and educational insights

#### 2. Performance Tracking
- **Arena Score**: Cumulative points from correct answers
- **Scenarios Played**: Total number of scenarios completed
- **Accuracy**: Success rate percentage
- **Skill Level**: Progressive ranking system

#### 3. Skill Levels
- 🦐 **Shrimp Trader**: 0-19 points
- 🐟 **Fish Trader**: 20-49 points
- 🦈 **Shark Trader**: 50-99 points
- 🐋 **Whale Master**: 100+ points

## 🏗️ Architecture

### Multi-Agent System
```
User Query → Agent 1 (Whale Detection) → Agent 2 (Market Validation) → Agent 3 (Performance Forecast) → Final Response
```

### Agent Responsibilities

#### Agent 1: Whale Analyzer
- Extracts asset from user query
- Identifies best-performing whale for specific asset
- Calculates performance scores based on multiple factors
- Provides detailed whale profile and trading summary

#### Agent 2: Market Validator
- Determines analysis timeframe from user query
- Fetches real-time technical data via MCP server
- Analyzes whale trading patterns for long-term insights
- Provides dual-timeframe analysis when appropriate

#### Agent 3: Performance Forecaster
- Generates forecasts using Agent 2's data
- Creates price target predictions
- Develops interactive charts and visualizations
- Provides conversational investment summaries

### Arena System

#### Arena Agent 1: Technical Analyzer
- Connects to MCP server for real-time market data
- Extracts technical indicators (RSI, MACD, Moving Averages)
- Handles fallback scenarios when live data unavailable
- Generates realistic indicator values for simulation

#### Arena Agent 2: Scenario Creator
- Creates trading scenarios using real technical data
- Develops educational multiple-choice questions
- Evaluates user responses with detailed feedback
- Tracks performance and provides technical insights

## 📊 Data Sources

### Whale Trading Data
- Primary source: `data - Sheet1.csv`
- Contains historical and current whale trading positions
- Includes performance metrics and risk assessments

### Real-Time Market Data
- Source: Jenius MCP Server
- Technical indicators and price data
- Volume analysis and market momentum
- Support/resistance levels

### Fallback Data
- AI-generated realistic market indicators
- Used when live data is unavailable
- Maintains educational value for Arena scenarios

## 🔧 Configuration

### Environment Variables
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| OPENAI_API_KEY | Yes | OpenAI API access key | sk-... |
| JENIUS_MCP_TOKEN | Yes | MCP server authentication token | Bearer token |

### Model Configuration
- **Primary Model**: GPT-4-1106-preview (for detailed analysis)
- **Arena Model**: GPT-4o (for real-time scenarios)
- **Parsing Model**: GPT-4o-mini (for efficient data extraction)

### Supported Cryptocurrencies
- **BTC** (Bitcoin)
- **ETH** (Ethereum)
- **SOL** (Solana)
- **HYPE** (Hype Token)

## 🐛 Troubleshooting

### Common Issues

#### 1. "Whale data file not found"
**Solution**: Ensure `data - Sheet1.csv` exists in the root directory with proper column structure.

#### 2. "JENIUS_MCP_TOKEN environment variable is not set"
**Solution**: Add your MCP token to the `.env` file or set it as an environment variable.

#### 3. "Agent 2 Error" or MCP connection issues
**Solution**: 
- Verify MCP token is valid and not expired
- Check internet connection
- The system will use fallback AI-generated data if MCP fails

#### 4. Missing columns in CSV
**Solution**: Ensure all required columns are present in the whale data file. Check the data structure section above.

#### 5. Streamlit performance issues
**Solution**: 
- Reduce the size of the whale data file
- Clear Streamlit cache: `streamlit cache clear`
- Restart the application

### Performance Optimization

#### Memory Management
- The application automatically cleans whale data on load
- Large datasets are processed in chunks
- Session state is managed efficiently

#### API Rate Limits
- OpenAI API calls are optimized for token usage
- Streaming responses reduce perceived latency
- Fallback mechanisms prevent service disruption

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for functions and classes
- Maintain consistent naming conventions

### Testing
- Test with different whale data formats
- Verify MCP server integration
- Test arena scenarios with various market conditions
- Ensure responsive design on different screen sizes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and API access
- **Streamlit** for the web application framework
- **Plotly** for interactive data visualizations
- **Jenius MCP** for real-time market data integration

## 📞 Support

For support, questions, or feature requests:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the usage guide for common scenarios

## 🔄 Version History

### v1.0.0 (Current)
- Multi-agent AI system with whale detection
- Dual-timeframe market analysis
- Arena playground for skill development
- Real-time technical indicator integration
- Interactive performance forecasting

---

**Built with ❤️ for the crypto trading community**

*WhaleFlow Intelligence - Follow the whales, master the markets*


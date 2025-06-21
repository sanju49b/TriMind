import streamlit as st
import pandas as pd
import json
import os
from openai import OpenAI
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import re
from dotenv import load_dotenv
import textwrap

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def local_css(file_name):
    """Function to load a local CSS file."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found. Using default theme.")

# Set page config
st.set_page_config(
    page_title="Trading Intelligence Platform", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Load custom CSS
local_css("style.css")

def load_whale_data():
    """Load whale trading data with proper column handling"""
    try:
        # Try different possible file names
        possible_files = ['data - Sheet1.csv', 'whale_data.csv', 'data.csv']
        df = None
        
        for filename in possible_files:
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                break
        
        if df is None:
            return None
        
        # Expected columns based on your specification
        expected_columns = [
            'Whale ID', 'Wallet Address', 'Whale Name', 'Total Portfolio ($)', 
            'Asset', 'Direction', 'Position Size ($)', 'Amount', 'PnL ($)', 
            'PnL %', 'Leverage', 'Entry Price', 'Current Price', 'Weekly PnL ($)', 
            'Win Rate (%)', 'Avg Trade Size ($)', 'Risk Score', 'Last Active', 'Confidence'
        ]
        
        # Clean column names (remove extra spaces, fix encoding issues)
        df.columns = df.columns.str.strip()
        
        # Check which columns are missing
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.warning(f"⚠️ Missing columns: {missing_columns}")
            st.info(f"📊 Available columns: {list(df.columns)}")
        
        # Ensure essential columns exist
        essential_columns = ['Whale ID', 'Whale Name', 'Asset', 'Win Rate (%)', 'PnL %', 'Confidence']
        available_essential = [col for col in essential_columns if col in df.columns]
        
        if len(available_essential) < 4:  # Need at least 4 essential columns
            st.error(f"❌ Not enough essential columns. Need: {essential_columns}")
            return None
        
        # Clean and validate data
        df = clean_whale_data(df)
        
        return df
        
    except FileNotFoundError:
        st.error("❌ Whale data file not found. Please upload a CSV file with whale trading data.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None

def clean_whale_data(df):
    """Clean and validate whale data"""
    try:
        # Convert percentage columns
        percentage_cols = ['Win Rate (%)', 'PnL %']
        for col in percentage_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert dollar columns
        dollar_cols = ['Total Portfolio ($)', 'Position Size ($)', 'PnL ($)', 'Weekly PnL ($)', 'Avg Trade Size ($)']
        for col in dollar_cols:
            if col in df.columns:
                # Remove $ and , if present
                df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert price columns
        price_cols = ['Entry Price', 'Current Price']
        for col in price_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean text columns
        text_cols = ['Whale ID', 'Whale Name', 'Asset', 'Direction']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Fill missing values
        if 'Confidence' in df.columns:
            df['Confidence'] = pd.to_numeric(df['Confidence'], errors='coerce')
            if hasattr(df['Confidence'], 'fillna'):
                df['Confidence'] = df['Confidence'].fillna(50.0)
        
        # Remove rows with missing essential data
        essential_cols = ['Whale ID', 'Asset']
        df = df.dropna(subset=[col for col in essential_cols if col in df.columns])
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error cleaning data: {str(e)}")
        return df

class Agent1WhaleAnalyzer:
    """Agent 1: Whale Trade Analyzer and Query Router"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def analyze_query_streaming(self, user_query, df, container):
        """Stream Agent 1 analysis based on user query"""
        try:
            # First, determine if this is a direct asset query or whale-related query
            query_type_prompt = f"""Determine if this query is asking about:
1. Specific whale recommendations/analysis
2. Direct asset investment advice

User Query: "{user_query}"

Respond with either:
"WHALE_QUERY" - if asking about whale traders, their performance, or recommendations
"ASSET_QUERY: [ASSET]" - if asking about direct investment in a specific asset (extract the asset symbol)
"""
            # Get query type
            query_type_response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": query_type_prompt}],
                temperature=0.1,
                stream=False
            )
            query_type = query_type_response.choices[0].message.content.strip()

            if query_type.startswith("ASSET_QUERY:"):
                # Direct asset query - pass through to Agent 2
                asset = query_type.split(":")[1].strip()
                container.markdown(
                    f"""
                    <div class="agent-response">
                        <div class="agent-icon">🧠</div>
                        <div class="agent-content">
                            <span class="elegant-italic">Direct Asset Analysis</span>
                            <div class="highlight-info">Analyzing {asset} market conditions</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                return {
                    'response': f"Proceeding with market analysis for {asset}...",
                    'whale_id': None,  # Signal that no whale recommendation is needed
                    'asset': asset,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Whale-related query - proceed with whale analysis
                whale_summary = self._prepare_whale_summary(df)
                
                prompt = f"""You are an expert whale trading analyst. A user is asking: "{user_query}"

Based on this whale trading data, provide your analysis:
{whale_summary}

Your response should include:
1. Answer to the user's specific question
2. Which whale trader to follow (provide exact Whale ID)
3. Which asset to invest in (provide exact Asset symbol)
4. Why this recommendation makes sense based on available data
5. Key performance metrics supporting your choice
"""
                
                # Stream the response
                stream = self.client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    stream=True
                )
                
                response_container = container.empty()
                stream_content_container = container.empty()
                full_response = ""
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        stream_content_container.markdown(
                            f"""
                            <div class="agent-response">
                                <div class="agent-icon">🧠</div>
                                <div class="agent-content">
                                    <span class="elegant-italic">Whale Analysis & Strategy</span>
                                    {full_response}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        time.sleep(0.01)
                
                # Extract data and return
                whale_id = self._extract_whale_id(full_response)
                asset = self._extract_asset(full_response)
                
                return {
                    'response': full_response,
                    'whale_id': whale_id,
                    'asset': asset,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            container.error(f"Agent 1 Error: {str(e)}")
            return {'error': str(e)}
    
    def _prepare_whale_summary(self, df):
        """Prepare whale data summary with available columns"""
        summary = []
        
        for whale_id in df['Whale ID'].unique():
            whale_data = df[df['Whale ID'] == whale_id].iloc[0]
            
            summary_line = f"Whale {whale_id}"
            
            if 'Whale Name' in df.columns:
                summary_line += f" ({whale_data['Whale Name']})"
            
            metrics = []
            
            if 'Win Rate (%)' in df.columns:
                metrics.append(f"Win Rate: {whale_data['Win Rate (%)']}%")
            
            if 'Total Portfolio ($)' in df.columns:
                metrics.append(f"Portfolio: ${whale_data['Total Portfolio ($)']:,.0f}")
            
            if 'Risk Score' in df.columns:
                metrics.append(f"Risk: {whale_data['Risk Score']}")
            
            if 'Confidence' in df.columns:
                metrics.append(f"Confidence: {whale_data['Confidence']}")
            
            if metrics:
                summary_line += " | " + " | ".join(metrics)
            
            summary.append(summary_line)
        
        return "\n".join(summary)
    
    def _extract_whale_id(self, response):
        """Extract whale ID from response"""
        if not response:
            return None
            
        # Look for the exact format first
        match = re.search(r'RECOMMENDED WHALE:\s*(whale_\d+)', response)
        if match:
            return match.group(1)
            
        # Try alternative formats
        match = re.search(r'whale[_-]?\d+', response.lower())
        return match.group(0) if match else None
    
    def _extract_asset(self, response):
        """Extract asset symbol from response"""
        if not response:
            return None
            
        # Look for the exact format first
        match = re.search(r'RECOMMENDED ASSET:\s*(\w+)', response)
        if match:
            return match.group(1)
            
        # Try to find any mention of BTC, ETH, HYPE, or SOL
        match = re.search(r'\b(BTC|ETH|HYPE|SOL)\b', response)
        return match.group(1) if match else None

class Agent2SentimentValidator:
    """Agent 2: Market Data Validator using MCP Jenius"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.mcp_token = os.getenv('JENIUS_MCP_TOKEN')
        if not self.mcp_token:
            raise ValueError("JENIUS_MCP_TOKEN environment variable is not set")
    
    def validate_streaming(self, whale_id, asset, agent1_response, container):
        """Agent 2 validation using MCP Jenius server via OpenAI tools API"""
        try:
            validation_prompt = f"""Analyze the current market conditions for {asset} and provide a detailed analysis.
Include current price, technical indicators, market sentiment, and a clear investment recommendation.
If this is a whale position validation, consider the whale's current position in your analysis.
Whale ID: {whale_id if whale_id else 'Direct Market Analysis'}"""

            try:
                # Exactly match the notebook configuration
                resp = self.client.responses.create(
                    model="gpt-4o",
                    input=[{"role": "user", "content": validation_prompt}],
                    tools=[{
                        "type": "mcp",
                        "server_label": "Jenius",
                        "server_url": "https://mcp-jenius.rndm.io/sse",
                        "headers": {"Authorization": f"Bearer {self.mcp_token}"},
                        "require_approval": "never"
                    }],
                    stream=False
                )
                
                # Get the response text as shown in the notebook
                if hasattr(resp, 'output_text'):
                    full_response = resp.output_text
                else:
                    full_response = "Error: No output received from MCP server"
                    container.error("Failed to get market data. Please check your MCP token.")
                    return {'error': 'No output from MCP server'}

                # Display the response with compact styling
                container.markdown(
                    f"""
                    <div class="agent-response agent2-body">
                        <div class="agent-icon">📊</div>
                        <div class="agent-content">
                            <span class="elegant-italic">Market Validation &amp; Insights</span>
                            <div class="agent2-text">
                                {full_response}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                return {
                    'response': full_response,
                    'decision': self._extract_decision_from_narrative(full_response),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                error_msg = f"MCP Error: {str(e)}"
                container.error(error_msg)
                # Print detailed error information for debugging
                st.write("Detailed error information:")
                st.write({
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "mcp_token_exists": bool(self.mcp_token),
                    "openai_key_exists": bool(os.getenv('OPENAI_API_KEY'))
                })
                return {'error': error_msg}
                
        except Exception as e:
            container.error(f"Agent 2 Error: {str(e)}")
            return {'error': str(e)}
            
    def _extract_decision_from_narrative(self, response):
        """Extract the investment decision from the narrative response"""
        try:
            # Look for the decision in the first paragraph
            first_para = response.split('\n')[0].lower()
            
            if 'invest' in first_para:
                if 'do not invest' in first_para or 'don\'t invest' in first_para:
                    return 'DO_NOT_INVEST'
                return 'INVEST'
            elif 'wait' in first_para:
                return 'WAIT'
            
            # Fallback to strict decision extraction if narrative parsing fails
            return self._extract_decision_strict(response)
            
        except Exception:
            return 'UNCLEAR'
    
    def _extract_decision_strict(self, response):
        """Strict decision extraction looking for specific phrases"""
        response = response.lower()
        
        if 'do not invest' in response or 'don\'t invest' in response:
            return 'DO_NOT_INVEST'
        elif 'invest' in response:
            return 'INVEST'
        elif 'wait' in response:
            return 'WAIT'
        else:
            return 'UNCLEAR'

class Agent3PerformanceForecaster:
    """Agent 3: Future Performance Forecaster"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def forecast_streaming(self, whale_id, asset, agent1_response, agent2_response, container):
        """Generate performance forecast using context from Agent 1 & Agent 2"""
        try:
            prompt = f"""
You are a cryptocurrency performance forecaster.

Context from Whale Analysis (Agent 1):
{agent1_response}

Context from Market Validator (Agent 2 – includes technical indicators):
{agent2_response}

Task: Provide expected percentage returns for {asset} over the next timeframes:
1 Week (key "1W"), 1 Month ("1M"), 3 Months ("3M"), and 6 Months ("6M").

Respond **exactly** in this JSON format on the first line:
{{
    "1W": <number>,
    "1M": <number>,
    "3M": <number>,
    "6M": <number>
}}

After the JSON, add a short narrative explanation (2-3 paragraphs) of the drivers behind the forecast (use technical indicators when relevant).
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                stream=False
            )
            full_response = response.choices[0].message.content
            
            # Try to extract the JSON object on the first line
            price_targets = self._extract_price_targets(full_response)
            
            # Extract current price from Agent 2 narrative (best-effort)
            baseline_price = self._extract_current_price(agent2_response)
            
            # Display narrative & charts
            container.markdown(
                f"""
                <div class="agent-response">
                    <div class="agent-icon">🎯</div>
                    <div class="agent-content">
                        <span class="elegant-italic">Performance Forecasting</span>
                        {full_response}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if price_targets:
                chart_pct = create_forecast_chart(asset, price_targets)
                container.plotly_chart(chart_pct, use_container_width=True)
                
                if baseline_price:
                    chart_price = create_price_projection_chart(asset, baseline_price, price_targets)
                    container.plotly_chart(chart_price, use_container_width=True)
            
            return {
                'response': full_response,
                'price_targets': price_targets,
                'baseline_price': baseline_price,
                'indicators': self._extract_technical_indicators(agent2_response),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            container.error(f"Agent 3 Error: {str(e)}")
            return {'error': str(e)}
    
    def _extract_price_targets(self, response):
        """Extract price target percentages from a JSON block or fallback patterns"""
        import json, re
        targets = {}
        # Attempt to parse first JSON block
        json_match = re.search(r'\{[^\n]*?1W[^\n]*?\}', response, re.DOTALL)
        if json_match:
            try:
                targets = json.loads(json_match.group(0))
                return {k.upper(): float(v) for k, v in targets.items()}
            except Exception:
                pass
        
        # Fallback regex pattern (existing behaviour)
        patterns = {
            '1W': r'1[\s-]?week[^\d+-]*([+-]?\d+\.?\d*)%?',
            '1M': r'1[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
            '3M': r'3[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
            '6M': r'6[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
        }
        for tf, pat in patterns.items():
            m = re.search(pat, response, re.IGNORECASE)
            if m:
                try:
                    targets[tf] = float(m.group(1))
                except ValueError:
                    pass
        return targets
    
    def _extract_current_price(self, agent2_response):
        """Extract current price (first $xxx,xxx) from Agent 2 narrative"""
        import re
        m = re.search(r'\$([0-9,.]+)', agent2_response)
        if m:
            try:
                return float(m.group(1).replace(',', ''))
            except ValueError:
                return None
        return None

    def _extract_technical_indicators(self, agent2_response):
        """Parse RSI, EMA, Stochastic and MACD numbers from Agent 2 narrative"""
        indicators = {}
        patterns = {
            'RSI': r'RSI[^\d]*(\d+\.?\d*)',
            'EMA': r'EMA[^\d]*(\d+\.?\d*)',
            'Stochastic': r'Stochastic[^\d]*(\d+\.?\d*)',
            'MACD': r'MACD[^\d]*(\d+\.?\d*)',
        }
        for name, pat in patterns.items():
            m = re.search(pat, agent2_response, re.IGNORECASE)
            if m:
                try:
                    indicators[name] = float(m.group(1))
                except ValueError:
                    pass
        return indicators

def create_forecast_chart(asset, price_targets):
    """Create performance forecast visualization"""
    timeframes = list(price_targets.keys())
    returns = list(price_targets.values())
    
    # If no targets extracted, use default example
    if all(r == 0 for r in returns):
        returns = [2.5, 8.2, 15.7, 28.4]
    
    fig = go.Figure()
    
    # Add forecast line
    fig.add_trace(go.Scatter(
        x=timeframes,
        y=returns,
        mode='lines+markers',
        name=f'{asset} Forecast',
        line=dict(color='#9f7aea', width=3),
        marker=dict(color='#E0E0E0', size=10, line=dict(color='#9f7aea', width=2))
    ))
    
    fig.update_layout(
        title=f'{asset} Performance Forecast (%)',
        xaxis_title='Timeframe',
        yaxis_title='Projected Return (%)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E0E0E0', family='Roboto Mono'),
        xaxis=dict(gridcolor='#4a5568'),
        yaxis=dict(gridcolor='#4a5568'),
    )
    
    return fig

def create_price_projection_chart(asset, baseline_price, price_targets):
    """Create price projection visualization"""
    timeframes = list(price_targets.keys())
    returns = list(price_targets.values())
    
    # If no targets extracted, use default example
    if all(r == 0 for r in returns):
        returns = [2.5, 8.2, 15.7, 28.4]
    
    fig = go.Figure()
    
    # Add forecast line
    fig.add_trace(go.Scatter(
        x=timeframes,
        y=returns,
        mode='lines+markers',
        name=f'{asset} Forecast',
        line=dict(color='#9f7aea', width=3),
        marker=dict(color='#E0E0E0', size=10, line=dict(color='#9f7aea', width=2))
    ))
    
    fig.update_layout(
        title=f'{asset} Price Projection (%)',
        xaxis_title='Timeframe',
        yaxis_title='Projected Price (%)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E0E0E0', family='Roboto Mono'),
        xaxis=dict(gridcolor='#4a5568'),
        yaxis=dict(gridcolor='#4a5568'),
    )
    
    return fig

def create_indicator_radar_chart(indicators):
    import plotly.graph_objects as go
    if not indicators:
        return go.Figure()
    categories = list(indicators.keys())
    values = list(indicators.values())
    # Normalize values to 0-100 for radar
    max_val = max(values) if max(values) > 0 else 1
    norm_values = [v / max_val * 100 for v in values]

    fig = go.Figure()
    if len(categories) >= 3:
        fig.add_trace(go.Scatterpolar(r=norm_values + [norm_values[0]], theta=categories + [categories[0]], fill='toself', name='Indicators'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, title='Technical Indicator Radar')
    else:
        # Fallback to bar chart for 1–2 indicators
        fig.add_trace(go.Bar(x=categories, y=values, marker_color='#9f7aea'))
        fig.update_layout(title='Technical Indicators', yaxis_title='Value')
    return fig

def main():
    """Main application function"""
    st.markdown(
        """
        <div class="app-header">
            <h1>Trading Intelligence Platform</h1>
            <p class="subtitle">AI-powered dashboard that tracks on-chain whale activity, validates positions with real-time market data, and forecasts crypto performance.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Load whale data
    df = load_whale_data()
    if df is None:
        st.error("❌ Unable to proceed without valid whale data.")
        return

    # Initialize agents
    agent1 = Agent1WhaleAnalyzer(openai_client)
    agent2 = Agent2SentimentValidator(openai_client)
    agent3 = Agent3PerformanceForecaster(openai_client)

    # Create sidebar
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-header">
                <h3>Navigation</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------- Chat Conversation UI ----------

    # Initialise chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for m in st.session_state.messages:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.markdown(m["content"], unsafe_allow_html=True)

    # Capture new user input
    user_query = st.chat_input("Ask about whales or crypto markets…")

    if user_query:
        # Save & show user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # ---------- Quick greeting / thanks handler ----------
        import re
        greet_regex = r"\b(hi|hello|hey|good\s*(morning|evening|afternoon)|thanks|thank\s*you)\b"
        if re.search(greet_regex, user_query.strip().lower()):
            greet_reply = (
                "**🤖 Hello!**\n\n"
                "I'm a coordinated trio of AI agents:  🧠 *Agent 1* spots whale-trading insights,  📊 *Agent 2* validates live market data,  "
                "and 🎯 *Agent 3* projects future performance.  Ask me anything about whales or crypto markets!"
            )
            with st.chat_message("assistant"):
                st.markdown(greet_reply)
            st.session_state.messages.append({"role": "assistant", "content": greet_reply})
            return

        try:
            # ---------- Agent executions (silent containers) ----------
            agent1_container = st.empty()
            agent1_result = agent1.analyze_query_streaming(user_query, df, agent1_container)

            def _shorten(txt, max_chars=260):
                plain = re.sub(r'<[^>]+>', '', txt)
                short = textwrap.shorten(plain.replace('\n', ' '), width=max_chars, placeholder='…')
                return short

            direct_asset_mode = agent1_result['whale_id'] is None and agent1_result['asset']

            if direct_asset_mode:
                agent1_summary = (
                    "As you asked specifically about the asset, we'll skip the whale-behaviour step "
                    "and jump straight to **Agent 2**, which taps live market feeds to validate current conditions.")
            else:
                agent1_summary = _shorten(agent1_result['response'])

            agent2_container = st.empty()
            agent2_result = agent2.validate_streaming(
                agent1_result['whale_id'],
                agent1_result['asset'],
                agent1_result['response'],
                agent2_container
            )

            agent3_container = st.empty()
            agent3_result = agent3.forecast_streaming(
                agent1_result['whale_id'],
                agent1_result['asset'],
                agent1_result['response'],
                agent2_result['response'],
                agent3_container
            )

            # Build combined assistant message
            combined_msg = (
                "**🤖 Summary:**\n\n"
                "🧠 **Agent 1 (Whale Analyzer)** – " + agent1_summary + "\n\n"
                "📊 **Agent 2 (Market Validation)** – " + _shorten(agent2_result['response']) + "\n\n"
                "🎯 **Agent 3 (Performance Forecast)** – " + _shorten(agent3_result.get('response', 'Forecast unavailable.'))
            )

            with st.chat_message("assistant"):
                st.markdown(combined_msg, unsafe_allow_html=True)
                # Plot charts if any
                if 'price_targets' in agent3_result and agent3_result['price_targets']:
                    st.plotly_chart(create_forecast_chart(agent1_result['asset'], agent3_result['price_targets']), use_container_width=True)
                # Technical indicator radar chart if extracted
                if 'indicators' in agent3_result and agent3_result['indicators']:
                    st.plotly_chart(create_indicator_radar_chart(agent3_result['indicators']), use_container_width=True)
            st.session_state.messages.append({"role": "assistant", "content": combined_msg})

        except Exception as e:
            err_txt = f"An error occurred: {str(e)}"
            with st.chat_message("assistant"):
                st.error(err_txt)
            st.session_state.messages.append({"role": "assistant", "content": err_txt})

if __name__ == "__main__":
    main()
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
    page_title="WhaleFlow Intelligence", 
    page_icon="🐋",
    layout="wide", 
    initial_sidebar_state="collapsed"
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

def is_greeting_query(query):
    """Check if query contains greeting words - improved detection"""
    query_lower = query.lower().strip()
    
    # Define greeting patterns
    greeting_patterns = [
        r'\b(hi|hello|hey|sup|yo)\b',
        r'\b(good\s*(morning|afternoon|evening|day))\b', 
        r'\b(thank\s*(you|s)|thanks)\b',
        r'^(hi|hello|hey)',  # Starting with greeting
        r'(hi|hello|hey)\s+[^\w]'  # Greeting followed by punctuation
    ]
    
    for pattern in greeting_patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False

class Agent1WhaleAnalyzer:
    """Agent 1: Whale Trade Analyzer and Query Router"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def analyze_query_streaming(self, user_query, df, container):
        """Stream Agent 1 analysis based on user query"""
        try:
            # Extract asset from query first
            asset = self._extract_asset_from_query(user_query)
            
            if not asset:
                container.error("❌ Please specify an asset (BTC, ETH, HYPE, or SOL) in your query.")
                return {'error': 'No asset specified'}
            
            # Find the best performing whale for this asset
            best_whale_data = self._find_best_whale_for_asset(df, asset)
            
            if not best_whale_data:
                container.error(f"❌ No whale data found for {asset}")
                return {'error': f'No whale data for {asset}'}
            
            # Create detailed whale analysis prompt
            whale_summary = self._create_detailed_whale_summary(best_whale_data, df)
            
            prompt = f"""You are an expert whale trading analyst. A user is asking: "{user_query}"

I've identified the best performing whale for {asset}:

{whale_summary}

Provide a comprehensive analysis including:
1. Summary of this whale's trading strategy and success with {asset}
2. Key performance metrics that make this whale worth following
3. Trading patterns and insights from their {asset} positions
4. Risk assessment and confidence level
5. Clear recommendation based on whale's track record

Focus on actionable insights and explain why this whale's approach to {asset} is noteworthy.

IMPORTANT: End your response with:
RECOMMENDED WHALE: {best_whale_data['whale_id']}
RECOMMENDED ASSET: {asset}
"""
            
            # Stream the response
            stream = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                stream=True
            )
            
            response_container = container.empty()
            full_response = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_container.markdown(
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
            
            return {
                'response': full_response,
                'whale_id': best_whale_data['whale_id'],
                'whale_data': best_whale_data,  # Pass complete whale data to Agent 2
                'asset': asset,
                'timestamp': datetime.now().isoformat()
            }
                
        except Exception as e:
            container.error(f"Agent 1 Error: {str(e)}")
            return {'error': str(e)}
    
    def _extract_asset_from_query(self, query):
        """Extract asset symbol from user query"""
        query_upper = query.upper()
        assets = ['BTC', 'ETH', 'HYPE', 'SOL']
        for asset in assets:
            if asset in query_upper:
                return asset
        return None
    
    def _find_best_whale_for_asset(self, df, asset):
        """Find the best performing whale for a specific asset"""
        # Filter for the specific asset
        asset_df = df[df['Asset'] == asset].copy()
        
        if asset_df.empty:
            return None
        
        # Calculate performance score based on multiple factors
        asset_df['performance_score'] = (
            asset_df['Win Rate (%)'] * 0.3 +
            asset_df['PnL %'] * 0.25 +
            asset_df['Confidence'] * 0.25 +
            (100 - asset_df['Risk Score']) * 0.2  # Lower risk is better
        )
        
        # Get the best whale
        best_whale = asset_df.loc[asset_df['performance_score'].idxmax()]
        
        return {
            'whale_id': best_whale['Whale ID'],
            'whale_name': best_whale['Whale Name'],
            'win_rate': best_whale['Win Rate (%)'],
            'pnl_percent': best_whale['PnL %'],
            'pnl_dollar': best_whale['PnL ($)'],
            'confidence': best_whale['Confidence'],
            'risk_score': best_whale['Risk Score'],
            'position_size': best_whale['Position Size ($)'],
            'direction': best_whale['Direction'],
            'leverage': best_whale['Leverage'],
            'entry_price': best_whale['Entry Price'],
            'current_price': best_whale['Current Price'],
            'total_portfolio': best_whale['Total Portfolio ($)'],
            'weekly_pnl': best_whale['Weekly PnL ($)'],
            'avg_trade_size': best_whale['Avg Trade Size ($)'],
            'last_active': best_whale['Last Active']
        }
    
    def _create_detailed_whale_summary(self, whale_data, df):
        """Create detailed summary of whale's performance"""
        whale_id = whale_data['whale_id']
        asset_positions = df[df['Whale ID'] == whale_id]
        
        summary = f"""
WHALE PROFILE:
- ID: {whale_data['whale_id']}
- Name: {whale_data['whale_name']}
- Total Portfolio: ${whale_data['total_portfolio']:,.0f}
- Win Rate: {whale_data['win_rate']}%
- Risk Score: {whale_data['risk_score']}/10
- Confidence Level: {whale_data['confidence']}%

CURRENT POSITION:
- Asset: {asset_positions.iloc[0]['Asset']}
- Direction: {whale_data['direction']}
- Position Size: ${whale_data['position_size']:,.0f}
- Leverage: {whale_data['leverage']}
- Entry Price: ${whale_data['entry_price']:,.2f}
- Current Price: ${whale_data['current_price']:,.2f}
- PnL: ${whale_data['pnl_dollar']:,.0f} ({whale_data['pnl_percent']:.2f}%)

PERFORMANCE METRICS:
- Weekly PnL: ${whale_data['weekly_pnl']:,.0f}
- Average Trade Size: ${whale_data['avg_trade_size']:,.0f}
- Last Active: {whale_data['last_active']}

PORTFOLIO DIVERSIFICATION:
- Assets Traded: {', '.join(asset_positions['Asset'].unique())}
- Total Positions: {len(asset_positions)}
"""
        return summary

class Agent2SentimentValidator:
    """Agent 2: Market Data Validator with Short/Long Term Analysis"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.mcp_token = os.getenv('JENIUS_MCP_TOKEN')
        if not self.mcp_token:
            raise ValueError("JENIUS_MCP_TOKEN environment variable is not set")
    
    def validate_streaming(self, whale_id, asset, agent1_response, whale_data, user_query, container):
        """Agent 2 validation with short/long term analysis"""
        try:
            # Extract timeframe from ORIGINAL USER QUERY
            timeframe = self._extract_timeframe_from_query(user_query)
            
            if timeframe == 'short':
                return self._analyze_short_term_only(asset, whale_data, container)
            elif timeframe == 'long':
                return self._analyze_long_term_only(asset, whale_data, container)
            else:
                # If unclear or not mentioned, provide BOTH analyses
                return self._analyze_both_timeframes(asset, whale_data, container)
                
        except Exception as e:
            container.error(f"Agent 2 Error: {str(e)}")
            return {'error': str(e)}
    
    def _extract_timeframe_from_query(self, user_query):
        """Extract investment timeframe from ORIGINAL user query"""
        query_lower = user_query.lower()
        
        short_terms = ['short term', 'short-term', 'quick', 'fast', 'day trading', 'swing', 'weeks', 'daily', 'weekly', 'short']
        long_terms = ['long term', 'long-term', 'hold', 'months', 'years', 'invest and hold', 'hodl', 'buy and hold', 'long']
        
        has_short = any(term in query_lower for term in short_terms)
        has_long = any(term in query_lower for term in long_terms)
        
        if has_short and not has_long:
            return 'short'
        elif has_long and not has_short:
            return 'long'
        else:
            return 'unclear'  # This will trigger both analyses
    
    def _analyze_both_timeframes(self, asset, whale_data, container):
        """Always provide BOTH analyses when timeframe not specified"""
        try:
            # Get SHORT-TERM analysis from MCP server (real-time data)
            short_analysis = self._get_technical_analysis_from_mcp(asset)
            
            # Get LONG-TERM analysis from whale patterns
            long_analysis = self._get_whale_pattern_analysis(asset, whale_data)
            
            combined_response = f"""**COMPREHENSIVE INVESTMENT ANALYSIS FOR {asset}**

**🚀 SHORT-TERM ANALYSIS (1-4 weeks)**
*Based on Real-Time Market Data from MCP Server:*

{short_analysis['analysis']}

**Technical Recommendation:** {short_analysis['recommendation']}
**Confidence Level:** {short_analysis['confidence']}%

---

**🏗️ LONG-TERM ANALYSIS (3-12 months)**
*Based on Whale Trading Patterns:*

{long_analysis['analysis']}

**Whale-Based Recommendation:** {long_analysis['recommendation']}
**Performance Score:** {long_analysis['score']}/100

---

**📊 SUMMARY:**
- **Short-Term (Technical)**: {short_analysis['decision']} 
- **Long-Term (Whale-Based)**: {long_analysis['decision']}

**💡 Choose Your Strategy:**
- For **quick trades** (1-4 weeks): Follow the technical analysis
- For **long-term holds** (3+ months): Follow the whale patterns"""

            container.markdown(
                f"""
                <div class="agent-response agent2-body">
                    <div class="agent-icon">📊</div>
                    <div class="agent-content">
                        <span class="elegant-italic">Dual Market Analysis</span>
                        <div class="agent2-text">
                            {combined_response}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            return {
                'response': combined_response,
                'analysis_type': 'both',
                'short_term_data': short_analysis,
                'long_term_data': long_analysis,
                'decision': 'BOTH_PROVIDED',
                'mcp_data': short_analysis.get('mcp_raw_data', ''),  # Pass raw MCP data to Agent 3
                'whale_patterns': long_analysis.get('whale_patterns', {}),  # Pass whale patterns to Agent 3
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            container.error(f"Comprehensive analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_short_term_only(self, asset, whale_data, container):
        """Short-term analysis using ONLY MCP real-time data"""
        try:
            analysis_result = self._get_technical_analysis_from_mcp(asset)
            
            final_response = f"""**SHORT-TERM TECHNICAL ANALYSIS FOR {asset}**
*Based on Real-Time Market Data:*

{analysis_result['analysis']}

**RECOMMENDATION:** {analysis_result['recommendation']}
**CONFIDENCE:** {analysis_result['confidence']}%"""

            container.markdown(
                f"""
                <div class="agent-response agent2-body">
                    <div class="agent-icon">📊</div>
                    <div class="agent-content">
                        <span class="elegant-italic">Short-Term Technical Analysis</span>
                        <div class="agent2-text">
                            {final_response}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            return {
                'response': final_response,
                'decision': analysis_result['decision'],
                'analysis_type': 'short_term',
                'mcp_data': analysis_result.get('mcp_raw_data', ''),
                'indicators': analysis_result.get('indicators', {}),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            container.error(f"Short-term analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_long_term_only(self, asset, whale_data, container):
        """Long-term analysis using ONLY whale patterns"""
        try:
            analysis_result = self._get_whale_pattern_analysis(asset, whale_data)
            
            whale_analysis = f"""**LONG-TERM WHALE PATTERN ANALYSIS FOR {asset}**
*Based on Whale Trading History:*

{analysis_result['analysis']}

**RECOMMENDATION:** {analysis_result['recommendation']}
**PERFORMANCE SCORE:** {analysis_result['score']}/100"""
            
            container.markdown(
                f"""
                <div class="agent-response agent2-body">
                    <div class="agent-icon">📊</div>
                    <div class="agent-content">
                        <span class="elegant-italic">Long-Term Whale Pattern Analysis</span>
                        <div class="agent2-text">
                            {whale_analysis}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            return {
                'response': whale_analysis,
                'decision': analysis_result['decision'],
                'analysis_type': 'long_term',
                'whale_patterns': analysis_result.get('whale_patterns', {}),
                'whale_metrics': whale_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            container.error(f"Long-term analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _get_technical_analysis_from_mcp(self, asset):
        """Get real-time technical analysis from MCP server"""
        try:
            technical_prompt = f"""Provide comprehensive technical analysis for {asset}:

1. Current price and recent price movement
2. RSI value and interpretation (oversold <30, neutral 30-70, overbought >70)
3. MACD signal line and histogram
4. Stochastic oscillator reading
5. Moving averages (20-day, 50-day)
6. Support and resistance levels
7. Volume analysis
8. Market momentum indicators
9. Clear BUY/SELL/HOLD recommendation

Focus on actionable technical signals for short-term trading (1-4 weeks)."""

            resp = self.client.responses.create(
                model="gpt-4o",
                input=[{"role": "user", "content": technical_prompt}],
                tools=[{
                    "type": "mcp",
                    "server_label": "Jenius",
                    "server_url": "https://mcp-jenius.rndm.io/sse",
                    "headers": {"Authorization": f"Bearer {self.mcp_token}"},
                    "require_approval": "never"
                }],
                stream=False
            )
            
            if hasattr(resp, 'output_text'):
                mcp_response = resp.output_text
            else:
                mcp_response = "Error: No technical data available from MCP server"
            
            # Extract indicators and create recommendation
            indicators = self._extract_technical_indicators(mcp_response)
            evaluation = self._evaluate_technical_signals(mcp_response)
            
            return {
                'analysis': mcp_response,
                'mcp_raw_data': mcp_response,  # Raw data for Agent 3
                'indicators': indicators,
                'recommendation': evaluation['recommendation'],
                'confidence': evaluation['confidence'],
                'decision': evaluation['decision'],
                'support_resistance': self._extract_support_resistance(mcp_response)
            }
            
        except Exception as e:
            return {
                'analysis': f"Unable to fetch real-time data: {str(e)}",
                'mcp_raw_data': f"Error: {str(e)}",
                'recommendation': 'WAIT - Data unavailable',
                'confidence': 0,
                'decision': 'WAIT'
            }
    
    def _get_whale_pattern_analysis(self, asset, whale_data):
        """Analyze whale trading patterns for long-term insights"""
        try:
            # Analyze whale's trading patterns and performance
            patterns = self._analyze_whale_trading_patterns(whale_data)
            performance_eval = self._evaluate_whale_performance_detailed(whale_data)
            
            pattern_analysis = f"""**WHALE TRADING PATTERN ANALYSIS:**

**Whale Profile:**
- Name: {whale_data['whale_name']} ({whale_data['whale_id']})
- Portfolio Size: ${whale_data['total_portfolio']:,.0f}
- Current {asset} Position: {whale_data['direction']} ${whale_data['position_size']:,.0f}

**Performance Metrics:**
- Win Rate: {whale_data['win_rate']}% (Historical Success)
- Current PnL: ${whale_data['pnl_dollar']:,.0f} ({whale_data['pnl_percent']:.2f}%)
- Risk Profile: {whale_data['risk_score']}/10
- Confidence Score: {whale_data['confidence']}%

**Trading Pattern Insights:**
{patterns['pattern_description']}

**Long-Term Outlook:**
{performance_eval['analysis']}

**Position Sizing:** {whale_data['direction']} position with {whale_data['leverage']} leverage
**Entry Strategy:** Entered at ${whale_data['entry_price']:,.2f}, current price ${whale_data['current_price']:,.2f}"""

            return {
                'analysis': pattern_analysis,
                'whale_patterns': patterns,
                'recommendation': performance_eval['recommendation'],
                'score': performance_eval['score'],
                'decision': performance_eval['decision']
            }
            
        except Exception as e:
            return {
                'analysis': f"Whale pattern analysis error: {str(e)}",
                'recommendation': 'UNCLEAR',
                'score': 0,
                'decision': 'ERROR'
            }
    
    def _analyze_whale_trading_patterns(self, whale_data):
        """Extract trading patterns from whale data"""
        # Calculate pattern insights
        leverage_risk = "High" if float(str(whale_data['leverage']).replace('X', '')) > 10 else "Moderate" if float(str(whale_data['leverage']).replace('X', '')) > 5 else "Low"
        
        position_size_pct = (whale_data['position_size'] / whale_data['total_portfolio']) * 100
        position_commitment = "Heavy" if position_size_pct > 30 else "Moderate" if position_size_pct > 15 else "Light"
        
        pnl_status = "Profitable" if whale_data['pnl_percent'] > 0 else "Losing"
        
        pattern_desc = f"""
• **Leverage Strategy**: {leverage_risk} risk approach ({whale_data['leverage']} leverage)
• **Position Commitment**: {position_commitment} allocation ({position_size_pct:.1f}% of portfolio)
• **Current Status**: {pnl_status} position ({whale_data['pnl_percent']:.2f}% return)
• **Trading Style**: {whale_data['direction']} bias with {whale_data['confidence']}% conviction
• **Risk Management**: {whale_data['risk_score']}/10 risk score
"""
        
        return {
            'leverage_risk': leverage_risk,
            'position_commitment': position_commitment,
            'pnl_status': pnl_status,
            'pattern_description': pattern_desc
        }
    
    def _extract_technical_indicators(self, mcp_response):
        """Extract technical indicators from MCP response"""
        indicators = {}
        
        # RSI
        rsi_match = re.search(r'RSI[^\d]*(\d+\.?\d*)', mcp_response, re.IGNORECASE)
        if rsi_match:
            indicators['RSI'] = float(rsi_match.group(1))
        
        # MACD
        macd_match = re.search(r'MACD[^\d-]*([+-]?\d+\.?\d*)', mcp_response, re.IGNORECASE)
        if macd_match:
            indicators['MACD'] = float(macd_match.group(1))
        
        # Stochastic
        stoch_match = re.search(r'Stochastic[^\d]*(\d+\.?\d*)', mcp_response, re.IGNORECASE)
        if stoch_match:
            indicators['Stochastic'] = float(stoch_match.group(1))
        
        # Price
        price_match = re.search(r'price[^\d]*\$?([0-9,]+\.?\d*)', mcp_response, re.IGNORECASE)
        if price_match:
            indicators['Current_Price'] = float(price_match.group(1).replace(',', ''))
        
        return indicators
    
    def _extract_support_resistance(self, mcp_response):
        """Extract support and resistance levels"""
        support_resistance = {}
        
        # Support level
        support_match = re.search(r'support[^\d]*\$?([0-9,]+\.?\d*)', mcp_response, re.IGNORECASE)
        if support_match:
            support_resistance['support'] = float(support_match.group(1).replace(',', ''))
        
        # Resistance level
        resistance_match = re.search(r'resistance[^\d]*\$?([0-9,]+\.?\d*)', mcp_response, re.IGNORECASE)
        if resistance_match:
            support_resistance['resistance'] = float(resistance_match.group(1).replace(',', ''))
        
        return support_resistance
    
    def _evaluate_technical_signals(self, mcp_response):
        """Evaluate technical signals from MCP data"""
        response_lower = mcp_response.lower()
        
        buy_signals = 0
        sell_signals = 0
        neutral_signals = 0
        
        # RSI signals
        if 'oversold' in response_lower:
            buy_signals += 2
        elif 'overbought' in response_lower:
            sell_signals += 2
        else:
            neutral_signals += 1
        
        # MACD signals
        if 'bullish' in response_lower or 'positive macd' in response_lower:
            buy_signals += 2
        elif 'bearish' in response_lower or 'negative macd' in response_lower:
            sell_signals += 2
        
        # General sentiment
        if 'buy' in response_lower and 'sell' not in response_lower:
            buy_signals += 1
        elif 'sell' in response_lower and 'buy' not in response_lower:
            sell_signals += 1
        
        if 'strong' in response_lower:
            if buy_signals > sell_signals:
                buy_signals += 1
            elif sell_signals > buy_signals:
                sell_signals += 1
        
        # Determine recommendation
        total_signals = buy_signals + sell_signals + neutral_signals
        
        if buy_signals > sell_signals and buy_signals >= 2:
            return {
                'recommendation': 'BUY - Technical indicators favor long position',
                'decision': 'BUY',
                'confidence': min(90, 50 + (buy_signals * 10))
            }
        elif sell_signals > buy_signals and sell_signals >= 2:
            return {
                'recommendation': 'SELL - Technical indicators favor short position',
                'decision': 'SELL',
                'confidence': min(90, 50 + (sell_signals * 10))
            }
        else:
            return {
                'recommendation': 'WAIT - Mixed or unclear signals from technical analysis',
                'decision': 'WAIT',
                'confidence': 40
            }
    
    def _evaluate_whale_performance_detailed(self, whale_data):
        """Detailed evaluation of whale performance for long-term strategy"""
        score = 0
        analysis_points = []
        
        # Win rate scoring (0-35 points)
        if whale_data['win_rate'] >= 85:
            score += 35
            analysis_points.append(f"✅ Exceptional win rate: {whale_data['win_rate']}% (Top-tier performer)")
        elif whale_data['win_rate'] >= 75:
            score += 25
            analysis_points.append(f"✅ Strong win rate: {whale_data['win_rate']}% (Above average)")
        elif whale_data['win_rate'] >= 65:
            score += 15
            analysis_points.append(f"⚠️ Moderate win rate: {whale_data['win_rate']}% (Average performer)")
        else:
            score += 5
            analysis_points.append(f"❌ Below average win rate: {whale_data['win_rate']}%")
        
        # PnL performance (0-30 points)
        if whale_data['pnl_percent'] > 20:
            score += 30
            analysis_points.append(f"✅ Outstanding returns: {whale_data['pnl_percent']:.2f}%")
        elif whale_data['pnl_percent'] > 10:
            score += 20
            analysis_points.append(f"✅ Strong returns: {whale_data['pnl_percent']:.2f}%")
        elif whale_data['pnl_percent'] > 0:
            score += 10
            analysis_points.append(f"✅ Positive returns: {whale_data['pnl_percent']:.2f}%")
        else:
            score -= 10
            analysis_points.append(f"❌ Currently losing: {whale_data['pnl_percent']:.2f}%")
        
        # Risk management (0-20 points)
        if whale_data['risk_score'] <= 5:
            score += 20
            analysis_points.append(f"✅ Excellent risk management: {whale_data['risk_score']}/10")
        elif whale_data['risk_score'] <= 7:
            score += 10
            analysis_points.append(f"⚠️ Moderate risk: {whale_data['risk_score']}/10")
        else:
            score -= 5
            analysis_points.append(f"❌ High risk approach: {whale_data['risk_score']}/10")
        
        # Confidence level (0-15 points)
        if whale_data['confidence'] >= 90:
            score += 15
            analysis_points.append(f"✅ Very high confidence: {whale_data['confidence']}%")
        elif whale_data['confidence'] >= 80:
            score += 10
            analysis_points.append(f"✅ High confidence: {whale_data['confidence']}%")
        else:
            score += 5
            analysis_points.append(f"⚠️ Moderate confidence: {whale_data['confidence']}%")
        
        # Final recommendation based on score
        if score >= 80:
            decision = 'STRONG_BUY'
            recommendation = 'STRONG BUY - Exceptional whale performance supports long-term investment'
        elif score >= 60:
            decision = 'BUY'
            recommendation = 'BUY - Good whale performance indicates positive long-term potential'
        elif score >= 40:
            decision = 'HOLD'
            recommendation = 'HOLD - Mixed signals, suitable for small position'
        else:
            decision = 'AVOID'
            recommendation = 'AVOID - Poor whale performance suggests high risk'
        
        analysis_text = '\n'.join(analysis_points)
        analysis_text += f"\n\n**WHALE PERFORMANCE SCORE: {score}/100**\n**RECOMMENDATION: {recommendation}**"
        
        return {
            'analysis': analysis_text,
            'decision': decision,
            'recommendation': recommendation,
            'score': score
        }

class Agent3PerformanceForecaster:
    """Agent 3: Performance Forecaster using data from Agent 2"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def forecast_streaming(self, whale_id, asset, agent1_response, agent2_response, container):
        """Generate forecast using Agent 2's data (NOT real-time access)"""
        try:
            analysis_type = agent2_response.get('analysis_type', 'general')
            
            if analysis_type == 'both':
                # Agent 2 provided both analyses
                forecast_result = self._generate_dual_forecast(asset, agent1_response, agent2_response, container)
            elif analysis_type == 'short_term':
                # Only short-term analysis
                forecast_result = self._generate_short_term_forecast(asset, agent1_response, agent2_response, container)
            elif analysis_type == 'long_term':
                # Only long-term analysis
                forecast_result = self._generate_long_term_forecast(asset, agent1_response, agent2_response, container)
            else:
                forecast_result = self._generate_general_forecast(asset, agent1_response, agent2_response, container)
            
            # Always add natural language summary
            summary = self._generate_conversational_summary(asset, agent1_response, agent2_response, forecast_result)
            
            # Display the summary
            container.markdown(
                f"""
                <div class="agent-response">
                    <div class="agent-icon">🎯</div>
                    <div class="agent-content">
                        <span class="elegant-italic">Investment Forecast & Guidance</span>
                        <div style="background-color: #f0f8f0; padding: 1.5rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #4a6741;">
                            {summary}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            forecast_result['conversational_summary'] = summary
            return forecast_result
                
        except Exception as e:
            container.error(f"Agent 3 Error: {str(e)}")
            return {'error': str(e)}
    
    def _generate_dual_forecast(self, asset, agent1_response, agent2_response, container):
        """Generate forecast for both timeframes using Agent 2's data"""
        
        # Extract data provided by Agent 2
        short_term_data = agent2_response.get('short_term_data', {})
        long_term_data = agent2_response.get('long_term_data', {})
        mcp_data = agent2_response.get('mcp_data', '')
        whale_patterns = agent2_response.get('whale_patterns', {})
        
        prompt = f"""You are a cryptocurrency performance forecaster. Use the provided analysis data to generate forecasts.

ASSET: {asset}

AGENT 1 - WHALE IDENTIFICATION:
{agent1_response}

AGENT 2 - DUAL ANALYSIS:
{agent2_response['response']}

SHORT-TERM DATA FROM MCP SERVER:
{mcp_data}

WHALE PATTERN DATA:
{whale_patterns}

Generate forecasts for BOTH timeframes using the provided data:

1. SHORT-TERM (1-4 weeks): Based on the MCP technical data above
2. LONG-TERM (3-12 months): Based on the whale patterns above

Provide percentage predictions in JSON format:
{{
    "1W": <short_term_week_1>,
    "4W": <short_term_week_4>,
    "3M": <long_term_month_3>,
    "12M": <long_term_month_12>
}}

Then explain:
- How technical indicators support short-term predictions
- How whale patterns support long-term predictions  
- Risk assessment for each timeframe
- Position sizing recommendations"""
        
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            stream=False
        )
        full_response = response.choices[0].message.content
        
        # Extract price targets and create charts
        price_targets = self._extract_price_targets(full_response)
        
        if price_targets:
            # Create dual timeframe chart
            chart = self._create_dual_timeframe_chart(asset, price_targets, short_term_data, long_term_data)
            container.plotly_chart(chart, use_container_width=True)
        
        return {
            'response': full_response,
            'forecast_type': 'dual',
            'price_targets': price_targets,
            'short_term_basis': 'MCP Technical Data',
            'long_term_basis': 'Whale Patterns',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_short_term_forecast(self, asset, agent1_response, agent2_response, container):
        """Generate short-term forecast using MCP data from Agent 2"""
        
        mcp_data = agent2_response.get('mcp_data', agent2_response.get('response', ''))
        indicators = agent2_response.get('indicators', {})
        
        prompt = f"""Generate SHORT-TERM forecast for {asset} using provided MCP technical data.

WHALE CONTEXT:
{agent1_response}

MCP TECHNICAL DATA FROM AGENT 2:
{mcp_data}

TECHNICAL INDICATORS:
{indicators}

Generate 4-week forecast based on the technical analysis provided above.

Provide percentage predictions in JSON format:
{{
    "1W": <week_1_prediction>,
    "2W": <week_2_prediction>, 
    "3W": <week_3_prediction>,
    "4W": <week_4_prediction>
}}

Explain how each technical indicator supports your predictions and provide entry/exit strategies."""
        
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            stream=False
        )
        full_response = response.choices[0].message.content
        
        price_targets = self._extract_price_targets(full_response)
        
        if price_targets:
            chart = self._create_short_term_chart(asset, price_targets, indicators)
            container.plotly_chart(chart, use_container_width=True)
        
        return {
            'response': full_response,
            'forecast_type': 'short_term',
            'price_targets': price_targets,
            'basis': 'MCP Technical Analysis',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_long_term_forecast(self, asset, agent1_response, agent2_response, container):
        """Generate long-term forecast using whale data from Agent 2"""
        
        whale_patterns = agent2_response.get('whale_patterns', {})
        whale_metrics = agent2_response.get('whale_metrics', {})
        
        prompt = f"""Generate LONG-TERM forecast for {asset} using whale performance data.

WHALE ANALYSIS:
{agent1_response}

WHALE PATTERN ANALYSIS FROM AGENT 2:
{agent2_response.get('response', '')}

WHALE PERFORMANCE METRICS:
{whale_metrics}

Generate 12-month forecast based on whale trading patterns and performance.

Provide percentage predictions in JSON format:
{{
    "3M": <month_3_prediction>,
    "6M": <month_6_prediction>,
    "9M": <month_9_prediction>, 
    "12M": <month_12_prediction>
}}

Explain how whale performance history supports your predictions and provide investment strategy."""
        
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            stream=False
        )
        full_response = response.choices[0].message.content
        
        price_targets = self._extract_price_targets(full_response)
        
        if price_targets:
            chart = self._create_long_term_chart(asset, price_targets, whale_metrics)
            container.plotly_chart(chart, use_container_width=True)
        
        return {
            'response': full_response,
            'forecast_type': 'long_term',
            'price_targets': price_targets,
            'basis': 'Whale Performance Patterns',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_conversational_summary(self, asset, agent1_response, agent2_response, forecast_result):
        """Generate natural language summary of complete analysis"""
        prompt = f"""You are a friendly investment advisor. Provide a conversational summary of the {asset} analysis.

Complete Analysis Summary:
- Agent 1: {agent1_response[:300]}...
- Agent 2: {agent2_response.get('response', '')[:300]}...
- Agent 3: {forecast_result.get('response', '')[:300]}...

Write a natural, friendly summary that:
1. Explains what we discovered about {asset} in simple terms
2. Highlights the key insights from whale data and market analysis  
3. Gives clear, actionable investment advice
4. Mentions specific timeframes and expected returns
5. Explains the reasoning in an easy-to-understand way

Start with something like "Here's what I found about {asset}..." and keep it conversational like you're talking to a friend who wants investment advice."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Here's the bottom line on {asset}: Our analysis looked at both the best-performing whale trader and current market conditions. Based on the data, we've provided specific recommendations for both short-term trading and long-term investment strategies. Check the detailed analysis above for the complete picture and specific return projections."
    
    def _create_dual_timeframe_chart(self, asset, price_targets, short_data, long_data):
        """Create chart showing both short and long term forecasts"""
        fig = go.Figure()
        
        # Short-term data (weeks)
        short_timeframes = [tf for tf in price_targets.keys() if 'W' in tf]
        short_returns = [price_targets.get(tf, 0) for tf in short_timeframes]
        
        # Long-term data (months)  
        long_timeframes = [tf for tf in price_targets.keys() if 'M' in tf]
        long_returns = [price_targets.get(tf, 0) for tf in long_timeframes]
        
        if short_timeframes and short_returns:
            fig.add_trace(go.Scatter(
                x=short_timeframes,
                y=short_returns,
                mode='lines+markers',
                name=f'{asset} Short-Term (Technical)',
                line=dict(color='#FF6B6B', width=3),
                marker=dict(color='#FF6B6B', size=10)
            ))
        
        if long_timeframes and long_returns:
            fig.add_trace(go.Scatter(
                x=long_timeframes,
                y=long_returns,
                mode='lines+markers',
                name=f'{asset} Long-Term (Whale-Based)',
                line=dict(color='#4a6741', width=3),
                marker=dict(color='#4a6741', size=12)
            ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=f'{asset} Dual Forecast: Technical vs Whale-Based',
            xaxis_title='Timeframe',
            yaxis_title='Expected Return (%)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a', family='Inter'),
            height=450,
            showlegend=True
        )
        
        return fig
    
    def _create_short_term_chart(self, asset, price_targets, indicators):
        """Create short-term chart with technical indicator context"""
        timeframes = [tf for tf in price_targets.keys() if 'W' in tf]
        returns = [price_targets.get(tf, 0) for tf in timeframes]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timeframes,
            y=returns,
            mode='lines+markers',
            name=f'{asset} Technical Forecast',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(color='#FF6B6B', size=10)
        ))
        
        # Add technical indicator reference lines if available
        if 'RSI' in indicators:
            rsi = indicators['RSI']
            if rsi < 30:
                fig.add_annotation(text="RSI Oversold", x=timeframes[-1], y=max(returns), 
                                 showarrow=True, arrowcolor="green")
            elif rsi > 70:
                fig.add_annotation(text="RSI Overbought", x=timeframes[-1], y=max(returns),
                                 showarrow=True, arrowcolor="red")
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=f'{asset} Short-Term Technical Forecast',
            xaxis_title='Weeks',
            yaxis_title='Expected Return (%)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a', family='Inter'),
            height=400
        )
        
        return fig
    
    def _create_long_term_chart(self, asset, price_targets, whale_metrics):
        """Create long-term chart with whale performance context"""
        timeframes = [tf for tf in price_targets.keys() if 'M' in tf]
        returns = [price_targets.get(tf, 0) for tf in timeframes]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timeframes,
            y=returns,
            mode='lines+markers',
            name=f'{asset} Whale-Based Forecast',
            line=dict(color='#4a6741', width=3),
            marker=dict(color='#4a6741', size=12)
        ))
        
        # Add whale performance reference line
        if whale_metrics and 'pnl_percent' in whale_metrics:
            whale_return = whale_metrics['pnl_percent']
            fig.add_hline(
                y=whale_return,
                line_dash="dot",
                line_color="#9f7aea",
                annotation_text=f"Whale Current Return: {whale_return:.1f}%"
            )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=f'{asset} Long-Term Whale-Based Forecast',
            xaxis_title='Months', 
            yaxis_title='Expected Return (%)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a', family='Inter'),
            height=450
        )
        
        return fig
    
    def _extract_price_targets(self, response):
        """Extract price targets from response"""
        import json, re
        targets = {}
        
        # Try JSON first
        json_match = re.search(r'\{[^}]*\}', response)
        if json_match:
            try:
                targets = json.loads(json_match.group(0))
                return {k.upper(): float(v) for k, v in targets.items()}
            except Exception:
                pass
        
        # Fallback patterns
        patterns = {
            '1W': r'1[\s-]?week[^\d+-]*([+-]?\d+\.?\d*)%?',
            '2W': r'2[\s-]?week[^\d+-]*([+-]?\d+\.?\d*)%?',
            '3W': r'3[\s-]?week[^\d+-]*([+-]?\d+\.?\d*)%?',
            '4W': r'4[\s-]?week[^\d+-]*([+-]?\d+\.?\d*)%?',
            '1M': r'1[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
            '3M': r'3[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
            '6M': r'6[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
            '9M': r'9[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
            '12M': r'12[\s-]?month[^\d+-]*([+-]?\d+\.?\d*)%?',
        }
        
        for tf, pat in patterns.items():
            m = re.search(pat, response, re.IGNORECASE)
            if m:
                try:
                    targets[tf] = float(m.group(1))
                except ValueError:
                    pass
        
        return targets

def main():
    """Main application function with Claude-like UI"""
    
    # Create attractive header with tool description
    st.markdown("""
        <div class="main-header">
            <div class="header-content">
                <div class="title-section">
                    <h1><span class="whale-icon">🐋</span> WhaleFlow Intelligence</h1>
                    <p class="subtitle">AI-powered crypto investment platform that tracks whale traders, validates market conditions, and forecasts performance</p>
                </div>
                <div class="feature-badges">
                    <span class="badge">🧠 Smart Whale Detection</span>
                    <span class="badge">📊 Real-Time Market Analysis</span>
                    <span class="badge">🎯 Performance Forecasting</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Load whale data
    df = load_whale_data()
    if df is None:
        st.error("❌ Unable to proceed without valid whale data.")
        return

    # Initialize agents
    agent1 = Agent1WhaleAnalyzer(openai_client)
    agent2 = Agent2SentimentValidator(openai_client)
    agent3 = Agent3PerformanceForecaster(openai_client)

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for m in st.session_state.messages:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.markdown(m["content"], unsafe_allow_html=True)

    # Capture new user input
    user_query = st.chat_input("Ask about investing in BTC, ETH, HYPE, or SOL...")

    if user_query:
        # Save & show user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # FIXED: Better greeting detection that works with "hey! something else"
        if is_greeting_query(user_query):
            greet_reply = """**🤖 Hello there!**

I'm **WhaleFlow Intelligence** - your advanced crypto investment assistant powered by three specialized AI agents:

**🧠 Agent 1: Whale Detector**  
Identifies the best-performing whale traders for your chosen cryptocurrency

**📊 Agent 2: Market Validator**  
• **Short-term**: Real-time technical analysis from market data  
• **Long-term**: Whale trading pattern analysis

**🎯 Agent 3: Performance Forecaster**  
Creates detailed forecasts and provides conversational investment guidance

**Ready to analyze:** BTC, ETH, HYPE, or SOL

*Just ask me something like "Should I invest in BTC?" or "What about ETH for long term?"*"""
            
            with st.chat_message("assistant"):
                st.markdown(greet_reply)
            st.session_state.messages.append({"role": "assistant", "content": greet_reply})
            return

        try:
            # Execute agents
            agent1_container = st.empty()
            agent1_result = agent1.analyze_query_streaming(user_query, df, agent1_container)

            if 'error' in agent1_result:
                return

            agent2_container = st.empty()
            agent2_result = agent2.validate_streaming(
                agent1_result['whale_id'],
                agent1_result['asset'], 
                agent1_result['response'],
                agent1_result.get('whale_data'),
                user_query,  # Pass original user query
                agent2_container
            )

            agent3_container = st.empty()
            agent3_result = agent3.forecast_streaming(
                agent1_result['whale_id'],
                agent1_result['asset'],
                agent1_result['response'],
                agent2_result,
                agent3_container
            )

            # Build summary message
            def _shorten(txt, max_chars=200):
                plain = re.sub(r'<[^>]+>', '', txt)
                short = textwrap.shorten(plain.replace('\n', ' '), width=max_chars, placeholder='…')
                return short

            combined_msg = (
                "**🤖 Complete Analysis Summary:**\n\n"
                "🧠 **Whale Detection** – " + _shorten(agent1_result['response']) + "\n\n"
                "📊 **Market Validation** – " + _shorten(agent2_result['response']) + "\n\n"
                "🎯 **Forecast & Guidance** – " + _shorten(agent3_result.get('conversational_summary', 'Analysis complete'))
            )

            with st.chat_message("assistant"):
                st.markdown(combined_msg, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": combined_msg})

        except Exception as e:
            err_txt = f"⚠️ Analysis error: {str(e)}"
            with st.chat_message("assistant"):
                st.error(err_txt)
            st.session_state.messages.append({"role": "assistant", "content": err_txt})

if __name__ == "__main__":
    main()
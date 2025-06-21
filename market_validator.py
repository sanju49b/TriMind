# market_validator.py
# Placeholder for market validator agent functions

import pandas as pd
import random
import traceback
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    openai_available = True
except Exception:
    openai_available = False
    traceback.print_exc()

def calculate_confidence(whale_df: pd.DataFrame) -> float:
    """
    Calculate confidence using Win Rate, Risk Score, and Confidence columns.
    confidence = 0.5*WinRate + 0.3*Confidence + 0.2*(100 - RiskScore*10)
    """
    try:
        win_rate = float(whale_df.loc[whale_df.index[0], 'Win Rate (%)'])
        confidence_col = float(whale_df.loc[whale_df.index[0], 'Confidence'])
        risk_score = float(whale_df.loc[whale_df.index[0], 'Risk Score'])
        confidence = 0.5 * win_rate + 0.3 * confidence_col + 0.2 * (100 - risk_score * 10)
        return max(0, min(100, round(confidence, 1)))
    except Exception:
        return 50.0  # fallback if data is missing or invalid

def get_verdict_from_confidence(confidence_score: float) -> str:
    """
    Decide verdict based on confidence score.
    >=80: '✅ Supported'
    60-79: '⚠️ Mixed Signals'
    40-59: '❓ Insufficient Data'
    <40: '❌ Not Supported'
    """
    if confidence_score >= 80:
        return "✅ Supported"
    elif confidence_score >= 60:
        return "⚠️ Mixed Signals"
    elif confidence_score >= 40:
        return "❓ Insufficient Data"
    else:
        return "❌ Not Supported"

def validate_whale_trades(df: pd.DataFrame, whale_id: str, asset: str = None) -> dict:
    """
    Returns a market validation verdict for the selected whale's trades using MCP server.
    Falls back to mock if OpenAI SDK or API call fails.
    """
    whale_df = df[df['Whale ID'] == whale_id].reset_index(drop=True)
    if whale_df.empty or not isinstance(whale_df, pd.DataFrame):
        return {"error": "No data for selected whale."}
    # Use asset in the question if provided
    if asset:
        question = f"Analyze the market sentiment and validate the current trades for whale: {whale_df.loc[0, 'Whale Name']} in {asset}. Provide a verdict and reasoning."
    else:
        question = f"Validate the current trades and positions for whale: {whale_df.loc[0, 'Whale Name']}. Provide a verdict and reasoning."
    confidence_score = calculate_confidence(whale_df)
    verdict = get_verdict_from_confidence(confidence_score)
    
    if openai_available:
        try:
            resp = client.responses.create(
                model="gpt-4-1106-preview",
                input=[{"role": "user", "content": question}],
                tools=[{
                    "type": "mcp",
                    "server_label": "Jenius",
                    "server_url": "https://mcp-jenius.rndm.io/sse",
                    "headers": {"Authorization": f"Bearer {os.getenv('JENIUS_MCP_TOKEN')}"},
                    "require_approval": "never"
                }],
                stream=False
            )
            return {
                "verdict": verdict + " (MCP)",
                "reason": resp.output_text,
                "confidence": confidence_score
            }
        except Exception as e:
            traceback.print_exc()
    # Fallback to mock verdict
    return {
        "verdict": verdict,
        "reason": f"Mocked market validation verdict for {whale_df.loc[0, 'Whale Name']}",
        "confidence": confidence_score
    } 
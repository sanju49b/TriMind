# strategy_generator.py
# Placeholder for strategy generator agent functions 

import pandas as pd

def generate_strategies(df: pd.DataFrame, whale_id: str) -> dict:
    """
    Returns mock strategies for the selected whale.
    """
    whale_df = df[df['Whale ID'] == whale_id]
    if whale_df.empty:
        return {"error": "No data for selected whale."}
    return {
        "Conservative": {
            "description": "Low risk, small position sizes, focus on high-confidence trades.",
            "expected_return": "+5%",
            "risk": "Low"
        },
        "Moderate": {
            "description": "Balanced risk/reward, diversified assets, moderate leverage.",
            "expected_return": "+12%",
            "risk": "Medium"
        },
        "Aggressive": {
            "description": "High risk, large positions, high leverage, quick entries/exits.",
            "expected_return": "+25%",
            "risk": "High"
        }
    } 
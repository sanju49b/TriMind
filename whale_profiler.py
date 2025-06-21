# whale_profiler.py
# Placeholder for whale profiler agent functions 

import pandas as pd

def profile_whale(df: pd.DataFrame, whale_id: str) -> dict:
    """
    Returns a summary profile for the selected whale_id from the DataFrame.
    """
    whale_df = df[df['Whale ID'] == whale_id]
    if whale_df.empty:
        return {"error": "No data for selected whale."}
    profile = {
        "Whale Name": whale_df['Whale Name'].iloc[0],
        "Total Portfolio ($)": whale_df['Total Portfolio ($)'].iloc[0],
        "Assets": whale_df['Asset'].unique().tolist(),
        "Direction Counts": whale_df['Direction'].value_counts().to_dict(),
        "Avg Leverage": whale_df['Leverage'].astype(str).str.replace('X','').astype(float).mean(),
        "Win Rate (%)": whale_df['Win Rate (%)'].iloc[0],
        "Risk Score": whale_df['Risk Score'].iloc[0],
        "Confidence": whale_df['Confidence'].iloc[0],
        "Summary": f"{whale_df['Whale Name'].iloc[0]} trades {', '.join(whale_df['Asset'].unique())} with an average leverage of {whale_df['Leverage'].astype(str).str.replace('X','').astype(float).mean():.2f}X."
    }
    return profile 
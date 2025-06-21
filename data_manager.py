# data_manager.py
# Placeholder for data loading and validation functions 

import pandas as pd
from typing import Tuple, List, Optional

REQUIRED_COLUMNS = [
    'Whale ID',
    'Wallet Address',
    'Whale Name',
    'Total Portfolio ($)',
    'Asset',
    'Direction',
    'Position Size ($)',
    'Amount',
    'PnL ($)',
    'PnL %',
    'Leverage',
    'Entry Price',
    'Current Price',
    'Weekly PnL ($)',
    'Win Rate (%)',
    'Avg Trade Size ($)',
    'Risk Score',
    'Last Active',
    'Confidence',
]

def validate_whale_data(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """
    Validates the whale trading data DataFrame.
    Returns a tuple of (cleaned DataFrame or None, list of error messages).
    """
    errors = []
    # Check for missing columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return None, errors
    # Check for empty DataFrame
    if df.empty:
        errors.append("The uploaded file is empty.")
        return None, errors
    # Optionally: check for invalid data types, NaNs, etc. (extend as needed)
    # For now, just return the DataFrame as is
    return df[REQUIRED_COLUMNS], errors 
# visualizations.py
# Placeholder for visualization/chart functions 

import pandas as pd
import plotly.express as px

# Portfolio performance over time (mocked by using Last Active as x, Total Portfolio as y)
def portfolio_performance_chart(whale_df: pd.DataFrame):
    df = whale_df.copy()
    df = df.sort_values('Last Active')
    fig = px.line(df, x='Last Active', y='Total Portfolio ($)', title='Portfolio Performance Over Time')
    return fig

# Asset allocation pie chart
def asset_allocation_chart(whale_df: pd.DataFrame):
    asset_sums = whale_df.groupby('Asset')['Position Size ($)'].sum().reset_index()
    fig = px.pie(asset_sums, names='Asset', values='Position Size ($)', title='Asset Allocation')
    return fig

# Win rate and PnL distribution (bar chart)
def winrate_pnl_chart(whale_df: pd.DataFrame):
    df = whale_df.copy()
    df['PnL ($)'] = pd.to_numeric(df['PnL ($)'].astype(str).str.replace(',', ''), errors='coerce')
    fig = px.bar(df, x='Asset', y='PnL ($)', color='Direction', title='PnL Distribution by Asset')
    return fig 
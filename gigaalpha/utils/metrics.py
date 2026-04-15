import pandas as pd
from typing import Dict, Optional, Any, List

def calc_sharpe_tvr_summary(
    df: pd.DataFrame, 
    segment_val: str, 
    segment_col: str = 'segment', 
    shrape_col: str = 'sharpe', 
    lst_sharpe_threshold: List[float] = [0, 1, 2], 
    tvr_col: str = 'tvr'
) -> Optional[Dict[str, Any]]:
    """
    Utility function to calculate performance summary metrics for a specific segment.
    Input: DataFrame of backtest results.
    Output: Dictionary with summary stats.
    """
    if df.empty or segment_col not in df.columns:
        return None
    
    # Filter for segment and ensure active trading (tvr > 0)
    df_seg = df[(df[segment_col] == segment_val) & (df[tvr_col] > 0)].copy()
    if df_seg.empty:
        return None

    total_runs = len(df_seg)
    get_pct = lambda thres: round(len(df_seg[df_seg[shrape_col].fillna(0) > thres]) / total_runs * 100, 2)
    
    res = {
        'Segment':      segment_val,
        'TotalConfigs':   total_runs,
    }
    for threshold in lst_sharpe_threshold:
        res[f'Sharpe > {threshold} (%)'] = get_pct(threshold)
        
    res['TVR (mean)'] = float(round(df_seg[tvr_col].mean(), 4))
    return res

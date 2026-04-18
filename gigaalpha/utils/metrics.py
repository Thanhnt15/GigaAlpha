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
    if df.empty or segment_col not in df.columns:
        return None
    
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

def calc_custom_segment_metrics(
    df: pd.DataFrame,
    segment_val: str,
    lst_n_profit: List[float] = [5, 10, 20],
    segment_col: str = 'segment',
    sharpe_col: str = 'sharpe',
    profit_col: str = 'netProfit',
    mdd_col: str = 'mddPct',
    tvr_col: str = 'tvr'
) -> Optional[Dict[str, Any]]:
    if df.empty or segment_col not in df.columns:
        return None
        
    df_seg = df[df[segment_col] == segment_val].copy()
    if df_seg.empty:
        return None
        
    total_configs = len(df_seg)
    
    sharpe_mask = df_seg[sharpe_col] > 1
    profit_mask = df_seg[profit_col] > 0
    
    res = {
        'Segment': segment_val,
        'TotalConfigs': total_configs,
        'NetProfit > 0': f"{int(profit_mask.sum())} ({round(profit_mask.sum() / total_configs * 100, 2)}%)",
        'Sharpe > 1': f"{int(sharpe_mask.sum())} ({round(sharpe_mask.sum() / total_configs * 100, 2)}%)",
    }

    for n in lst_n_profit:
        combo_mask = (df_seg[profit_col] > n) & (df_seg[mdd_col] < 20)
        combo_df = df_seg[combo_mask]
        
        count = int(combo_mask.sum())
        ratio = round(count / total_configs * 100, 2)
        tvr_avg = round(combo_df[tvr_col].mean(), 4) if not combo_df.empty else 0.0
        
        res[f'[Net>{n}, MDD<20]'] = f"{count} ({ratio}%)"
        res[f'TVR (Net>{n})'] = float(tvr_avg)
    
    return res

import pandas as pd
from typing import Dict, Optional, Any, List

def calc_sharpe_tvr_summary(
    df: pd.DataFrame, 
    segment_val: str, 
    shrape_col: str = 'sharpe', 
    lst_sharpe_threshold: List[float] = [0, 1, 2], 
    tvr_col: str = 'tvr'
) -> Optional[Dict[str, Any]]:
    if df.empty:
        return None
    
    df_seg = df[df[tvr_col] > 0].copy()
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

def calc_custom_statistics(
    df: pd.DataFrame,
    lst_n_profit: List[float] = [5, 10, 20],
    sharpe_col: str = 'sharpe',
    profit_col: str = 'netProfit',
    mdd_col: str = 'mddPct',
    tvr_col: str = 'tvr'
) -> Optional[List[Dict[str, Any]]]:
    if df.empty:
        return None
        
    df_seg = df[df[tvr_col] > 0].copy()
    if df_seg.empty:
        return None
    
    total_configs = len(df_seg)
    sharpe_mask = df_seg[sharpe_col] > 1
    profit_mask = df_seg[profit_col] > 0
    
    rows = [
        {'Metric': 'TotalConfigs',   'Value': total_configs, 'Avg TVR': ''},
        {'Metric': 'NetProfit > 0',  'Value': f"{int(profit_mask.sum())} ({round(profit_mask.sum() / total_configs * 100, 2)}%)", 'Avg TVR': ''},
        {'Metric': 'Sharpe > 1',     'Value': f"{int(sharpe_mask.sum())} ({round(sharpe_mask.sum() / total_configs * 100, 2)}%)", 'Avg TVR': ''},
    ]

    for n in lst_n_profit:
        combo_mask = (df_seg[profit_col] > n) & (df_seg[mdd_col] < 20)
        combo_df = df_seg[combo_mask]
        
        count = int(combo_mask.sum())
        ratio = round(count / total_configs * 100, 2)
        tvr_avg = round(combo_df[tvr_col].mean(), 4) if not combo_df.empty else 0.0
        
        rows.append({
            'Metric': f'[Net>{n}, MDD<20]', 
            'Value': f"{count} ({ratio}%)",
            'Avg TVR': float(tvr_avg)
        })
    
    return rows

def sharpe_stats_by_freq(
    df: pd.DataFrame, 
    freq_col: str = 'frequency', 
    shrape_col: str = 'sharpe',
    lst_sharpe_threshold: List[float] = [1, 2, 3],
    tvr_col: str = 'tvr'
) -> Optional[Dict[str, Any]]:
    df = df[df[tvr_col] > 0]
    total = df.groupby(freq_col)[shrape_col].count().rename('total')
    
    rows = {'total': total}
    for t in lst_sharpe_threshold:
        count = df[df[shrape_col] > t].groupby(freq_col)[shrape_col].count()
        pct = (count / total * 100).round(2).fillna(0)
        count = count.fillna(0).astype(int)
        rows[f'sharpe > {t}'] = count.astype(str) + ' (' + pct.astype(str) + '%)'

    result = pd.DataFrame(rows).fillna('0 (0.0%)')
    result['total'] = result['total'].astype(int)
    return result

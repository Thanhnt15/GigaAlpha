import numpy as np
import pandas as pd
from typing import Dict, List, Any

def compute_scores(
    chunk_df: pd.DataFrame, 
    sharpe_map: Dict[str, float], 
    dim_values: Dict[int, List[str]], 
    dim_value_to_idx: Dict[int, Dict[str, int]], 
    num_neighbors: int, 
    col_target: str, 
    col_strategy: str, 
    mode_test: bool = False
) -> List[Dict[str, Any]]:
    """
    Core scoring logic (L1/L2).
    Moved to utils for portability and cleanup.
    """
    results = []
    
    params_count = len(dim_values)
    half = num_neighbors // 2
    steps = [s for s in range(-half, half + 1) if s != 0]
    
    for _, row in chunk_df.iterrows():
        curr_strat = str(row[col_strategy]).strip()
        curr_sharpe = float(row[col_target])
        
        res = {'Score_L1': 0, 'Score_L2': 0}
        if mode_test: res['Strategy_neighbor_fail'] = ""

        if pd.isna(curr_sharpe) or curr_sharpe <= 0:
            results.append(res); continue

        curr_p_list = curr_strat.split('_')
        score_l1 = 0
        l1_strategy_map = {} 

        for i in range(params_count):
            if i >= len(curr_p_list): continue
            
            p_values = dim_values[i]
            p_v_to_idx = dim_value_to_idx[i]
            
            p_val = curr_p_list[i]
            if p_val not in p_v_to_idx:
                continue
            p_idx = p_v_to_idx[p_val]

            is_dim_l1_ok = True
            valid_l1_strategies = []

            for s in steps:
                nb_idx = p_idx + s
                if 0 <= nb_idx < len(p_values):
                    nb_p = curr_p_list.copy()
                    nb_p[i] = p_values[nb_idx]
                    l1_strategy = "_".join(nb_p)

                    if l1_strategy in sharpe_map:
                        l1_sharpe = sharpe_map[l1_strategy]
                        if pd.isna(l1_sharpe) or float(l1_sharpe) <= 0:
                            is_dim_l1_ok = False
                            if mode_test and not res['Strategy_neighbor_fail']: 
                                res['Strategy_neighbor_fail'] = f"L1_Fail:{l1_strategy}"
                            break
                        valid_l1_strategies.append(l1_strategy)
            
            if is_dim_l1_ok:
                score_l1 += 1
                l1_strategy_map[i] = valid_l1_strategies

        if score_l1 == params_count:
            res['Score_L1'] = 1
            score_l2 = 0

            for i, l1_strategies in l1_strategy_map.items():
                is_dim_l2_ok = True
                for l1_strat_item in l1_strategies:
                    l1_p = l1_strat_item.split('_')
                    if i >= len(l1_p): continue
                    
                    l1_v_val = l1_p[i]
                    if l1_v_val not in dim_value_to_idx[i]: continue
                    l1_v_idx = dim_value_to_idx[i][l1_v_val]

                    for s2 in steps:
                        l2_idx = l1_v_idx + s2
                        if 0 <= l2_idx < len(dim_values[i]):
                            l2_p = l1_p.copy()
                            l2_p[i] = dim_values[i][l2_idx]
                            l2_strategy = "_".join(l2_p)
                            
                            if l2_strategy != curr_strat and l2_strategy in sharpe_map:
                                l2_sharpe = sharpe_map[l2_strategy]
                                if pd.isna(l2_sharpe) or float(l2_sharpe) <= 0:
                                    is_dim_l2_ok = False
                                    if mode_test:
                                        res['Strategy_neighbor_fail'] = f"L2_Fail:{l2_strategy}"
                                    break
                    if not is_dim_l2_ok: break
                
                if is_dim_l2_ok:
                    score_l2 += 1
            
            if score_l2 == params_count:
                res['Score_L2'] = 1
        results.append(res)
    return results

import pandas as pd
from gigaalpha.core.registry import register_alpha
from gigaalpha.core.operators import O

@register_alpha(param_ranges={
    'window': [1,2,3,4],
    'window_rank': list(range(10,101,10)),
})
def alpha_001(df: pd.DataFrame,window=1, window_rank=20):
    returns = (df['close'] - O.ts_lag(df['close'], window)) / (O.ts_lag(df['close'], 1) + 1e-8)
    
    volume = df.get('volume', df.get('matchingVolume'))
    raw_flow = returns * volume
    ranked_signal = O.ts_rank_normalized(raw_flow, window_rank)
    signal = (2 * ranked_signal) - 1
    
    return signal.fillna(0)
import pandas as pd
import numpy as np
from gigaalpha.core.registry import register_alpha


# @register_alpha(param_ranges={
#     'window_fast': [10, 12, 15],
#     'window_slow': [20, 26, 30],
# })
# def alpha_001(df, window_fast=12, window_slow=26) -> pd.Series:
#     ema_f = df['close'].ewm(span=window_fast, adjust=False).mean()
#     ema_s = df['close'].ewm(span=window_slow, adjust=False).mean()
#     diff = ema_f - ema_s
#     std = diff.rolling(window=window_slow).std()
#     vol_sma = df['matchedVolume'].rolling(window=window_slow).mean()
#     vol_ratio = (df['matchedVolume'] / (vol_sma + 1e-9)).clip(0, 2) / 2 
#     signal = (diff / (std * 2 + 1e-9)).clip(-1, 1).fillna(0)

#     return -signal * vol_ratio

@register_alpha(param_ranges={
    'window': [10, 20, 30],
    'factor': [0, 0.2],
})
def alpha_001(df, window=20, factor=0) -> pd.Series:
    relative_intensity = df['hose_Busd'] / (df['matchingVolume'] + 1e-9)

    signal = np.tanh(relative_intensity * 2.5) 
    if factor > 0:
        signal = signal.ewm(halflife=factor).mean()

    return signal.rolling(window=window, min_periods=window//2).rank(pct=True) * 2 - 1
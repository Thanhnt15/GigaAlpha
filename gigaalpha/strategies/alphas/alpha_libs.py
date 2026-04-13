import pandas as pd
from gigaalpha.core.registry import register_alpha


@register_alpha(param_ranges={
    'window_fast': [10, 12, 15],
    'window_slow': [20, 26, 30],
})
def alpha_001(df, window_fast=12, window_slow=26) -> pd.Series:
    ema_f = df['close'].ewm(span=window_fast, adjust=False).mean()
    ema_s = df['close'].ewm(span=window_slow, adjust=False).mean()
    diff = ema_f - ema_s
    std = diff.rolling(window=window_slow).std()
    vol_sma = df['matchedVolume'].rolling(window=window_slow).mean()
    vol_ratio = (df['matchedVolume'] / (vol_sma + 1e-9)).clip(0, 2) / 2 
    signal = (diff / (std * 2 + 1e-9)).clip(-1, 1).fillna(0)

    return -signal * vol_ratio
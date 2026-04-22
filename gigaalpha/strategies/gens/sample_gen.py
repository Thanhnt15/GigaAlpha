import numpy as np
import pandas as pd
from gigaalpha.core.registry import register_gen

@register_gen(param_range={
    'threshold': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    'half_life': [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
})
def gen_sample(signal: pd.Series, threshold=0.3, half_life=0) -> pd.Series:
    if half_life > 0:
        signal = signal.ewm(halflife=half_life).mean()
    position = pd.Series(np.nan, index=signal.index)
    position
    return position
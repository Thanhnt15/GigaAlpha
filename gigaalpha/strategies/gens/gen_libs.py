import numpy as np
import pandas as pd
from gigaalpha.core.registry import register_gen

@register_gen(param_ranges={
    'threshold': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
})
def gen_1_1(signal: pd.Series, threshold=0.3) -> pd.Series:
    position = pd.Series(np.nan, index=signal.index)
    position.loc[signal > threshold] = 1
    position.loc[signal < -threshold] = -1
    return position

import logging
import pandas as pd
from typing import Dict, Any, Optional, List
from gigaalpha.utils.metrics import calc_sharpe_tvr_summary, calc_custom_segment_metrics

logger = logging.getLogger(__name__)

class StatisticsService:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run_statistics(self, segment_val: str) -> Optional[Dict[str, Any]]:
        return calc_sharpe_tvr_summary(self.df, segment_val)

    def run_custom_statistics(self, segment_val: str, lst_n_profit: List[float] = [5, 10, 20]) -> Optional[Dict[str, Any]]:
        return calc_custom_segment_metrics(self.df, segment_val, lst_n_profit)

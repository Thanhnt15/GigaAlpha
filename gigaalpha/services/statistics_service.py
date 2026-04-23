import logging
import pandas as pd
from typing import Dict, Any, Optional, List
from gigaalpha.utils.metrics import calc_sharpe_tvr_summary, calc_custom_statistics, sharpe_stats_by_freq

logger = logging.getLogger(__name__)

class StatisticsService:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run_statistics(self, segment_val: str) -> Optional[Dict[str, Any]]:
        return calc_sharpe_tvr_summary(self.df, segment_val)

    def run_custom_statistics(self, lst_n_profit: List[float]) -> Optional[pd.DataFrame]:
        return calc_custom_statistics(self.df, lst_n_profit)
        
    def run_sharpe_stats_by_freq(self, lst_sharpe_threshold: List[float]) -> Optional[Dict[str, Any]]:
        return sharpe_stats_by_freq(self.df, lst_sharpe_threshold=lst_sharpe_threshold)
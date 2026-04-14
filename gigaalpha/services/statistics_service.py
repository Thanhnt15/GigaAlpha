import logging
import pandas as pd
from typing import Dict, Any, Optional
from gigaalpha.utils.metrics import calc_sharpe_tvr_summary

logger = logging.getLogger(__name__)

class StatisticsService:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run_statistics(self, segment_val: str) -> Optional[Dict[str, Any]]:
        return calc_sharpe_tvr_summary(self.df, segment_val)


import logging
import pandas as pd
from typing import List
from gigaalpha.utils.visualize import plot_sharpe_surface

logger = logging.getLogger(__name__)

class VisualizationService:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run_visualization(self, title: str, target_cols: List[str], colors: List[str], output_path: str):
        plot_sharpe_surface(df=self.df, title=title, target_cols=target_cols, colors=colors, output_path=output_path)
        
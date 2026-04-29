import pandas as pd
import os
import logging
from gigaalpha.utils.excel_fomat import (
    sort_report_data, 
    rename_and_reorder_report_columns, 
    apply_excel_report_formatting
)

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self, df: pd.DataFrame, output_path: str):
        self.df = df.copy()
        self.output_path = output_path
    
    def save_to_xlsx(self, summary_df: pd.DataFrame = None, sharpe_stats_df: pd.DataFrame = None):
        try:
            processed_df = sort_report_data(self.df)
            processed_df = rename_and_reorder_report_columns(processed_df)
            
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            writer = pd.ExcelWriter(self.output_path, engine='xlsxwriter')
            processed_df.to_excel(writer, index=False, sheet_name='Report')
            
            next_col = len(processed_df.columns)

            if summary_df is not None:
                summary_df.to_excel(writer, index=False, sheet_name='Report', startcol=next_col)
                next_col += len(summary_df.columns)
            
            if sharpe_stats_df is not None:
                sharpe_stats_df.to_excel(writer, index=True, sheet_name='Report', startcol=next_col)
            
            # Apply formatting with all pieces
            apply_excel_report_formatting(
                writer.book, 
                writer.sheets['Report'], 
                processed_df, 
                summary_df=summary_df,
                sharpe_stats_df=sharpe_stats_df
            )

            writer.close()
            logger.info(f"Excel report saved: {self.output_path} ({len(processed_df)} rows)")
        except Exception:
            logger.exception(f"Failed to save Excel report: {self.output_path}")

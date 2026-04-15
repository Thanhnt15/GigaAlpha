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
    
    def save_to_xlsx(self):
        try:
            processed_df = sort_report_data(self.df)
            processed_df = rename_and_reorder_report_columns(processed_df)
            
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            writer = pd.ExcelWriter(self.output_path, engine='xlsxwriter')
            processed_df.to_excel(writer, index=False, sheet_name='Report')
            apply_excel_report_formatting(writer.book, writer.sheets['Report'], processed_df)

            writer.close()
            logger.info(f"Excel report saved: {self.output_path} ({len(processed_df)} rows)")
        except Exception:
            logger.exception(f"Failed to save Excel report: {self.output_path}")

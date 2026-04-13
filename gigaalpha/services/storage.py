from gigaalpha.utils.excel_fomat import ExcelFomat
import pandas as pd
class StorageService:
    def __init__(self, df: pd.DataFrame, output_path: str):
        self.df = df
        self.output_path = output_path
    
    def save_to_xlsx(self):
        ExcelFomat(self.df).save_to_xlsx(self.output_path)


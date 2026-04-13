import pandas as pd
import numpy as np
import logging
from xlsxwriter.utility import xl_col_to_name
import os

logger = logging.getLogger(__name__)

class ExcelFomat:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def sort_data(self) -> pd.DataFrame:
        """Sort rows based on backtest parameters."""
        global_paras = ['bar_size']
        alpha_params = sorted([c for c in self.df.columns if c.startswith('alpha_') and c != 'alpha_name'])
        gen_params = sorted([c for c in self.df.columns if c.startswith('gen_') and c != 'gen_name'])
        
        sort_priority = [c for c in global_paras if c in self.df.columns]
        sort_priority.extend(alpha_params)
        sort_priority.extend(gen_params)
        
        if sort_priority:
            self.df = self.df.sort_values(by=sort_priority, ascending=True).reset_index(drop=True)
        return self.df

    def rename_and_reorder_columns(self) -> pd.DataFrame:
        """Rename columns to reporting standards and reorder linearly."""
        mapping = {
            'strategy': 'Strategy',
            'bar_size': 'Bar_Size',
            'sharpe': 'Sharpe Ratio',
            'hhi': 'HHI',
            'psr': 'PSR (%)',
            'dsr': 'DSR (%)',
            'mdd': 'MDD',
            'mddPct': 'MDD (%)',
            'ppc': 'PPC',
            'tvr': 'TVR',
            'netProfit': 'Net Profit',
        }
        
        for col in self.df.columns:
            if col.startswith('alpha_') or col.startswith('gen_'):
                mapping[col] = col.title()

        df_new = self.df.rename(columns=mapping)

        strategy_col = ['Strategy']
        base_param_col = ['Bar_Size']
        alpha_cols = sorted([c.title() for c in self.df.columns if c.startswith('alpha_') and c != 'alpha_name'])
        gen_cols = sorted([c.title() for c in self.df.columns if c.startswith('gen_') and c != 'gen_name'])
        
        score_cols = ['Score_L1', 'Score_L2', 'Strategy_neighbor_fail']
        perf_cols = ['Sharpe Ratio', 'HHI', 'PSR (%)', 'DSR (%)', 'MDD', 'MDD (%)', 'PPC', 'TVR', 'Net Profit', ]
        
        expected_order = (
            perf_cols + 
            score_cols + 
            base_param_col + 
            alpha_cols + 
            gen_cols + 
            strategy_col 
        )
        
        final_cols = [c for c in expected_order if c in df_new.columns]
        self.df = df_new[final_cols]
        return self.df

    def apply_formatting(self, workbook, worksheet):
        """Apply styles, column widths (sampling), and conditional formatting."""
        num_rows = len(self.df)
        last_row = num_rows + 1

        # Styles
        header_fmt = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#366092',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        data_fmt = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })

        # Column width optimization (1000 row sampling)
        sample_rows = min(num_rows, 1000)
        df_sample = self.df.head(sample_rows)
        
        for i, col in enumerate(self.df.columns):
            worksheet.write(0, i, col, header_fmt)
            
            max_len = df_sample[col].astype(str).map(len).max()
            max_len = max(max_len, len(str(col))) + 3
            worksheet.set_column(i, i, min(max_len, 50), data_fmt)

        # 3-color and 2-color scales for key metrics
        color_rules = {
            'Sharpe Ratio': {
                'type': '3_color_scale',
                'min_color': "#F8696B", 'mid_color': "#FFEB9C", 'max_color': "#63BE7B",
                'min_type': 'num', 'min_value': 0,
                'mid_type': 'num', 'mid_value': 1.5,
                'max_type': 'num', 'max_value': 3.5
            },
            'MDD (%)': {
                'type': '3_color_scale',
                'min_color': "#63BE7B", 'mid_color': "#FFEB9C", 'max_color': "#F8696B",
                'min_type': 'num', 'min_value': 0,
                'mid_type': 'num', 'mid_value': 0.2,
                'max_type': 'num', 'max_value': 0.5
            },
            'PPC': {
                'type': '3_color_scale',
                'min_color': "#F8696B", 'mid_color': "#FFEB9C", 'max_color': "#63BE7B",
                'min_type': 'min', 'mid_type': 'num', 'mid_value': 0, 'max_type': 'max'
            },
            'TVR': {
                'type': '3_color_scale',
                'min_color': "#63BE7B", 'mid_color': "#FFEB9C", 'max_color': "#F8696B",
                'min_type': 'min', 'mid_type': 'percentile', 'mid_value': 50, 'max_type': 'max'
            },
            'Score_L1': {
                'type': '2_color_scale',
                'min_color': "#F8696B", 'max_color': "#63BE7B",
                'min_type': 'num', 'min_value': 0, 'max_type': 'num', 'max_value': 1
            },
            'Score_L2': {
                'type': '2_color_scale',
                'min_color': "#F8696B", 'max_color': "#63BE7B",
                'min_type': 'num', 'min_value': 0, 'max_type': 'num', 'max_value': 1
            }
        }

        for i, col in enumerate(self.df.columns):
            if col in color_rules:
                col_name = xl_col_to_name(i)
                range_str = f"{col_name}2:{col_name}{last_row}"
                worksheet.conditional_format(range_str, color_rules[col])

    def save_to_xlsx(self, output_path: str):
        """Main orchestrator: Process data -> Setup Writer -> Apply Formatting -> Save."""
        self.sort_data()
        self.rename_and_reorder_columns()
        
        # High-performance streaming engine
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        self.df.to_excel(writer, index=False, sheet_name='Report')
        
        self.apply_formatting(writer.book, writer.sheets['Report'])
        # 5. Đóng writer và xuất kết quả
        writer.close()
        num_rows = len(self.df)
        logger.info(f"Excel report exported successfully: {output_path} ({num_rows} rows)")

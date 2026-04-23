import pandas as pd
import logging
from xlsxwriter.utility import xl_col_to_name

logger = logging.getLogger(__name__)

def sort_report_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    global_paras = ['frequency']
    alpha_params = sorted([c for c in df.columns if c.startswith('alpha_') and c != 'alpha_name'])
    gen_params = sorted([c for c in df.columns if c.startswith('gen_') and c != 'gen_name'])
    
    sort_priority = [c for c in global_paras if c in df.columns]
    sort_priority.extend(gen_params)
    sort_priority.extend(alpha_params)
    
    if sort_priority:
        df = df.sort_values(by=sort_priority, ascending=True).reset_index(drop=True)
    return df

def rename_and_reorder_report_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        'strategy': 'Strategy',
        'frequency': 'Frequency',
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
    
    for col in df.columns:
        if col.startswith('alpha_') or col.startswith('gen_'):
            mapping[col] = col.title()

    df_new = df.rename(columns=mapping)

    strategy_col = ['Strategy']
    base_param_col = ['Frequency']
    alpha_cols = sorted([c.title() for c in df.columns if c.startswith('alpha_') and c != 'alpha_name'])
    gen_cols = sorted([c.title() for c in df.columns if c.startswith('gen_') and c != 'gen_name'])
    
    score_cols = ['Score_L1', 'Score_L2', 'Strategy_neighbor_fail']
    perf_cols = ['Sharpe Ratio', 'HHI', 'PSR (%)', 'DSR (%)', 'MDD', 'MDD (%)', 'PPC', 'TVR', 'Net Profit', ]
    
    expected_order = (
        perf_cols + 
        score_cols + 
        base_param_col + 
        gen_cols + 
        alpha_cols + 
        strategy_col 
    )
    
    final_cols = [c for c in expected_order if c in df_new.columns]
    return df_new[final_cols]

def apply_excel_report_formatting(workbook, worksheet, df: pd.DataFrame, summary_df: pd.DataFrame = None, sharpe_stats_df: pd.DataFrame = None):
    num_rows = len(df)
    last_row = num_rows + 1

    header_fmt = workbook.add_format({
        'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#366092',
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    data_fmt = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    
    # Range color formats (Low, Mid, High)
    f_red = workbook.add_format({'bg_color': '#F8696B', 'border': 1, 'align': 'center'})
    f_yel = workbook.add_format({'bg_color': '#FFEB9C', 'border': 1, 'align': 'center'})
    f_grn = workbook.add_format({'bg_color': '#63BE7B', 'border': 1, 'align': 'center'})

    # 1. Main Report Formatting
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
    for i, col in enumerate(df.columns):
        worksheet.write(0, i, col, header_fmt)
        for r, val in enumerate(df[col]):
            worksheet.write(r + 1, i, val, data_fmt)
        max_len = max(df[col].astype(str).map(len).max() if not df.empty else 0, len(str(col))) + 1
        worksheet.set_column(i, i, min(max_len, 50))
        if col in color_rules:
            worksheet.conditional_format(f"{xl_col_to_name(i)}2:{xl_col_to_name(i)}{last_row}", color_rules[col])

    next_col = len(df.columns)

    # 2. Vertical Summary Formatting (Row-based Coloring)
    if summary_df is not None:
        for i, col in enumerate(summary_df.columns):
            curr_col = next_col + i
            worksheet.write(0, curr_col, col, header_fmt)
            for r, val in enumerate(summary_df[col]):
                fmt = data_fmt
                if col == 'Value':
                    metric = str(summary_df.iloc[r]['Metric'])
                    try:
                        if 'NetProfit > 0' in metric:
                            p = float(str(val).split('(')[1].split('%')[0])
                            fmt = f_red if p < 60 else (f_yel if p < 80 else f_grn)
                        elif 'Sharpe > 1' in metric:
                            p = float(str(val).split('(')[1].split('%')[0])
                            fmt = f_red if p < 30 else (f_yel if p < 50 else f_grn)
                    except: pass
                worksheet.write(r + 1, curr_col, val, fmt)
            max_len = max(summary_df[col].astype(str).map(len).max() if not summary_df.empty else 0, len(str(col))) + 1
            worksheet.set_column(curr_col, curr_col, min(max_len, 50))
        next_col += len(summary_df.columns)

    # 3. Sharpe Stats Formatting (Column-based Coloring)
    if sharpe_stats_df is not None:
        temp_df = sharpe_stats_df.reset_index()
        for i, col in enumerate(temp_df.columns):
            curr_col = next_col + i
            worksheet.write(0, curr_col, col, header_fmt)
            for r, val in enumerate(temp_df[col]):
                fmt = data_fmt
                try:
                    if 'sharpe > 0' in str(col).lower():
                        p = float(str(val).split('(')[1].split('%')[0])
                        fmt = f_red if p < 60 else (f_yel if p < 80 else f_grn)
                    elif 'sharpe > 1' in str(col).lower():
                        p = float(str(val).split('(')[1].split('%')[0])
                        fmt = f_red if p < 30 else (f_yel if p < 50 else f_grn)
                except: pass
                worksheet.write(r + 1, curr_col, val, fmt)
            max_len = max(temp_df[col].astype(str).map(len).max() if not temp_df.empty else 0, len(str(col))) + 1
            worksheet.set_column(curr_col, curr_col, min(max_len, 50))


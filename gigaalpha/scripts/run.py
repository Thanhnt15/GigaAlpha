import sys, pandas as pd, yaml, argparse
import logging
from pathlib import Path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT))

import gigaalpha.strategies
from gigaalpha.services.backtest import BacktestService
from gigaalpha.services.statistic import Statistics
from gigaalpha.core.scanner import ScanParams
from gigaalpha.utils.config import PipelineConfig
from gigaalpha.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger("run")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Sequential Backtest")
    parser.add_argument('--config', default='configs/default.yaml', help='Path to YAML config file')
    args = parser.parse_args()

    # Load Config
    pipeline_config = PipelineConfig.load(PROJECT_ROOT / args.config)
    bt_config = pipeline_config.backtest

    lst_configs = ScanParams.gen_all_params(
        alpha_name = bt_config.alpha_name,
        gen_name = bt_config.gen_name,
        lst_bar_size = bt_config.lst_bar_size,
        lst_fee = bt_config.lst_fee,
    )

    logger.info(f"Running sequentially backtest")
    logger.info(f'Alpha: {bt_config.alpha_name} | Gen: {bt_config.gen_name} | Total configs: {len(lst_configs)}')
    
    backtester = BacktestService(dic_data = pd.read_pickle(PROJECT_ROOT / pipeline_config.data.path), segments=pipeline_config.data.segments)
    reports = pd.DataFrame(backtester.run_sequential(lst_configs))

    logger.info(f'Statistics summary:')
    results = []      
    for segment in pipeline_config.data.segments:  
        segment_val = f'{segment[0]}_{segment[1]}'
        res = Statistics.calc_sharpe_tvr_summary(df=reports[reports['segment'] == segment_val], segment_val=segment_val)
        logger.info(res)



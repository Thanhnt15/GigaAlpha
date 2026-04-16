import sys, logging, pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT))

from gigaalpha.services.backtest_service import BacktestService
from gigaalpha.services.statistics_service import StatisticsService
from gigaalpha.helpers.system import System
import gigaalpha.strategies 

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.Formatter.converter = System.vn_time_converter
logger = logging.getLogger(__name__)

DATA_PATH = PROJECT_ROOT / "data/dic_freqs.pickle"
SEGMENTS = [["2018_01_01", "2020_01_01"]]
LST_CONFIGS = [
    {
        'alpha_name': 'popbo_003', 'window': 1, 'window_rank': 10, 
        'gen_name': '1_1', 'threshold': 0.1, 'half_life': 0,
        'frequency': 10, 'fee': 0.175,
    }
]

if __name__ == '__main__':
    logger.info(f"Loading data: {DATA_PATH}")
    dic_data = pd.read_pickle(DATA_PATH)
    
    backtester = BacktestService(dic_data=dic_data, segments=SEGMENTS)
    reports = pd.DataFrame(backtester.run_sequential(LST_CONFIGS))
    
    print(reports.to_string(index=False))

    for segment in SEGMENTS:
        segment_val = f"{segment[0]}_{segment[1]}"
        res = StatisticsService(df=reports[reports['segment'] == segment_val]).run_statistics(segment_val)
        logger.info(res)

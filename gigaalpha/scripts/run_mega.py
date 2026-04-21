import pandas as pd
from gigaalpha.services.backtest_mega_service import BacktestMegaService

DATA_PATH = '/home/ubuntu/GigaAlpha/data/dic_freqs_vnindex.pickle'
ALPHA_NAME = '005'
GEN_NAME = '1_1'
FEE = 0.175
CORES = 20

STRATEGY_IDS = [
    "10_5_0_0.1",
    "10_5_0_0.2",
]

SEGMENTS = [
    ["2022_01_01", "2026_01_01"],
]

if __name__ == "__main__":
    dic_data = pd.read_pickle(DATA_PATH)
    
    svc = BacktestMegaService(
        dic_data=dic_data,
        segments=SEGMENTS,
        fee=FEE,
    )

    reports = svc.run_parallel(ALPHA_NAME, GEN_NAME, STRATEGY_IDS, cores=CORES)

    for r in reports:
        print(r)

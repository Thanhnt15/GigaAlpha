import logging
import pandas as pd
import multiprocessing as mp
from typing import List, Dict, Any, Optional

from gigaalpha.core.mega import MegaSimulator
from gigaalpha.core.metrics import AlphaDomains

logger = logging.getLogger(__name__)

_DIC_DATA_WORKER  = None
_SEGMENTS_WORKER  = None


def _init_data(data: pd.DataFrame, segments: List):
    global _DIC_DATA_WORKER, _SEGMENTS_WORKER
    if _DIC_DATA_WORKER is None:
        _DIC_DATA_WORKER = data
    if _SEGMENTS_WORKER is None:
        _SEGMENTS_WORKER = segments



def _simulate_component_worker(task: Dict[str, Any]):
    from gigaalpha.core.simulator import Simulator
    from gigaalpha.core.mega import MegaSimulator
    import gigaalpha.strategies
    try:
        freq, a_p, g_p = MegaSimulator._parse_id(task['strategy_id'], task['alpha_name'], task['gen_name'])
        sim = Simulator(
            data=_DIC_DATA_WORKER[freq],
            frequency=freq,
            alpha_name=task['alpha_name'],
            alpha_params=a_p,
            gen_name=task['gen_name'],
            gen_params=g_p,
            fee=task['fee'],
        )
        sim.compute_signal()
        sim.compute_position()
        return sim.data['position'].copy()
    except Exception as e:
        logger.error(f"Worker failed for strategy {task.get('strategy_id', '?')}: {e}")
        raise e


class BacktestMegaService:
    def __init__(self, dic_data: Dict, segments: List, fee: float = 0.175):
        self.dic_data = dic_data
        self.segments = segments
        self.fee      = fee

    def _build_tasks(self, alpha_name: str, gen_name: str, strategy_ids: List[str]) -> List[Dict]:
        return [
            {'strategy_id': sid, 'alpha_name': alpha_name, 'gen_name': gen_name, 'fee': self.fee}
            for sid in strategy_ids
        ]

    def _execute_mega(self, alpha_name: str, gen_name: str, base_freq: int, positions: List) -> List[Dict[str, Any]]:
        mega = MegaSimulator(self.dic_data[base_freq], alpha_name, gen_name, [], self.fee)
        mega.compute_mega_position(positions_list=positions)
        mega.compute_tvr_and_fee()
        mega.compute_profits()

        df_1d = AlphaDomains.aggregate_to_1d(mega.data)
        reports = []
        for segment in self.segments:
            start, end = segment[0], segment[1]
            report = mega.compute_performance(df_1d, start, end)
            report['segment'] = f'{start}_{end}'
            reports.append(report)
        return reports

    def run_sequential(self, alpha_name: str, gen_name: str, strategy_ids: List[str]) -> List[Dict[str, Any]]:
        global _DIC_DATA_WORKER, _SEGMENTS_WORKER
        _DIC_DATA_WORKER = self.dic_data
        _SEGMENTS_WORKER = self.segments

        base_freq = int(strategy_ids[0].split('_')[0])
        tasks = self._build_tasks(alpha_name, gen_name, strategy_ids)
        positions = [_simulate_component_worker(task) for task in tasks]
        return self._execute_mega(alpha_name, gen_name, base_freq, positions)

    def run_parallel(self, alpha_name: str, gen_name: str, strategy_ids: List[str], cores: int) -> List[Dict[str, Any]]:
        base_freq = int(strategy_ids[0].split('_')[0])
        tasks = self._build_tasks(alpha_name, gen_name, strategy_ids)
        with mp.Pool(processes=cores, initializer=_init_data, initargs=(self.dic_data, self.segments)) as pool:
            try:
                positions = pool.map(_simulate_component_worker, tasks)
            except Exception:
                logger.critical("Mega parallel backtest aborted due to fatal error in worker process.")
                pool.terminate()
                pool.join()
                raise
        return self._execute_mega(alpha_name, gen_name, base_freq, positions)

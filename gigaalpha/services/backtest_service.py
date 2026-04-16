import logging, gc
import pandas as pd 
import multiprocessing as mp
from typing import List, Dict, Any, Optional
from tqdm import tqdm

logger = logging.getLogger(__name__)

_DIC_DATA_WORKER = None
_SEGMENTS_WORKER = None

def _init_data(dic_data: Dict[str, pd.DataFrame], segments: Optional[List]):
    """Initialize data and segments for worker processes."""
    global _DIC_DATA_WORKER, _SEGMENTS_WORKER
    if _DIC_DATA_WORKER is None:
        _DIC_DATA_WORKER = dic_data
    if _SEGMENTS_WORKER is None:
        _SEGMENTS_WORKER = segments

def _single_simulation(config: Dict[str, Any], segments: Optional[List] = None):
    from gigaalpha.core.simulator import Simulator
    from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
    try:
        alpha_keys = ALPHA_REGISTRY[config['alpha_name']]['param_ranges'].keys()
        gen_keys = GEN_REGISTRY[config['gen_name']]['param_ranges'].keys()
        
        alpha_params = {k: config[k] for k in alpha_keys if k in config}
        gen_params = {k: config[k] for k in gen_keys if k in config}

        if _DIC_DATA_WORKER is None or config['frequency'] not in _DIC_DATA_WORKER:
            raise ValueError(f"Data for frequency {config['frequency']} not found in worker.")

        sim = Simulator(
            data=_DIC_DATA_WORKER[config['frequency']],
            frequency=config['frequency'],
            alpha_name=config['alpha_name'],
            alpha_params=alpha_params,
            gen_name=config['gen_name'],
            gen_params=gen_params,
            fee=config['fee']
        )
        target_segments = segments if segments is not None else _SEGMENTS_WORKER
        return sim.execute_pipeline(target_segments)
    except Exception as e:
        import traceback
        logger.error(f"Simulation failed for config: {config}\n{traceback.format_exc()}")
        return []
    
class BacktestService:
    def __init__(self, dic_data: Dict[str, pd.DataFrame], segments: Optional[List]):
        self.dic_data = dic_data
        self.segments = segments 
    
    def run_sequential(self, lst_configs: List[Dict[str, Any]]):
        global _DIC_DATA_WORKER, _SEGMENTS_WORKER
        _DIC_DATA_WORKER = self.dic_data
        _SEGMENTS_WORKER = self.segments
        
        all_results = []
        for config in tqdm(lst_configs, desc="Sequential Backtest"):
            res = _single_simulation(config, self.segments)
            if res:
                all_results.extend(res)
        return all_results
    
    def run_parallel(self, lst_configs: List[Dict[str, Any]], cores: int):
        all_results = []
        with mp.Pool(processes=cores, initializer=_init_data, initargs=(self.dic_data, self.segments)) as pool:
            for res in tqdm(pool.imap_unordered(_single_simulation, lst_configs, chunksize=10), 
                            total=len(lst_configs), desc="Parallel Backtest"):
                if res:
                    all_results.extend(res)       
        return all_results
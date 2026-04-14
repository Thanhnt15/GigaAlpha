import logging, gc
import pandas as pd     
from typing import List, Dict, Any, Optional
from functools import partial

logger = logging.getLogger(__name__)

_DIC_DATA_WORKER = None

def _init_data(dic_data: Dict[str, pd.DataFrame]):
    """Initialize data for worker processes."""
    global _DIC_DATA_WORKER
    if _DIC_DATA_WORKER is None:
        _DIC_DATA_WORKER = dic_data
    gc.collect()

def _single_simulation(config: Dict[str, Any], segments: Optional[List]):
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
        return sim.execute_pipeline(segments)
    except Exception as e:
        return [], f"{type(e).__name__}:{str(e)}"
    
class BacktestService:
    def __init__(self, dic_data: Dict[str, pd.DataFrame], segments: Optional[List]):
        self.dic_data = dic_data
        self.segments = segments 
    
    def run_sequential(self, lst_configs: List[Dict[str, Any]]):
        from tqdm import tqdm

        global _DIC_DATA_WORKER
        _DIC_DATA_WORKER = self.dic_data
        
        all_results = []
        for config in tqdm(lst_configs, desc="Sequential Backtest"):
            res = _single_simulation(config, self.segments)
            if res:
                all_results.extend(res)
        return all_results
    
    def run_parallel(self, lst_configs: List[Dict[str, Any]], cores: int):
        from tqdm import tqdm
        import multiprocessing as mp
        
        global _DIC_DATA_WORKER
        _DIC_DATA_WORKER = self.dic_data
        single_simulation_partial = partial(_single_simulation, segments=self.segments)
        all_results = []
        
        with mp.Pool(processes=cores, initializer=_init_data, initargs=(self.dic_data,)) as pool:
            for res in tqdm(pool.imap_unordered(single_simulation_partial, lst_configs, chunksize=10), 
                            total=len(lst_configs), desc="Parallel Backtest"):
                if res:
                    all_results.extend(res)       
        return all_results
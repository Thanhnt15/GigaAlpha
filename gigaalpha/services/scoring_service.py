import time
import logging
import multiprocessing as mp
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from functools import partial
from gigaalpha.utils.scoring import compute_scores

logger = logging.getLogger(__name__)

class ScoringService:
    def __init__(self, df: pd.DataFrame, num_neighbors: int, mode_test: bool = False, col_target: str = "sharpe", col_strategy: str = "strategy"):
        self.df = df
        self.num_neighbors = num_neighbors
        self.mode_test = mode_test
        self.col_target = col_target
        self.col_strategy = col_strategy

        self.strategy_norm = df[self.col_strategy].apply(self._normalize_id)
        self.sharpe_map = dict(zip(self.strategy_norm.str.strip(), df[self.col_target]))
        
        matrix = self.strategy_norm.str.strip().str.split('_', expand=True)
        params_count = matrix.shape[1]
        
        self.dim_values = {}
        self.dim_value_to_idx = {}
        for i in range(params_count):
            vals = sorted(matrix[i].unique(), key=lambda x: float(x) if x is not None else 0.0)
            self.dim_values[i] = vals
            self.dim_value_to_idx[i] = {v: idx for idx, v in enumerate(vals)}

    @staticmethod
    def _normalize_id(strategy_id: str) -> str:
        parts = str(strategy_id).split('_')
        new_parts = []
        for p in parts:
            p = p.strip()
            if p.startswith('(') and p.endswith(')'):
                inner = p[1:-1].replace(' ', '')
                new_parts.extend(inner.split(','))
            else:
                new_parts.append(p)
        return "_".join(new_parts)

    def run_sequential(self):
        time_start = time.time()
        logger.info("Running scoring sequentially")
        
        df = self.df.copy()
        df[self.col_strategy] = self.strategy_norm

        try:
            flat_results = compute_scores(
                chunk_df=df,
                sharpe_map=self.sharpe_map,
                dim_values=self.dim_values,
                dim_value_to_idx=self.dim_value_to_idx,
                num_neighbors=self.num_neighbors,
                col_target=self.col_target,
                col_strategy=self.col_strategy,
                mode_test=self.mode_test
            )
            df_results = pd.DataFrame(flat_results, index=self.df.index)
        except Exception:
            logger.exception("Scoring failed in sequential mode")
            return self.df
            
        logger.info(f"Sequential computation completed in {(time.time() - time_start) / 60:.2f} mins")
        return pd.concat([self.df, df_results], axis=1)

    def run_parallel(self, cores: int = 10):
        num_chunks = min(len(self.df), cores)
        if cores <= 1 or num_chunks <= 1:
            return self.run_sequential()

        time_start = time.time()
        
        df = self.df.copy()
        df[self.col_strategy] = self.strategy_norm
        df_chunks = [df.iloc[idx] for idx in np.array_split(np.arange(len(df)), num_chunks)]

        worker_func = partial(
            compute_scores, 
            sharpe_map=self.sharpe_map,
            dim_values=self.dim_values,
            dim_value_to_idx=self.dim_value_to_idx,
            num_neighbors=self.num_neighbors,
            col_target=self.col_target,
            col_strategy=self.col_strategy,
            mode_test=self.mode_test
        )

        try:
            with mp.Pool(processes=cores) as pool:
                chunks_results = pool.map(worker_func, df_chunks)

            flat_results = [item for sublist in chunks_results for item in sublist]
            df_results = pd.DataFrame(flat_results, index=self.df.index)
        except Exception:
            logger.exception("Scoring failed in parallel mode")
            return self.df
        
        logger.info(f"Parallel computation completed in {(time.time() - time_start) / 60:.2f} mins")
        return pd.concat([self.df, df_results], axis=1)

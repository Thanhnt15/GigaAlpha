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

        # Chuẩn bị dữ liệu phục vụ tính toán
        self.sharpe_map = dict(zip(df[self.col_strategy].str.strip(), df[self.col_target]))
        strategy_matrix = df[self.col_strategy].str.strip().str.split('_', expand=True)
        params_count = strategy_matrix.shape[1]
        
        self.dim_values = {}
        self.dim_value_to_idx = {}
        for i in range(params_count):
            vals = sorted(strategy_matrix[i].unique(), key=lambda x: float(x))
            self.dim_values[i] = vals
            self.dim_value_to_idx[i] = {v: idx for idx, v in enumerate(vals)}

    def run_sequential(self):
        time_start = time.time()
        logger.info("Running ScoringService sequentially...")
        
        flat_results = compute_scores(
            chunk_df=self.df,
            sharpe_map=self.sharpe_map,
            dim_values=self.dim_values,
            dim_value_to_idx=self.dim_value_to_idx,
            num_neighbors=self.num_neighbors,
            col_target=self.col_target,
            col_strategy=self.col_strategy,
            mode_test=self.mode_test
        )
        df_results = pd.DataFrame(flat_results, index=self.df.index)
        
        elapsed = (time.time() - time_start) / 60
        logger.info(f"Sequential score computation completed in {elapsed:.2f} mins")
        return pd.concat([self.df, df_results], axis=1)

    def run_parallel(self, cores: int = 10):
        num_chunks = min(len(self.df), cores)
        if cores <= 1 or num_chunks <= 1:
            return self.run_sequential()

        time_start = time.time()
        df_chunks = [self.df.iloc[idx] for idx in np.array_split(np.arange(len(self.df)), num_chunks)]

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

        with mp.Pool(processes=cores) as pool:
            chunks_results = pool.map(worker_func, df_chunks)

        flat_results = [item for sublist in chunks_results for item in sublist]
        df_results = pd.DataFrame(flat_results, index=self.df.index)
        
        elapsed = (time.time() - time_start) / 60
        logger.info(f"Parallel score with {cores} cores computation completed in {elapsed:.2f} mins")
        
        return pd.concat([self.df, df_results], axis=1)

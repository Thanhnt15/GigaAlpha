import multiprocessing as mp
import pandas as pd
import logging, os
from pathlib import Path

from gigaalpha.services.backtest import BacktestService
from gigaalpha.services.compute_score import ScoringService
from gigaalpha.services.statistic import StatisticsService
from gigaalpha.services.visualization import VisualizationService
from gigaalpha.services.storage import StorageService
from gigaalpha.core.scanner import ScanParams
from gigaalpha.utils.config import PipelineConfig

PROJECT_ROOT = Path(__file__).parents[2]
logger = logging.getLogger(__name__)

def _visualize_and_storage_worker(task):
    """Worker handles visualization and storage for a single segment."""
    segment, seg_df, config = task
    try:
        if config.visualize.enabled:
            visualizer = VisualizationService(df=seg_df)
            z = 'sharpe'
            x = sorted([col for col in seg_df.columns if 'alpha_' in col and col != 'alpha_name'])[0]
            y = sorted([col for col in seg_df.columns if 'gen_' in col and col != 'gen_name'])[0]

            target_cols = [z, x, y]
            output_path_html = Path(config.visualize.output_dir) / f"3D_{config.backtest.alpha_name}_{config.backtest.gen_name}_{segment}.html"
            visualizer.run_visualization(
                title=f"Sharpe_3D: Alpha_{config.backtest.alpha_name} | Gen_{config.backtest.gen_name} | {segment}", 
                target_cols=target_cols, 
                colors=config.visualize.chart_colors, 
                output_path=output_path_html
            )
        if config.storage.enabled:
            output_path_excel = Path(config.storage.output_dir) / f"alpha_{config.backtest.alpha_name}_{config.backtest.gen_name}_{segment}.xlsx"
            storage = StorageService(df=seg_df, output_path=output_path_excel)
            storage.save_to_xlsx()

    except Exception as e:
        logger.error(f"Error: {e}")
        return None

def _upload_worker(task):
    """Worker handles uploading a single generated file to Drive."""
    local_path, config = task
    try:
        if config.upload.enabled:
            from gigaalpha.services.upload import UploadService
            uploader = UploadService(
                local_path=str(local_path),
                token_path=os.getenv('GDRIVE_TOKEN_PATH'),
                target_folder_id=config.upload.target_folder_id
            )
            link = uploader.upload_to_drive()
            return (Path(local_path).name, link)
    except Exception as e:
        logger.error(f"Upload Error for {local_path}: {e}")
    return (None, None)

class ScanPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results_df = pd.DataFrame()

    def run_backtest_and_statistics(self):
        backtester = BacktestService(dic_data=pd.read_pickle(PROJECT_ROOT / self.config.data.path), segments=self.config.data.segments)
        lst_configs = ScanParams.gen_all_params(
            alpha_name = self.config.backtest.alpha_name,
            gen_name = self.config.backtest.gen_name,
            lst_bar_size = self.config.backtest.lst_bar_size,
            lst_fee = self.config.backtest.lst_fee,
        )
        
        logger.info(f"Running parallel backtest with {self.config.backtest.cores} cores")
        logger.info(f'Alpha: {self.config.backtest.alpha_name} | Gen: {self.config.backtest.gen_name} | Total configs: {len(lst_configs)}')
        self.results_df = pd.DataFrame(backtester.run_parallel(lst_configs, cores=self.config.backtest.cores))
        
        if self.results_df.empty:
            logger.error("No results generated.")
            return

        logger.info("Compute sharpe score and statistics") if self.config.compute_score.enabled else logger.info("Compute statistics")
        score_results = []
        stats_results = []
        for segment in self.results_df['segment'].unique():
            seg_df = self.results_df[self.results_df['segment'] == segment].copy()
            if self.config.compute_score.enabled:
                scorer = ScoringService(df=seg_df, num_neighbors=self.config.compute_score.num_neighbors)
                seg_df = scorer.run_parallel(cores=self.config.compute_score.cores)
        
            score_results.append(seg_df)
            stats_service = StatisticsService(df=seg_df)
            res = stats_service.run_statistics(segment)
            stats_results.append(res)
        logger.info("\n" + pd.DataFrame(stats_results).to_string(index=False))
        if score_results:
            self.results_df = pd.concat(score_results, ignore_index=True)
        logger.info("Backtest and statistics completed.\n")

    def run_visualization_and_storage(self):
        if self.results_df.empty:
            return
            
        if self.config.visualize.enabled or self.config.storage.enabled:
            logger.info("Generating professional reports and visualizations in parallel...")
            tasks = []
            for segment in self.results_df['segment'].unique():
                seg_df = self.results_df[self.results_df['segment'] == segment].copy()
                tasks.append((segment, seg_df, self.config))
            
            num_cores = self.config.visualize.cores
            with mp.Pool(processes=min(len(tasks), num_cores)) as pool:
                pool.map(_visualize_and_storage_worker, tasks)
                    
            logger.info("Visualization and storage completed.\n")

    def run_upload_to_drive(self):
        if self.config.upload.enabled:
            logger.info("Uploading reports to Google Drive in parallel...")
            target_dir = Path(self.config.storage.output_dir)
            if not target_dir.exists():
                logger.warning(f"Upload directory not found: {target_dir}")
                return
                
            excel_files = []
            for segment in self.results_df['segment'].unique():
                fpath = target_dir / f"alpha_{self.config.backtest.alpha_name}_{self.config.backtest.gen_name}_{segment}.xlsx"
                if fpath.exists():
                    excel_files.append(fpath)
                    
            if not excel_files:
                logger.info("No newly generated files found to upload.")
                return
                
            tasks = [(f, self.config) for f in excel_files]

            num_cores = self.config.upload.cores
            with mp.Pool(processes=min(len(tasks), num_cores)) as pool:
                results = pool.map(_upload_worker, tasks)
            
            
            seg_strs = [f"{s[0]}_{s[1]}" for s in self.config.data.segments]
            def get_order(name):
                return next((i for i, s in enumerate(seg_strs) if s in str(name)), 999)
            new_links = {n: l for n, l in sorted(results, key=lambda x: get_order(x[0])) if n and l}
        
            if new_links:
                from gigaalpha.utils.track_link import LinkTracker
                json_path = Path(self.config.log_link.sheet_path)
                LinkTracker.update_drive_json(str(json_path), new_links)
                    
            logger.info("Uploading completed.\n")

    

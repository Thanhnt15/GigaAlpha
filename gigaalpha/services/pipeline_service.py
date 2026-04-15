import multiprocessing as mp
import pandas as pd
import logging, os
from pathlib import Path

from gigaalpha.services.backtest_service import BacktestService
from gigaalpha.services.scoring_service import ScoringService
from gigaalpha.services.statistics_service import StatisticsService
from gigaalpha.services.visualization_service import VisualizationService
from gigaalpha.services.storage_service import StorageService
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
            # Use absolute path relative to PROJECT_ROOT
            output_dir = PROJECT_ROOT / config.visualize.output_dir
            output_path_html = output_dir / f"3D_{config.backtest.alpha_name}_{config.backtest.gen_name}_{segment}.html"
            visualizer.run_visualization(
                title=f"Sharpe_3D: Alpha_{config.backtest.alpha_name} | Gen_{config.backtest.gen_name} | {segment}", 
                target_cols=target_cols, 
                colors=config.visualize.chart_colors, 
                output_path=output_path_html
            )
        if config.storage.enabled:
            # Use absolute path relative to PROJECT_ROOT
            output_dir = PROJECT_ROOT / config.storage.output_dir
            output_path_excel = output_dir / f"alpha_{config.backtest.alpha_name}_{config.backtest.gen_name}_{segment}.xlsx"
            storage = StorageService(df=seg_df, output_path=output_path_excel)
            storage.save_to_xlsx()

    except Exception as e:
        import traceback
        logger.error(f"Visualization/Storage failed for segment {segment}:\n{traceback.format_exc()}")
        return None

def _upload_worker(task):
    """Worker handles uploading a single generated file to Drive."""
    local_path, config = task
    try:
        if config.upload.enabled:
            from gigaalpha.services.upload_service import UploadService
            uploader = UploadService(
                local_path=str(local_path),
                token_path=os.getenv('GDRIVE_TOKEN_PATH'),
                target_folder_id=config.upload.target_folder_id
            )
            link = uploader.upload_to_drive()
            return (Path(local_path).name, link)
    except Exception as e:
        import traceback
        logger.error(f"Upload failed for {local_path}:\n{traceback.format_exc()}")
    return (None, None)

class ScanPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results_df = pd.DataFrame()

    def run_backtest(self):
        """Generate configurations and run the core backtesting simulator in parallel."""
        logger.info(f"--- CORE BACKTEST ---")
        backtester = BacktestService(dic_data=pd.read_pickle(PROJECT_ROOT / self.config.data.path), segments=self.config.data.segments)
        lst_configs = ScanParams.gen_all_params(
            alpha_name = self.config.backtest.alpha_name,
            gen_name = self.config.backtest.gen_name,
            lst_frequency = self.config.backtest.lst_frequency,
            lst_fee = self.config.backtest.lst_fee,
        )
        
        logger.info(f"Running parallel backtest with {self.config.backtest.cores} cores")
        logger.info(f'Alpha: {self.config.backtest.alpha_name} | Gen: {self.config.backtest.gen_name} | Total configs: {len(lst_configs)}')
        
        self.results_df = pd.DataFrame(backtester.run_parallel(lst_configs, cores=self.config.backtest.cores))
        
        if self.results_df.empty:
            logger.error("No results generated.")
            return
        logger.info("Backtest completed successfully.\n")

    def run_scoring(self):
        """Calculate K-Neighbors Sharpe scores (if enabled)."""
        if self.results_df.empty or not self.config.compute_score.enabled:
            return
            
        logger.info(f"--- COMPUTE SCORING ---")
        logger.info("Computing K-Neighbors Sharpe score in parallel...")
        
        score_results = []
        for segment in self.results_df['segment'].unique():
            seg_df = self.results_df[self.results_df['segment'] == segment].copy()
            scorer = ScoringService(df=seg_df, num_neighbors=self.config.compute_score.num_neighbors)
            scored_df = scorer.run_parallel(cores=self.config.compute_score.cores)
            score_results.append(scored_df)
            
        if score_results:
            self.results_df = pd.concat(score_results, ignore_index=True)
            
        logger.info("Scoring completed.\n")

    def run_statistics(self):
        """Aggregate performance statistics."""
        if self.results_df.empty:
            return
        
        logger.info(f"--- STATISTICS SUMMARY ---")
        logger.info("Computing basic statistics...")
            
        stats_results = []
        
        for segment in self.results_df['segment'].unique():
            seg_df = self.results_df[self.results_df['segment'] == segment]
            stats_service = StatisticsService(df=seg_df)
            res = stats_service.run_statistics(segment)
            stats_results.append(res)
            
        logger.info("\nStatistics Summary:\n" + pd.DataFrame(stats_results).to_string(index=False))
        logger.info("Statistics completed.\n")

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
        """Upload Excel reports to Google Drive in parallel."""
        if self.config.upload.enabled:
            logger.info("Uploading reports to Google Drive in parallel...")
            # Use absolute path relative to PROJECT_ROOT
            target_dir = PROJECT_ROOT / self.config.storage.output_dir
            if not target_dir.exists():
                logger.warning(f"Upload directory not found: {target_dir}")
                return
            
            excel_files = []
            for segment in self.results_df['segment'].unique():
                fpath = target_dir / f"alpha_{self.config.backtest.alpha_name}_{self.config.backtest.gen_name}_{segment}.xlsx"
                if fpath.exists():
                    excel_files.append(str(fpath))

            if not excel_files:
                logger.info("No newly generated Excel files found to upload.")
                return

            tasks = [(f, self.config) for f in excel_files]
            
            # Use Pool for parallel uploads
            num_cores = min(len(tasks), self.config.upload.cores)
            with mp.Pool(processes=num_cores) as pool:
                results = pool.map(_upload_worker, tasks)
            
            # Collect successful links
            new_urls = {}
            for fname, link_dict in results:
                if fname and link_dict:
                    new_urls.update(link_dict)
            
            if new_urls:
                from gigaalpha.utils.track_link import update_drive_link_json
                update_drive_link_json(str(self.config.log_link.sheet_path), new_urls)
                    
            logger.info("Uploading completed.\n")

    

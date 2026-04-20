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
from gigaalpha.helpers.timer import Timer

PROJECT_ROOT = Path(__file__).parents[2]
logger = logging.getLogger(__name__)

def load_dic_data(config: PipelineConfig):
    dic_data_path = PROJECT_ROOT / config.data.path
    logger.info(f"Loading data from {dic_data_path}")
    return pd.read_pickle(dic_data_path)

def _visualize_and_storage_worker(task):
    segment, seg_df, config = task
    try:
        if config.visualize.enabled:
            visualizer = VisualizationService(df=seg_df)
            z = 'sharpe'
            x = next((col for col in sorted(seg_df.columns) if 'alpha_' in col and col != 'alpha_name'), 'frequency')
            y = next(col for col in sorted(seg_df.columns) if 'gen_' in col and col != 'gen_name')

            target_cols = [z, x, y]
            data_tag = config.data.name
            output_dir = PROJECT_ROOT / config.visualize.output_dir
            output_path_html = output_dir / f"3D_{config.backtest.alpha_name}_{config.backtest.gen_name}_{segment}{data_tag}.html"
            visualizer.run_visualization(
                title=f"3D: {config.backtest.alpha_name} | {config.backtest.gen_name} | {segment} | {data_tag}", 
                target_cols=target_cols, 
                colors=config.visualize.chart_colors, 
                output_path=output_path_html
            )
        if config.storage.enabled:
            data_tag = config.data.name
            output_dir = PROJECT_ROOT / config.storage.output_dir
            output_path_excel = output_dir / f"{config.backtest.alpha_name}_{config.backtest.gen_name}_{segment}{data_tag}.xlsx"
            storage = StorageService(df=seg_df, output_path=output_path_excel)
            
            summary_df = None
            if config.storage.custom_stats_enabled:
                stats_service = StatisticsService(df=seg_df)
                summary_dict = stats_service.run_custom_statistics(segment, lst_n_profit=[100, 120, 150, 180, 210, 240, 270, 300, 450, 600, 1200])
                summary_df = pd.DataFrame([summary_dict]) if summary_dict else None
            
            storage.save_to_xlsx(summary_df=summary_df)

    except Exception:
        logger.exception(f"Visualization/Storage failed for segment {segment}")
        return None

def _upload_worker(task):
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
    except Exception:
        logger.exception(f"Upload failed for {local_path}")
    return (None, None)

class ScanPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results_df = pd.DataFrame()

    @Timer("Core Backtest")
    def run_backtest(self):
        logger.info("="*80)
        logger.info(f"Core backtest")
        dic_data_path = PROJECT_ROOT / self.config.data.path
        logger.info(f"Loading data from {dic_data_path}")

        backtester = BacktestService(dic_data=pd.read_pickle(dic_data_path), segments=self.config.data.segments)
        lst_configs = ScanParams.gen_all_params(
            alpha_name = self.config.backtest.alpha_name,
            gen_name = self.config.backtest.gen_name,
            lst_frequency = self.config.backtest.lst_frequency,
            lst_fee = self.config.backtest.lst_fee,
        )
        logger.info(f"Running parallel backtest with {self.config.backtest.cores} cores...")
        logger.info(f'Alpha: {self.config.backtest.alpha_name} | Gen: {self.config.backtest.gen_name} | Total configs: {len(lst_configs)}')
        
        self.results_df = pd.DataFrame(backtester.run_parallel(lst_configs, cores=self.config.backtest.cores))
        if self.results_df.empty:
            msg = "No backtest results generated. Stopping pipeline."
            logger.error(msg)
            raise RuntimeError(msg)

    @Timer("Scoring Computation")
    def run_scoring(self):
        if self.results_df.empty or not self.config.compute_score.enabled:
            return
        logger.info("="*80)
        logger.info(f"Compute scoring")
        logger.info(f"Computing K-Neighbors Sharpe score in parallel with {self.config.compute_score.cores} cores...")
        
        score_results = []
        for segment in self.results_df['segment'].unique():
            seg_df = self.results_df[self.results_df['segment'] == segment].copy()
            scorer = ScoringService(df=seg_df, num_neighbors=self.config.compute_score.num_neighbors)
            scored_df = scorer.run_parallel(cores=self.config.compute_score.cores)
            score_results.append(scored_df)
            
        if score_results:
            self.results_df = pd.concat(score_results, ignore_index=True)

    @Timer("Statistics Summary")
    def run_statistics(self):
        if self.results_df.empty:
            return
        logger.info("="*80)
        logger.info(f"Statistics summary")
        logger.info("Computing basic statistics...")
            
        stats_results = []
        for segment in self.results_df['segment'].unique():
            seg_df = self.results_df[self.results_df['segment'] == segment]
            stats_service = StatisticsService(df=seg_df)
            res = stats_service.run_statistics(segment)
            stats_results.append(res)
            
        logger.info("Statistics Summary:\n" + pd.DataFrame(stats_results).to_string(index=False))

    @Timer("Visualization and storage")
    def run_visualization_and_storage(self):
        if self.results_df.empty:
            return
            
        if self.config.visualize.enabled or self.config.storage.enabled:
            actions = []
            if self.config.storage.enabled: actions.append("reports")
            if self.config.visualize.enabled: actions.append("visualizations")
            
            num_cores = max(self.config.visualize.cores, self.config.storage.cores)
            logger.info("="*80)
            logger.info(f"Generating professional {' and '.join(actions)} in parallel with {num_cores} cores...")
            tasks = []
            for segment in self.results_df['segment'].unique():
                seg_df = self.results_df[self.results_df['segment'] == segment].copy()
                tasks.append((segment, seg_df, self.config))
            
            with mp.Pool(processes=min(len(tasks), num_cores)) as pool:
                pool.map(_visualize_and_storage_worker, tasks)

    @Timer("Upload to drive")
    def run_upload_to_drive(self):
        if self.config.upload.enabled:      
            logger.info("="*80)
            logger.info(f"Uploading reports to Google Drive in parallel with {self.config.upload.cores} cores...")
            target_dir = PROJECT_ROOT / self.config.storage.output_dir
            if not target_dir.exists():
                logger.warning(f"Upload directory not found: {target_dir}")
                return
            
            excel_files = []
            data_tag = self.config.data.name
            for segment in self.results_df['segment'].unique():
                fpath = target_dir / f"{self.config.backtest.alpha_name}_{self.config.backtest.gen_name}_{segment}{data_tag}.xlsx"
                if fpath.exists():
                    excel_files.append(str(fpath))

            if not excel_files:
                logger.info("No newly generated Excel files found to upload.")
                return

            tasks = [(f, self.config) for f in excel_files]
            with mp.Pool(processes=self.config.upload.cores) as pool:
                results = pool.map(_upload_worker, tasks)
            
            new_urls, success_count = {}, 0
            for fname, link_dict in results:
                if fname and link_dict:
                    success_count += 1
                    new_urls.update(link_dict)
            
            if new_urls:
                from gigaalpha.utils.track_link import update_drive_link_json
                update_drive_link_json(str(self.config.log_link.sheet_path), new_urls)
            
            return success_count, len(tasks)
        return 0, 0

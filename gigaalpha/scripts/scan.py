import sys, argparse, logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT))

from gigaalpha.utils.config import PipelineConfig
from gigaalpha.utils.logger import setup_logging
from gigaalpha.services.pipeline_service import ScanPipeline
from gigaalpha.services.notification_service import NotificationService
from gigaalpha.helpers.timer import Timer
import gigaalpha.strategies

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="GigaAlpha Scan Pipeline")
    parser.add_argument('--config', default='configs/default.yaml', help='Path to YAML config file (default: configs/default.yaml)')
    args = parser.parse_args()

    pipeline_config = PipelineConfig.load(str(args.config))
    
    setup_logging(enable_file_logging=pipeline_config.system_log.enabled)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Running Scan Pipeline with config: {args.config}")
    pipeline = ScanPipeline(pipeline_config)
    try:
        total_time_str = "N/A"
        success_count, total_count = 0, 0
        
        with Timer("Total execution") as t:
            pipeline.run_backtest()
            
            if pipeline_config.compute_score.enabled:
                pipeline.run_scoring()
            
            pipeline.run_statistics()
            
            if pipeline_config.visualize.enabled or pipeline_config.storage.enabled:
                pipeline.run_visualization_and_storage()
            
            if pipeline_config.upload.enabled:
                success_count, total_count = pipeline.run_upload_to_drive()
            
        total_time_str = f"{t.duration:.2f}m"

        if pipeline_config.notification.enabled:
            notifier = NotificationService()
            notifier.notify_success(
                config=pipeline_config,
                results_df=pipeline.results_df,
                total_time=total_time_str,
                success_count=success_count,
            total_count=total_count
        )   

    except Exception:
        logger.exception("Pipeline execution failed")
        raise

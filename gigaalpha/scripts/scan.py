import sys, argparse, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT))

from gigaalpha.utils.config import PipelineConfig
from gigaalpha.utils.logger import setup_logging
from gigaalpha.services.pipeline_service import ScanPipeline
import gigaalpha.strategies

if __name__ == '__main__':
    setup_logging()
    import logging
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="GigaAlpha Scan Pipeline")
    parser.add_argument('--config', default='configs/default.yaml', help='Path to YAML config file (default: configs/default.yaml)')
    args = parser.parse_args()

    pipeline_config = PipelineConfig.load(str(args.config))
    
    from gigaalpha.helpers.timer import Timer

    logger.info(f"Running Scan Pipeline with config: {args.config}")
    pipeline = ScanPipeline(pipeline_config)

    with Timer("Total execution"):
        with Timer("Backtest and statistics"):
            pipeline.run_backtest_and_statistics()
        
        if pipeline_config.visualize.enabled or pipeline_config.storage.enabled:
            with Timer("Visualization and storage"):
                pipeline.run_visualization_and_storage()
        
        if pipeline_config.upload.enabled:
            with Timer("Upload to drive"):
                pipeline.run_upload_to_drive()

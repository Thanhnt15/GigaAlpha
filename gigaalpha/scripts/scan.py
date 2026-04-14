import sys, argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT))

from gigaalpha.utils.config import PipelineConfig
from gigaalpha.utils.logger import setup_logging
from gigaalpha.services.pipeline import ScanPipeline
import gigaalpha.strategies

if __name__ == '__main__':
    setup_logging()
    import logging
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="GigaAlpha Scan Pipeline")
    parser.add_argument('--config', default='configs/default.yaml', help='Path to YAML config file (default: configs/default.yaml)')
    args = parser.parse_args()

    # Determine config path
    config_path = Path(args.config)
    
    # Check if absolute or relative to root
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    pipeline_config = PipelineConfig.load(str(config_path))
    
    logger.info(f"Running Scan Pipeline with config: {config_path.name}")

    pipeline = ScanPipeline(pipeline_config)
    pipeline.run_backtest_and_statistics()
    
    if pipeline_config.visualize.enabled or pipeline_config.storage.enabled:
        pipeline.run_visualization_and_storage()
        
    if pipeline_config.upload.enabled:
        pipeline.run_upload_to_drive()

    if pipeline_config.deploy.enabled:
        pipeline.run_deploy_to_github()

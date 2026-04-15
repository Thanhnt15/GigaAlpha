import yaml, os, sys, logging
from dataclasses import dataclass, field, fields
from typing import List, Dict, Any, Type, Optional
from pathlib import Path
from dotenv import load_dotenv


# Auto-load environment variables from .env
load_dotenv()

from gigaalpha.constants.trading import SEGMENTS

logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    path: str = ""
    segments: List[List[str]] = field(default_factory=list)

@dataclass
class BacktestConfig:
    alpha_name: str = ""
    gen_name: str = ""
    lst_frequency: List[float] = field(default_factory=lambda: list(range(10,101,1)))
    lst_fee: List[float] = field(default_factory=list)
    cores: int = 1

@dataclass
class ComputeScoreConfig:
    enabled: bool = True
    num_neighbors: int = 4
    col_strategy: str = "strategy"
    col_target: str = "sharpe"
    mode_test: bool = False
    cores: int = 1


@dataclass
class VisualizeConfig:
    enabled: bool = True
    output_dir: str = "outputs/html" 
    chart_colors: List[str] = field(default_factory=lambda: ['#081d58', '#225ea8', '#41b6c4', '#7ed957', '#edf8b1'])
    cores: int = 8


@dataclass
class StorageConfig:
    enabled: bool = True
    output_dir: str = "outputs/excel"


@dataclass
class UploadConfig:
    enabled: bool = False
    target_folder_id: str = ""
    cores: int = 10

@dataclass
class LogLinkConfig:
    sheet_path: str = "logs/drive_links.json"
    
@dataclass
class NotificationConfig:
    enabled: bool = False

@dataclass
class PipelineConfig:
    data: DataConfig = field(default_factory=DataConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    compute_score: ComputeScoreConfig = field(default_factory=ComputeScoreConfig)
    visualize: VisualizeConfig = field(default_factory=VisualizeConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)
    log_link: LogLinkConfig = field(default_factory=LogLinkConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)

    @staticmethod
    def _map(cls: Type, data: Dict) -> Any:
        """Recursively maps dict to dataclass while ignoring extra keys."""
        if not isinstance(data, dict): return data
        v_fields = {f.name for f in fields(cls)}
        cleaned = {}
        for k, v in data.items():
            if k in v_fields:
                f_type = next(f.type for f in fields(cls) if f.name == k)
                cleaned[k] = PipelineConfig._map(f_type, v) if hasattr(f_type, "__dataclass_fields__") else v
        return cls(**cleaned)

    @classmethod
    def load(cls, config_path: str) -> 'PipelineConfig':
        """Load YAML and map to dataclasses hierarchy with environment variables support."""
        fp = Path(config_path)
        if not fp.exists():
            logger.error(f"Config not found: {fp}"); sys.exit(1)
            
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f) or {}
                config = cls._map(cls, raw_data)

                if not config.data.segments:
                    logger.info("No segments found in YAML. Falling back to trading.SEGMENTS defaults.")
                    config.data.segments = SEGMENTS    
                return config
        except Exception as e:
            logger.error(f"Load error {fp}: {e}"); sys.exit(1)

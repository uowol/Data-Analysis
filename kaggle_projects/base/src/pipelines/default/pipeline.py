import os
import yaml
from pathlib import Path
from typing import Optional

from base.src.pipelines import base
from base.src.components import (
    DownloadDataComponent,
    ExtractDataComponent,
)
from base.src.formats import (
    RequestDownloadData, ResponseDownloadData,
    RequestExtractInfo, ResponseExtractInfo,
)
from base.src.functions import get_logger


logger = get_logger()


class PipelineType(base.PipelineType):
    download_data: Optional[RequestDownloadData] = None
    extract_data: Optional[RequestExtractInfo] = None


class Pipeline(base.Pipeline):
    def init(self, **config):
        if config:
            self.config = PipelineType(**config)
        else:
            with open(os.path.join(Path(__file__).parent, "pipeline.yaml"), "r") as fp:
                self.config = yaml.safe_load(fp)
                self.config = self.config if self.config is not None else {}
        
    def call(self):
        upstream_events = []
        
        # -- run components
        logger.info("Pipeline started with config: %s", self.config)
        if self.config.download_data is not None:            
            logger.info("=== download_data start ===")
            component = DownloadDataComponent()
            request_message = self.config.download_data
            response_message = component(request_message, logger=logger)
            upstream_events.append(response_message)
            logger.info("=== download_data end ===")
        if self.config.extract_data is not None:
            logger.info("=== extract_data start ===")
            component = ExtractDataComponent()
            request_message = self.config.extract_data
            response_message = component(request_message, upstream_events=upstream_events, logger=logger)
            upstream_events.append(response_message)
            logger.info("=== extract_data end ===")
        logger.info("Pipeline finished with events: %s", upstream_events)

        return
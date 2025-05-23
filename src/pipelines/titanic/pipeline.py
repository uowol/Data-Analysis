from typing import Optional

from src.pipelines import base
from src.formats import (
    RequestDownloadData, ResponseDownloadData,
    RequestExtractInfo, ResponseExtractInfo,
    RequestPreprocessData, ResponsePreprocessData,
    RequestTestOutput, ResponseTestOutput,
    RequestModeling, ResponseModeling,
)

class PipelineType(base.PipelineType):
    download_data: Optional[RequestDownloadData] = None
    extract_data: Optional[RequestExtractInfo] = None
    preprocess_data: Optional[RequestPreprocessData] = None
    modeling: Optional[RequestModeling] = None
    test_output: Optional[RequestTestOutput] = None

class Pipeline(base.Pipeline):
    def init(self, **config):
        self.config = PipelineType(**config)
        
    def call(self):
        upstream_events = []
        if self.config.download_data is not None:
            from src.components.download_data.component import Component as DownloadDataComponent
            
            print("# [INFO] =============== download_data start ===============")
            component = DownloadDataComponent()
            request_message = self.config.download_data
            response_message = component(request_message)
            upstream_events.append(response_message)
            print("# [INFO] =============== download_data end ===============\n")
        if self.config.extract_data is not None:
            from src.components.extract_data_info.component import Component as ExtractDataComponent
            
            print("# [INFO] =============== extract_data start ===============")
            component = ExtractDataComponent()
            request_message = self.config.extract_data
            response_message = component(request_message, upstream_events=upstream_events)
            upstream_events.append(response_message)
            print("# [INFO] =============== extract_data end ===============\n")
        if self.config.preprocess_data is not None:
            from src.components.preprocess_data.component import Component as PreprocessDataComponent
            
            print("# [INFO] =============== preprocess_data start ===============")
            component = PreprocessDataComponent()
            request_message = self.config.preprocess_data
            response_message = component(request_message, upstream_events=upstream_events)
            upstream_events.append(response_message)
            print("# [INFO] =============== preprocess_data end ===============\n")
        if self.config.modeling is not None:
            from src.components.modeling.component import Component as ModelingComponent
            
            print("# [INFO] =============== modeling start ===============")
            component = ModelingComponent()
            request_message = self.config.modeling
            response_message = component(request_message, upstream_events=upstream_events)
            upstream_events.append(response_message)
            print("# [INFO] =============== modeling end ===============\n")
        if self.config.test_output is not None:
            from src.components.test_output.component import Component as TestOutputComponent
            
            print("# [INFO] =============== test_output start ===============")
            component = TestOutputComponent()
            request_message = self.config.test_output
            response_message = component(request_message, upstream_events=upstream_events)
            upstream_events.append(response_message)
            print("# [INFO] =============== test_output end ===============\n")

        return
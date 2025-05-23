from pydantic import BaseModel
from typing import List, Dict, Union, Optional


class RequestMessage(BaseModel):
    pass

class ResponseMessage(BaseModel):
    status: str

class RequestDownloadData(RequestMessage):
    url: str
    local_path: str
    is_competition: bool = False

class ResponseDownloadData(ResponseMessage, RequestDownloadData):
    pass 
    
class RequestExtractInfo(RequestMessage):
    local_path: str
    output_path: str
    
class ResponseExtractInfo(ResponseMessage, RequestExtractInfo):
    pass
    
class RequestPreprocessData(RequestMessage):
    local_path: str
    output_path: str
    target_columns: Optional[List[str]] = None
    outlier: Optional[List[Dict[str, Union[str, int, list]]]] = None
    missing: Optional[List[Dict[str, Union[str, int, list]]]] = None

class ResponsePreprocessData(ResponseMessage, RequestPreprocessData):
    pass
    
class RequestTestOutput(RequestMessage):
    output_filepath: str
    reference_filepath: str

class ResponseTestOutput(ResponseMessage, RequestTestOutput):
    pass
    
class RequestModeling(RequestMessage):
    train_filepath: str
    test_filepath: str
    output_filepath: str
    model_type: str

class ResponseModeling(ResponseMessage, RequestModeling):
    pass
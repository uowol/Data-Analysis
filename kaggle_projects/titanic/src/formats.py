from pydantic import BaseModel
from typing import List, Dict, Union, Optional

from base.src.formats import RequestMessage, ResponseMessage


class RequestModeling(RequestMessage):
    train_filepath: str
    test_filepath: str
    output_filepath: str
    model_type: str

class ResponseModeling(ResponseMessage, RequestModeling):
    pass

class RequestTestOutput(RequestMessage):
    output_filepath: str
    reference_filepath: str

class ResponseTestOutput(ResponseMessage, RequestTestOutput):
    pass
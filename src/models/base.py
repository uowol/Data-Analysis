import os
import time
import pandas as pd
from pathlib import Path
from src.formats import (
    RequestModeling, ResponseModeling
)


def predict(message: RequestModeling, params: dict = None) -> ResponseModeling:
    os.makedirs(Path(message.output_filepath).parent, exist_ok=True)
    assert os.path.exists(message.train_filepath), f"Train file {message.train_filepath} does not exist"
    assert os.path.exists(message.test_filepath), f"Test file {message.test_filepath} does not exist"
    
    # TBD
    
    return ResponseModeling(
        status="success",
        **message.model_dump()
    )
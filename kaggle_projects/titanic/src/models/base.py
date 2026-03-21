import os
from pathlib import Path

from titanic.src.formats import (
    RequestModeling, ResponseModeling
)


def predict(message: RequestModeling) -> ResponseModeling:
    base_dir = Path('./')
    output_filepath = base_dir / message.output_filepath
    train_filepath = base_dir / message.train_filepath
    test_filepath = base_dir / message.test_filepath
    
    os.makedirs(output_filepath.parent, exist_ok=True)
    assert os.path.exists(train_filepath), f"Train file {train_filepath} does not exist"
    assert os.path.exists(test_filepath), f"Test file {test_filepath} does not exist"
    
    # TBD
    
    return ResponseModeling(
        status="success",
        **message.model_dump()
    )
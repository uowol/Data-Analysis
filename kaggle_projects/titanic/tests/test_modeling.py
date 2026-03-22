import os
from pathlib import Path

from titanic.src.components import (
    ModelingComponent,
)
from titanic.src.formats import (
    RequestModeling, ResponseModeling,
)


def test_download_data():
    # -- test component
    component = ModelingComponent()
    request_message = RequestModeling(
        train_filepath="data/titanic/raw/train.csv",
        test_filepath="data/titanic/raw/test.csv",
        output_filepath="data/titanic/raw/submission.csv",
        model_type="logistic_regression",
    )
    response_message = component(request_message)
    assert isinstance(response_message, ResponseModeling)
    assert response_message.status == "success"

    # -- test output
    base_dir = Path('./')
    output_filepath = base_dir / request_message.output_filepath
    assert os.path.exists(output_filepath)
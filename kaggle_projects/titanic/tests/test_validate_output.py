import os
from pathlib import Path

from titanic.src.components import (
    TestOutputComponent,
)
from titanic.src.formats import (
    RequestTestOutput, ResponseTestOutput,
)


def test_download_data():
    # -- test component
    component = TestOutputComponent()
    request_message = RequestTestOutput(
        output_filepath="data/titanic/raw/submission.csv",
        reference_filepath="data/titanic/raw/gender_submission.csv",
    )
    response_message = component(request_message)
    assert isinstance(response_message, ResponseTestOutput)
    assert response_message.status == "success"

    # -- test output
    base_dir = Path('./')
    output_filepath = base_dir / request_message.output_filepath
    assert os.path.exists(output_filepath)
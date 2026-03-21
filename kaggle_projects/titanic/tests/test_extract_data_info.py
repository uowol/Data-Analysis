import os
from pathlib import Path

from base.src.components import (
    ExtractDataComponent,
)
from base.src.formats import (
    RequestExtractInfo, ResponseExtractInfo,
)


def test_download_data():
    # -- test component
    component = ExtractDataComponent()
    request_message = RequestExtractInfo(
        local_path="data/titanic/raw",
        output_path="data/titanic/info",
    )
    response_message = component(request_message)
    assert isinstance(response_message, ResponseExtractInfo)
    assert response_message.status == "success"

    # -- test output
    base_dir = Path('./')
    output_path = base_dir / request_message.output_path
    assert os.path.exists(output_path)
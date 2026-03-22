import os
from pathlib import Path

from base.src.components import (
    DownloadDataComponent,
)
from base.src.formats import (
    RequestDownloadData, ResponseDownloadData,
)


def test_download_data():
    # -- test component
    component = DownloadDataComponent()
    request_message = RequestDownloadData(
        url="titanic",
        local_path="data/titanic/raw",
        is_competition=True
    )
    response_message = component(request_message)
    assert isinstance(response_message, ResponseDownloadData)
    assert response_message.status == "success"

    # -- test output
    base_dir = Path('./')
    local_path = base_dir / request_message.local_path
    assert os.path.exists(local_path)
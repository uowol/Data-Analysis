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
        url="zahrazolghadr/ab-test-cookie-cats",
        local_path="data/cookie-cats/raw",
        is_competition=False
    )
    response_message = component(request_message)
    assert isinstance(response_message, ResponseDownloadData)
    assert response_message.status == "success"

    # -- test output
    base_dir = Path('./')
    local_path = base_dir / request_message.local_path
    assert os.path.exists(local_path)
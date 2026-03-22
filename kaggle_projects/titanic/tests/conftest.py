import pytest
from pathlib import Path

from base.src.components import DownloadDataComponent
from base.src.formats import RequestDownloadData


@pytest.fixture(scope="session", autouse=True)
def download_titanic_data():
    """Download titanic data once before all tests in this directory."""
    local_path = Path("data/titanic/raw")
    train_file = local_path / "train.csv"

    if not train_file.exists():
        component = DownloadDataComponent()
        request = RequestDownloadData(
            url="titanic",
            local_path=str(local_path),
            is_competition=True,
        )
        component(request)

    assert train_file.exists(), f"Train file {train_file} does not exist"
    return local_path

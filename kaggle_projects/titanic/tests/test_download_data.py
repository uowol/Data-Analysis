import os


def test_download_data(download_titanic_data):
    """Verify that the session fixture downloaded data successfully."""
    local_path = download_titanic_data
    assert os.path.exists(local_path)
    assert os.path.exists(local_path / "train.csv")
    assert os.path.exists(local_path / "test.csv")

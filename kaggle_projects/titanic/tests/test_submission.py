"""TDD: submission.csv 및 submission_meta.json 검증 테스트."""
import json
import pytest
import pandas as pd
from pathlib import Path

SUBMISSION_PATH = Path("kaggle_projects/titanic/outputs/submission/submission.csv")
META_PATH = Path("kaggle_projects/titanic/outputs/submission/submission_meta.json")
TEST_DATA_PATH = Path("kaggle_projects/titanic/data/test.csv")


@pytest.fixture
def submission():
    assert SUBMISSION_PATH.exists(), f"{SUBMISSION_PATH} not found"
    return pd.read_csv(SUBMISSION_PATH)


@pytest.fixture
def meta():
    assert META_PATH.exists(), f"{META_PATH} not found"
    return json.loads(META_PATH.read_text())


@pytest.fixture
def test_data():
    return pd.read_csv(TEST_DATA_PATH)


class TestSubmissionCSV:
    def test_columns(self, submission):
        assert list(submission.columns) == ["PassengerId", "Survived"]

    def test_row_count_matches_test(self, submission, test_data):
        assert len(submission) == len(test_data)

    def test_no_missing_values(self, submission):
        assert submission.isnull().sum().sum() == 0

    def test_survived_values_binary(self, submission):
        assert set(submission["Survived"].unique()).issubset({0, 1})

    def test_passenger_ids_match(self, submission, test_data):
        assert list(submission["PassengerId"]) == list(test_data["PassengerId"])


class TestSubmissionMeta:
    def test_required_fields(self, meta):
        required = ["model", "features_count", "train_rows", "test_rows",
                     "prediction_distribution", "validation"]
        for field in required:
            assert field in meta, f"Missing field: {field}"

    def test_validation_passed(self, meta):
        assert meta["validation"]["rows_match"] is True
        assert meta["validation"]["no_missing"] is True
        assert meta["validation"]["format_correct"] is True

    def test_prediction_distribution(self, meta):
        dist = meta["prediction_distribution"]
        assert "survived_count" in dist and "dead_count" in dist
        assert dist["survived_count"] + dist["dead_count"] == meta["test_rows"]

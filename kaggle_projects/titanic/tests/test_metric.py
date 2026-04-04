"""TDD: metric_definition.json 스키마 및 내용 검증 테스트."""
import json
import pytest
from pathlib import Path

METRIC_PATH = Path("kaggle_projects/titanic/outputs/metric/metric_definition.json")


@pytest.fixture
def metric_def():
    assert METRIC_PATH.exists(), f"{METRIC_PATH} not found"
    return json.loads(METRIC_PATH.read_text())


class TestMetricDefinition:
    def test_required_fields(self, metric_def):
        required = ["project", "target", "problem_type", "class_distribution",
                     "primary_metric", "secondary_metrics", "metric_rationale"]
        for field in required:
            assert field in metric_def, f"Missing field: {field}"

    def test_project_name(self, metric_def):
        assert metric_def["project"] == "titanic"

    def test_target_is_survived(self, metric_def):
        assert metric_def["target"] == "Survived"

    def test_problem_type(self, metric_def):
        assert metric_def["problem_type"] == "binary_classification"

    def test_class_distribution_keys(self, metric_def):
        dist = metric_def["class_distribution"]
        assert "0" in dist and "1" in dist
        assert dist["0"] + dist["1"] == 891  # total train rows

    def test_primary_metric_is_valid(self, metric_def):
        valid = ["f1_score", "accuracy", "roc_auc", "precision", "recall"]
        assert metric_def["primary_metric"] in valid

    def test_secondary_metrics_is_list(self, metric_def):
        assert isinstance(metric_def["secondary_metrics"], list)
        assert len(metric_def["secondary_metrics"]) >= 1

    def test_metric_rationale_nonempty(self, metric_def):
        assert len(metric_def["metric_rationale"]) > 10

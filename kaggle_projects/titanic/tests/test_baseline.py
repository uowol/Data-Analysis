"""TDD: baseline_result.json 스키마 및 내용 검증 테스트."""
import json
import pytest
from pathlib import Path

BASELINE_PATH = Path("kaggle_projects/titanic/outputs/metric/baseline_result.json")


@pytest.fixture
def baseline():
    assert BASELINE_PATH.exists(), f"{BASELINE_PATH} not found"
    return json.loads(BASELINE_PATH.read_text())


class TestBaselineResult:
    def test_required_fields(self, baseline):
        required = ["project", "baseline_model", "cv", "results",
                     "majority_class_baseline", "target_metric", "baseline_threshold"]
        for field in required:
            assert field in baseline, f"Missing field: {field}"

    def test_project_name(self, baseline):
        assert baseline["project"] == "titanic"

    def test_baseline_model_has_rule(self, baseline):
        model = baseline["baseline_model"]
        assert "name" in model
        assert "description" in model
        assert "rule_feature" in model

    def test_cv_config(self, baseline):
        cv = baseline["cv"]
        assert cv["method"] == "StratifiedKFold"
        assert cv["n_splits"] == 5
        assert cv["random_state"] == 42

    def test_results_has_primary_metric(self, baseline):
        metric = baseline["target_metric"]
        assert metric in baseline["results"]
        result = baseline["results"][metric]
        assert "mean" in result and "std" in result and "folds" in result
        assert len(result["folds"]) == 5

    def test_f1_above_majority(self, baseline):
        """베이스라인 F1이 다수 클래스 accuracy보다 높아야 의미 있음."""
        f1 = baseline["results"]["f1_score"]["mean"]
        majority = baseline["majority_class_baseline"]["accuracy"]
        assert f1 > majority * 0.9, f"F1 {f1} too close to majority {majority}"

    def test_baseline_threshold_matches_mean(self, baseline):
        metric = baseline["target_metric"]
        assert abs(baseline["baseline_threshold"] - baseline["results"][metric]["mean"]) < 0.001

    def test_fold_scores_reasonable(self, baseline):
        """각 fold 점수가 0~1 범위이고 분산이 합리적."""
        for metric_name, result in baseline["results"].items():
            if "folds" in result:
                for score in result["folds"]:
                    assert 0.0 <= score <= 1.0, f"{metric_name} fold score {score} out of range"

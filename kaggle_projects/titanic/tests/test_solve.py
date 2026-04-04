"""TDD: solve_result.json 스키마 및 성능 검증 테스트."""
import json
import pytest
from pathlib import Path

SOLVE_DIR = Path("kaggle_projects/titanic/outputs/solve")
BASELINE_PATH = Path("kaggle_projects/titanic/outputs/metric/baseline_result.json")


def get_latest_iteration():
    """최신 iteration 디렉토리를 반환."""
    iters = sorted(SOLVE_DIR.glob("iteration_*"))
    assert len(iters) > 0, "No iteration directories found"
    return iters[-1]


@pytest.fixture
def solve_result():
    path = get_latest_iteration() / "solve_result.json"
    assert path.exists(), f"{path} not found"
    return json.loads(path.read_text())


@pytest.fixture
def feature_insights():
    path = get_latest_iteration() / "feature_insights.json"
    assert path.exists(), f"{path} not found"
    return json.loads(path.read_text())


@pytest.fixture
def baseline():
    return json.loads(BASELINE_PATH.read_text())


class TestSolveResult:
    def test_required_fields(self, solve_result):
        required = ["project", "preprocessing_plan", "cv", "models",
                     "best_model", "best_f1"]
        for field in required:
            assert field in solve_result, f"Missing field: {field}"

    def test_project_name(self, solve_result):
        assert solve_result["project"] == "titanic"

    def test_cv_config(self, solve_result):
        cv = solve_result["cv"]
        assert cv["method"] == "StratifiedKFold"
        assert cv["n_splits"] == 5
        assert cv["random_state"] == 42

    def test_minimum_3_models(self, solve_result):
        assert len(solve_result["models"]) >= 3, "Need at least 3 models"

    def test_has_linear_model(self, solve_result):
        types = [m.get("type") for m in solve_result["models"].values()]
        assert "linear" in types, "Must include a linear model"

    def test_has_tree_model(self, solve_result):
        types = [m.get("type") for m in solve_result["models"].values()]
        assert any(t in types for t in ["ensemble_tree", "boosting"]), \
            "Must include a tree-based model"

    def test_each_model_has_rationale(self, solve_result):
        for name, model in solve_result["models"].items():
            assert "rationale" in model, f"{name} missing rationale"
            assert len(model["rationale"]) > 5, f"{name} rationale too short"

    def test_each_model_has_f1(self, solve_result):
        for name, model in solve_result["models"].items():
            f1 = model["results"]["f1_score"]
            assert "mean" in f1 and "folds" in f1
            assert len(f1["folds"]) == 5
            assert all(0 <= s <= 1 for s in f1["folds"])

    def test_best_model_beats_baseline(self, solve_result, baseline):
        threshold = baseline["baseline_threshold"]
        assert solve_result["best_f1"] > threshold, \
            f"Best F1 {solve_result['best_f1']} <= baseline {threshold}"

    def test_best_model_is_in_models(self, solve_result):
        assert solve_result["best_model"] in solve_result["models"]


class TestFeatureInsights:
    def test_required_fields(self, feature_insights):
        required = ["linear_coefficients", "tree_importances", "consensus"]
        for field in required:
            assert field in feature_insights, f"Missing field: {field}"

    def test_coefficients_nonempty(self, feature_insights):
        assert len(feature_insights["linear_coefficients"]) > 0

    def test_importances_nonempty(self, feature_insights):
        assert len(feature_insights["tree_importances"]) > 0

    def test_consensus_nonempty(self, feature_insights):
        assert len(feature_insights["consensus"]) > 0

---
name: kaggle-metric
description: Define target variable, problem type, and evaluation metric for Kaggle projects
user_invocable: true
---

# Kaggle Metric Skill

insight 스킬의 전처리 계획을 기반으로 문제를 정의하고 평가 지표를 확정한다.

## Input

- 전처리 계획 JSON: `<project>/outputs/profiling/preprocessing_plan_*.json`
- 프로파일링 요약: `<project>/outputs/profiling/<filename>_summary.json`

## Rules

- 모든 판단은 데이터 수치 근거에서만 도출한다. 사전 지식이나 웹상의 알려진 정답을 사용하지 않는다.
- 평가 지표 선정 시 근거(클래스 불균형 정도, 문제 특성 등)를 반드시 제시한다.

## Workflow

### Step 1: 타겟 변수 확정

1. 전처리 계획 JSON에서 `target` 필드를 읽는다
2. 타겟 변수의 분포를 확인한다:
   - 고유값 수, 클래스 비율 (분류), 분포 형태 (회귀)
3. 타겟 변수를 확정하고 사용자에게 보고한다

### Step 2: 문제 유형 판단

1. 타겟 변수의 특성으로 문제 유형을 판단한다:
   - 이산값 2개 → 이진 분류
   - 이산값 3개 이상 → 다중 분류
   - 연속값 → 회귀
2. 클래스 불균형 정도를 수치로 보고한다 (분류의 경우)

### Step 3: 평가 지표 선정

1. 문제 유형에 따른 후보 지표를 제시한다:
   - 이진 분류: Accuracy, F1 Score, AUC-ROC, Precision, Recall
   - 다중 분류: Macro F1, Weighted F1, Accuracy
   - 회귀: RMSE, MAE, R²
2. 각 지표의 특성을 데이터 기반으로 비교한다:
   - 클래스 불균형이 있으면 F1/AUC 권장 근거 제시
   - 균형적이면 Accuracy 가능 근거 제시
3. **사용자와 논의하여 주 평가 지표를 확정한다**

## Output

`<project>/outputs/metric/metric_definition.json`에 저장:

```json
{
  "project": "titanic",
  "target": "Survived",
  "problem_type": "binary_classification",
  "class_distribution": {"0": 549, "1": 342},
  "primary_metric": "f1_score",
  "secondary_metrics": ["accuracy", "precision", "recall"],
  "metric_rationale": "클래스 비율 6:4 불균형 존재, 정밀도와 재현율 균형 필요"
}
```

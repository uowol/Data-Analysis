---
name: kaggle-baseline
description: Build baseline model and set target metric for Kaggle projects
user_invocable: true
---

# Kaggle Baseline Skill

metric 스킬에서 확정된 평가 지표를 기준으로 베이스라인 모델을 구축하고 목표 metric을 설정한다.

## Input

- 전처리 계획: `<project>/outputs/profiling/preprocessing_plan_*.json`
- 평가 지표 정의: `<project>/outputs/metric/metric_definition.json`
- 학습 데이터: `<project>/data/train.csv`

## Rules

- 베이스라인은 가능한 한 단순한 규칙 또는 최소 전처리 모델이어야 한다.
- 복잡한 피처 엔지니어링이나 하이퍼파라미터 튜닝을 하지 않는다.
- 모든 성능 수치는 교차 검증으로 측정한다.

## Workflow

### Step 1: 베이스라인 후보 탐색

1. metric_definition.json에서 타겟, 문제 유형, 평가 지표를 읽는다
2. 데이터에서 타겟과 가장 강한 상관을 보이는 단일 피처를 식별한다
3. 단순 규칙 베이스라인을 구성한다:
   - 이진 분류: 최강 상관 피처 기반 규칙 (예: Sex=female → 생존)
   - 회귀: 타겟 평균값 예측
4. 다수 클래스 예측(majority class)도 참고 수치로 함께 측정한다

### Step 2: 베이스라인 평가 (교차 검증)

1. StratifiedKFold(n_splits=5, shuffle=True, random_state=42)로 교차 검증을 수행한다
2. 각 fold에서 주 평가 지표 + 보조 지표를 측정한다
3. fold별 점수와 평균±표준편차를 보고한다
4. 전체 교차 검증 예측을 합산하여 Confusion matrix를 제시한다 (분류의 경우)

### Step 3: 목표 설정

1. 베이스라인 성능을 기준점으로 설정한다
2. 이후 모델은 이 기준을 넘어야 의미가 있음을 명시한다
3. **사용자에게 베이스라인 결과를 보고하고 확인을 받는다**

## Output

`<project>/outputs/metric/baseline_result.json`에 저장:

```json
{
  "project": "titanic",
  "baseline_model": {
    "name": "sex_rule",
    "description": "female=생존, male=사망",
    "rule_feature": "Sex"
  },
  "cv": {
    "method": "StratifiedKFold",
    "n_splits": 5,
    "random_state": 42
  },
  "results": {
    "f1_score": {"mean": 0.7104, "std": 0.0, "folds": [...]},
    "accuracy": {"mean": 0.7868, "std": 0.0, "folds": [...]},
    "precision": {"mean": 0.7420, "std": 0.0, "folds": [...]},
    "recall": {"mean": 0.6813, "std": 0.0, "folds": [...]}
  },
  "majority_class_baseline": {
    "accuracy": 0.6162
  },
  "target_metric": "f1_score",
  "baseline_threshold": 0.7104
}
```

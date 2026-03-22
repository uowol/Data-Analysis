---
name: kaggle-solve
description: Apply preprocessing and train models with feature insights for Kaggle projects
user-invocable: true
---

# Kaggle Solve Skill

전처리 계획을 적용하고, 모델을 학습하여 baseline을 넘는 성능을 달성한다.

## Input

- 전처리 계획: `<project>/outputs/profiling/preprocessing_plan_*.json`
- 평가 지표 정의: `<project>/outputs/metric/metric_definition.json`
- 베이스라인 결과: `<project>/outputs/metric/baseline_result.json`
- 피처 인사이트 (있으면): `<project>/outputs/metric/feature_insights.json`
- 학습 데이터: `<project>/data/train.csv`

## Rules

- 모든 성능 수치는 StratifiedKFold(n_splits=5, shuffle=True, random_state=42) 교차 검증으로 측정한다.
- 모델 선정 시 선정 이유를 반드시 명시한다.
- 해석 가능 모델을 최소 1개 포함하여 피처 인사이트를 추출한다.
- 전처리 계획이 복수(`_a`, `_b`, ...)면 각각 별도 브랜치에서 실행하고 metric 기반으로 최선을 채택한다.

## 소규모 데이터 정규화 가이드라인 (rows < 5000)

소규모 데이터셋에서는 과적합 방지가 핵심이다. 아래 원칙을 따른다:

- **부스팅 모델 선택**: sklearn GradientBoosting 대신 **XGBoost를 기본으로** 사용한다. XGBoost는 gamma, subsample, colsample_bytree 등 세밀한 정규화 파라미터를 제공한다.
- **공격적 정규화**: 소규모 데이터에서 부스팅 모델의 기본 하이퍼파라미터 가이드:
  - `learning_rate`: 0.01~0.05 (낮을수록 안정적, n_estimators를 비례 증가)
  - `max_depth`: 3~4 (깊을수록 과적합 위험)
  - `n_estimators`: 500~2000 (lr이 낮으면 보상으로 높게)
  - `gamma`: 0.3~0.6 (분할 최소 손실 감소)
  - `subsample`: 0.7~0.8, `colsample_bytree`: 0.7~0.8 (확률적 부스팅)
- **연속형 변수 구간화**: log 변환뿐 아니라 categorical binning도 반드시 시도한다. 트리 모델에서 구간화된 피처가 연속값보다 일반화 성능이 높은 경우가 빈번하다.
  - **데이터 기반 구간화**: `DecisionTreeClassifier(max_leaf_nodes=N)`으로 타겟 대비 최적 분할점을 찾는다.
  - **분위수 구간화**: `pd.qcut()`으로 등빈도 구간을 생성한다.
  - log 변환과 구간화를 동시에 적용하여 ablation으로 어느 쪽이 나은지 비교한다.

## Workflow

### Step 1: 전처리 적용

1. preprocessing_plan JSON을 읽고 전처리를 적용한다
2. 결측값 0건, 모든 피처 수치화 확인
3. 전처리 후 데이터 shape과 피처 목록을 보고한다

### Step 1.5: evaluate 피드백 반영 (재실행 시)

evaluate_result.json이 존재하면 이전 반복의 피드백을 반영한다:

1. **피처 변경안 적용**: evaluate에서 도출한 새 피처 생성, 기존 피처 조정을 적용한다
2. **피처 적용 전 검증**: 각 피처에 대해 아래를 확인한다:
   - 인코딩 방식: 범주형 상호작용 피처에 수치 인코딩 사용 금지, 원핫 인코딩 적용
   - 정보 중복: 새 피처가 기존 피처를 포함하면, 원본 제거 또는 대체 여부를 결정한다
   - 샘플 충분성: 대상 샘플이 전체의 5% 미만이면 과적합 위험을 보고한다
   - 구간 경계: 자의적 기준이면 데이터 기반 최적 경계를 탐색한다
3. **신규 모델 추가**: evaluate에서 제안한 모델 후보를 Step 2의 모델 목록에 추가한다. 선정 이유를 이전 evaluate의 구체적 한계(오분류 패턴, 모델 구조적 약점)와 연결하여 명시한다
4. 이전 반복 대비 변경점을 명시한다

### Step 2: 모델 선정 및 학습

1. 최소 3개 모델을 선정한다:
   - **선형 모델 1개** (LogisticRegression 등) — 해석 가능성, 피처 기여도 추출용
   - **트리 앙상블 1개** (RandomForest) — 비선형 관계, 피처 상호작용 포착용
   - **부스팅 모델 1개** (XGBoost) — 소규모 데이터 정규화 가이드라인에 따른 파라미터 적용. **첫 iteration부터 포함한다** (이후 튜닝할 베이스라인 확보)
   - **재실행 시**: evaluate에서 제안한 모델 후보 추가
2. 첫 실험에서도 소규모 데이터 정규화 가이드라인의 기본 파라미터를 적용한다 (sklearn 기본값을 그대로 쓰지 않는다)
3. CV로 주 평가 지표 + 보조 지표를 측정한다
4. baseline_threshold 및 이전 반복 결과와 비교하여 개선폭을 보고한다
5. **성능 하락 시 원인 분석**: 이전 반복 대비 하락한 모델이 있으면 어떤 피처/변경이 원인인지 ablation(피처 제거 실험)으로 확인한다
6. **모델 전략 우선순위**: 이전 iteration에서 큰 폭의 개선(>0.03)이 있었으면, 다음에는 하이퍼파라미터 튜닝보다 모델 구조 변경(앙상블, 다른 알고리즘)을 먼저 시도한다. 튜닝은 모델 구조가 확정된 후에 수행한다.

### Step 3: 피처 인사이트 추출

1. 선형 모델: 표준화 후 계수를 절대값 순으로 정리한다
2. 트리 모델: Gini 피처 중요도를 정리한다
3. 두 모델의 합의점과 차이점을 도출한다
4. 다음 개선 방향을 제안한다:
   - 비선형 패턴이 의심되는 피처 → 구간화 실험
   - 상위 피처 간 상호작용 피처
   - 중요도 낮은 피처 제거 실험

### Step 4: 복수 전처리 계획 처리 (해당 시)

1. preprocessing_plan이 복수면 각 계획별로 Step 1~3을 반복한다
2. 동일 모델·동일 CV 설정으로 비교한다
3. 주 평가 지표 기준 최선의 계획을 채택한다

## Output

`<project>/outputs/solve/` 디렉토리에 반복별로 저장:

```
outputs/solve/
├── iteration_1/
│   ├── solve_result.json      # 모델별 CV 결과, 피처 목록, 변경점
│   └── feature_insights.json  # 피처 계수/중요도, 합의 인사이트
├── iteration_2/
│   ├── solve_result.json
│   ├── feature_insights.json
│   └── ablation.json          # ablation 실험 결과 (있을 경우)
└── best/
    └── solve_result.json      # 현재 최선 결과 (최고 iteration에서 복사)
```

각 iteration의 solve_result.json에 반드시 포함:
- `iteration`: 반복 번호
- `features`: 사용한 피처 목록
- `changes_from_previous`: 이전 반복 대비 변경점
- `models`: 모델별 결과 (rationale 포함)
- `best_model`, `best_f1`, `vs_baseline`, `vs_prev_iteration`

### solve_result.json 예시

```json
{
  "project": "titanic",
  "preprocessing_plan": "plan_a",
  "cv": {
    "method": "StratifiedKFold",
    "n_splits": 5,
    "random_state": 42
  },
  "models": {
    "LogisticRegression": {
      "type": "linear",
      "rationale": "해석 가능한 선형 모델, 피처 기여도 추출",
      "results": {
        "f1_score": {"mean": 0.7302, "std": 0.0400, "folds": [...]},
        "accuracy": {"mean": 0.8002}
      },
      "vs_baseline": "+0.0209"
    },
    "RandomForest": {
      "type": "ensemble_tree",
      "rationale": "비선형 관계·상호작용 포착, 스케일링 불필요",
      "results": {
        "f1_score": {"mean": 0.7649, "std": 0.0291, "folds": [...]},
        "accuracy": {"mean": 0.8204}
      },
      "vs_baseline": "+0.0556"
    }
  },
  "best_model": "RandomForest",
  "best_f1": 0.7649,
  "baseline_threshold": 0.7093
}
```

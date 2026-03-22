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
- **정규화 전략**: 수동 튜닝 초기값은 보수적으로 설정한다:
    - `learning_rate`: 0.01~0.05, `n_estimators`: lr과 반비례로 설정
    - `max_depth`: 2~4 (소규모 데이터에서 3이 안정적인 시작점)
    - `min_child_weight`: 2 이상 (1은 단일 샘플 리프를 허용하여 과적합 위험)
    - `subsample`: 0.7~0.9, `colsample_bytree`: 0.7~0.9
    - gamma, reg_lambda, reg_alpha 등 정규화 파라미터 간 최적 조합은 데이터마다 다르므로 수동 직관에 의존하지 말고 HPO로 탐색한다.
  - **CV 과적합 방지 (Bayesian HPO 사용 시)**:
    - CV 스코어를 최대화해도 실제 테스트 일반화가 보장되지 않는다. HPO가 CV fold 구조에 과적합(selection bias)할 수 있다.
    - Optuna 탐색 공간을 **좁게** 유지한다 (넓은 범위 + 많은 trial = CV overfit 위험).
    - CV fold 수를 **10-fold**로 늘려 추정 안정성을 높인다.
    - trial 수는 **60~80회**로 제한한다 (150+ trials는 CV overfit 위험이 높아진다).
    - **대회 평가 지표와 동일한 metric으로 최적화**한다 (예: 대회가 Accuracy면 F1이 아닌 Accuracy로 최적화).
  - **피처 수 제어**: 소규모 데이터에서 피처를 과도하게 늘리면 CV에서는 좋아도 실제 테스트에서 하락할 수 있다. ablation 결과도 CV에 종속적임을 인지하고, 의심스러우면 단순한 피처 세트를 우선한다.
  - **인코딩 전략**: one-hot 인코딩은 피처 수를 급증시킨다. 트리 모델에서는 **ordinal 인코딩**이 피처 수를 줄이고 일반화에 유리할 수 있다. 양쪽을 시도하여 비교한다.
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
6. **모델 전략 우선순위**: 이전 iteration에서 큰 폭의 개선(>0.03)이 있었으면, 다음에는 하이퍼파라미터 튜닝보다 모델 구조 변경(앙상블, 다른 알고리즘)을 먼저 시도한다. 피처와 모델 구조가 수렴한 후에는 **Optuna Bayesian HPO**로 최종 튜닝한다. 소규모 데이터에서 앙상블(Stacking, Voting)은 메타러너 과적합 위험이 높으므로, 단독 모델 + HPO가 더 효과적일 수 있다.

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

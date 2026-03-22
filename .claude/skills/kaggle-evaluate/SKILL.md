---
name: kaggle-evaluate
description: Analyze model results and derive improvement directions for Kaggle projects
user-invocable: true
---

# Kaggle Evaluate Skill

solve 스킬의 모델 결과를 분석하고, 다음 solve 반복을 위한 개선 방향을 도출한다.

## Input

- 모델 결과: `<project>/outputs/solve/best/solve_result.json` (또는 최신 `iteration_N/solve_result.json`)
- 피처 인사이트: `<project>/outputs/solve/iteration_N/feature_insights.json` (최신 iteration)
- 베이스라인: `<project>/outputs/metric/baseline_result.json`
- 이전 evaluate 결과 (있으면): `<project>/outputs/evaluate/iteration_N-1/evaluate_result.json`
- 학습 데이터: `<project>/data/train.csv`

## Rules

- 모든 분석은 데이터 수치 근거에서만 도출한다.
- 개선 방향은 오분류 패턴에서 직접 도출한다. 일반적 ML 팁을 나열하지 않는다.
- 각 개선 방향에 기대 영향도(high/medium/low)와 근거를 명시한다.

## Workflow

### Step 1: 현재 성능 요약

1. 최선 모델의 주 평가 지표를 baseline과 비교한다
2. 이전 evaluate 결과가 있으면 반복 간 개선 추이를 보고한다

### Step 2: 오분류 분석

1. 최선 모델의 CV 예측으로 오분류 케이스를 수집한다
2. FN(실제 양성→음성 예측)과 FP(실제 음성→양성 예측)를 분리한다
3. 각 그룹의 프로필을 분석한다:
   - 주요 피처별 분포 (Sex, Pclass, Age, FamilySize 등)
   - 피처 조합별 오분류율 (Pclass × Sex 등)
   - 오분류 집중 구간 식별
4. Age 구간별, FamilySize 구간별 오분류율을 산출한다

### Step 3: 피처 개선안 도출

오분류 패턴에서 구체적인 피처 변경안을 도출한다:

1. **새 피처 생성**: 오분류 집중 구간의 패턴을 포착하는 피처
   - 피처 상호작용이 필요한 구간 → 상호작용 피처 (예: Pclass × Sex)
   - 특정 서브그룹에서 집중 오분류 → 해당 그룹 타겟 피처 (예: IsAloneFemale3rd)
2. **기존 피처 조정**: 오분류율이 높은 구간의 피처 변환
   - 비선형 패턴이 있는 피처 → 구간화 (예: Age → Child/Adult/Senior)
   - 중요도 낮은 피처 → 제거 또는 다른 피처와 결합
3. 각 변경안에 대해 기대 영향도(high/medium/low)와 수치 근거를 명시한다
4. **피처 설계 검증 체크리스트**:
   - 인코딩 방식이 적절한가? (범주형에 수치 인코딩 → 의미 없는 순서 부여 위험, 원핫 검토)
   - 기존 피처와 정보 중복이 있는가? (중복 시 제거 또는 원본 대체 명시)
   - 대상 샘플 수가 충분한가? (전체의 5% 미만이면 과적합 위험 경고)
   - 구간 경계의 근거가 있는가? (자의적 기준 vs 데이터 기반 최적 경계)

### Step 4: 모델 비교 분석 및 신규 모델 검토

1. **기존 모델 간 비교**: 선형 vs 비선형 모델의 오분류 패턴 차이 분석
   - 한쪽만 맞추는 케이스가 많으면 앙상블 가능성 시사
   - 양쪽 모두 틀리는 케이스 → 피처 부족 신호
2. **신규 모델 후보 검토**: 현재 모델의 한계에 따라 제안
   - 피처 상호작용 부족 → GradientBoosting/XGBoost 검토
   - 과적합 의심 → 정규화 강화 모델 검토
   - 단순 규칙 패턴 → 앙상블 (Voting/Stacking) 검토
3. **개선 시도의 근거**: 데이터 수치 근거뿐 아니라, 가능성이 보이는 논리적 근거가 있다면 시도를 제안한다
   - 통계적 기법: 피처 선택(mutual information, permutation importance), 클래스 가중치 조정
   - 수학적 기법: 하이퍼파라미터 탐색(Bayesian optimization), 임계값 최적화(F1 최적 threshold)
   - 확률적 기법: Stacking(메타 러너), Blending, 확률 캘리브레이션
   - 최신 방법론: 타겟 인코딩, 자동 피처 상호작용 탐색 등
   - 각 제안에 "왜 현재 상황에서 효과가 기대되는지" 논리적 근거를 명시한다
4. 신규 모델 제안 시 선정 이유를 현재 모델의 구체적 한계와 연결한다

### Step 4.5: Ablation 분석 (필수)

이번 iteration에서 새 피처를 추가했거나 피처를 변경한 경우, 변경의 기여를 검증한다:

1. 추가/변경된 각 피처를 제거한 상태에서 최선 모델의 F1을 측정한다
2. 피처별 기여도(with - without)를 산출한다
3. 기여도가 ±0.003 이내인 피처는 noise로 판단하고 제거를 권장한다
4. 결과를 `ablation.json`으로 저장한다
5. ablation 결과를 시각화한다 (bar chart: 피처별 기여도)

ablation은 **매 iteration 필수**. 피처 변경이 없는 경우(모델만 변경)는 생략 가능.

### Step 5: solve 재실행 판단

1. 피처 변경안 + 모델 변경안을 종합하여 다음 solve 반복의 실행 계획을 수립한다
2. 개선 방향이 있고 기대 영향이 high/medium이면 → solve 재실행 권장
3. 개선 방향이 low뿐이거나 성능이 수렴했으면 → 현재 모델 확정
4. **사용자에게 판단을 보고한다**

## Output

`<project>/outputs/evaluate/iteration_N/evaluate_result.json`에 iteration별로 저장:

```json
{
  "project": "titanic",
  "current_best": {
    "model": "RandomForest",
    "f1_score": 0.7649,
    "baseline_threshold": 0.7093,
    "improvement": "+0.0556"
  },
  "error_analysis": {
    "total_misclassified": 160,
    "false_negatives": {"count": 82, "profile": "...", "hardest_group": "..."},
    "false_positives": {"count": 78, "profile": "...", "hardest_group": "..."}
  },
  "improvement_directions": [
    {"direction": "...", "rationale": "...", "expected_impact": "high"}
  ],
  "ablation": {
    "<feature_name>": {"with": 0.7922, "without": 0.7892, "diff": 0.003}
  }
}
```

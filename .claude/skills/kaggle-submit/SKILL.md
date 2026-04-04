---
name: kaggle-submit
description: Generate predictions on test data and create Kaggle submission CSV
user_invocable: true
---

# Kaggle Submit Skill

최종 모델로 test 데이터에 대한 예측을 생성하고 Kaggle submission CSV를 만든다.

## Input

- 최종 모델 결과: `<project>/outputs/solve/best/solve_result.json`
- 전처리 계획: `<project>/outputs/profiling/preprocessing_plan_*.json`
- 학습 데이터: `<project>/data/train.csv`
- 테스트 데이터: `<project>/data/test.csv`
- 제출 양식 (있으면): `<project>/data/sample_submission.csv` 등

## Rules

- 학습 데이터 전체로 최종 모델을 재학습한다 (CV가 아닌 full train).
- 전처리 계획을 test 데이터에 동일하게 적용한다.
- test 데이터에 대한 전처리 시 train 데이터의 통계량(중앙값, 최빈값 등)을 사용한다 (data leakage 방지).
- 제출 양식이 있으면 해당 포맷을 따르고, 없으면 `<id_column>,<target>` 형태로 생성한다.

## Workflow

### Step 1: 제출 양식 확인

1. `<project>/data/` 에서 `sample_submission.csv` 등 제출 양식 파일을 탐색한다
2. 양식의 컬럼명과 ID 컬럼을 확인한다
3. 양식이 없으면 test.csv의 ID 컬럼 + 타겟 컬럼으로 구성한다

### Step 2: 전처리 적용 (train + test)

1. preprocessing_plan JSON을 읽고 train/test에 동일 전처리를 적용한다
2. **train 데이터의 통계량으로 test를 변환한다** (data leakage 방지):
   - 수치형 결측: train에서 계산한 중앙값/평균값으로 test 대체
   - 범주형 결측: train의 최빈값으로 test 대체
   - test에만 존재하는 결측: train 통계량 기준으로 대체
3. solve/best/solve_result.json에서 사용한 피처 목록을 읽어 동일 피처를 구성한다

### Step 3: 최종 모델 학습 + 예측

1. train 전체로 최종 모델(solve_result의 best_model)을 학습한다
2. test에 대해 예측을 생성한다
3. submission CSV를 저장한다

### Step 4: 검증

1. submission CSV의 행 수가 test.csv와 일치하는지 확인한다
2. 결측값이 없는지 확인한다
3. 제출 양식과 포맷이 일치하는지 확인한다
4. 예측 분포를 보고한다 (예: 클래스별 비율)

### Step 5: 최종 리포트 Confusion Matrix (필수)

최종 리포트의 Confusion Matrix는 **CV 예측 기반**으로 생성한다. full train fit CM은 낙관적 편향이 있으므로 사용하지 않는다.

1. 최종 모델을 동일 CV 설정(StratifiedKFold 5-fold, random_state=42)으로 `cross_val_predict`를 실행한다
2. CV 예측 결과로 Confusion Matrix를 생성한다
3. 이 CM을 최종 리포트 시각화에 사용한다

## Output

- `<project>/outputs/submission/submission.csv`
- `<project>/outputs/submission/submission_meta.json` (모델 정보, 예측 분포, 검증 결과)

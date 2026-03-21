---
name: kaggle-autopilot
description: End-to-end automated pipeline orchestration for Kaggle projects
user_invocable: true
---

# Kaggle Autopilot Skill

전체 파이프라인을 자동으로 오케스트레이션한다. 데이터만 지정하면 인사이트 추출부터 모델 확정까지 실행한다.

## Input

- 프로젝트 이름: `<project>`
- 학습 데이터: `<project>/data/train.csv` (사전 다운로드 필요, 없으면 `/kaggle-browse`로 안내)

## Rules

- 각 스킬의 Rules를 그대로 준수한다.
- 스킬 간 데이터 전달은 파일 기반 (JSON/CSV). 각 스킬의 Output 경로를 따른다.
- solve↔evaluate 루프는 최대 5회로 제한한다. 수렴 전이라도 5회 도달 시 현재 최선으로 확정.
- 최종 모델은 전체 반복 중 주 평가 지표가 가장 높았던 모델로 선택한다.

## Branch Strategy

autopilot 실행마다 타임스탬프 기반 고유 브랜치를 생성하고, 하나의 PR에서 과정을 기록한다.

```
dev (프레임워크/스킬 개발)
  └── proj/<project> (프로젝트 메인)
        └── autopilot/<project>-YYYYMMDD-HHMM (실행 브랜치)
              ├── commit: Stage 1 insight
              ├── commit: Stage 2+3 metric + baseline
              ├── commit: Stage 4 iter1~N (각 iteration별 커밋)
              └── commit: Stage 5 최종 확정

            → PR to proj/<project> (1개)
              ├── PR comment: Stage 1 결과 (전처리 계획, 품질 이슈)
              ├── PR comment: Stage 2+3 결과 (평가지표, 베이스라인)
              ├── PR comment: iter1 결과 + evaluate 피드백
              ├── PR comment: iter2~N 결과 + 수렴 판단
              └── PR comment: 최종 리포트
```

### 브랜치 생성 시점

1. **autopilot 시작 시**: `proj/<project>`에서 `autopilot/<project>-YYYYMMDD-HHMM` 브랜치 생성
2. **각 Stage 완료 시**: 해당 브랜치에 커밋 + PR 코멘트로 결과 기록
3. **복수 전처리 계획 시**: 동일 브랜치에서 순차 실행, 결과 비교 후 최선 채택
4. **완료 시**: PR을 통해 `proj/<project>`에 merge

## Pipeline

```
[proj/<project> 브랜치 생성]
1. insight → 2. metric → 3. baseline
[복수 계획 시 plan 브랜치 분기]
4. solve ↔ evaluate (루프)
[최선 plan을 proj/<project>에 merge]
5. 완료
```

### Stage 1: Insight (`/kaggle-insight`)

1. 프로파일링 실행 → 품질 분석 → 선제 분석 자동 수행
2. 전처리 계획 JSON 출력 (자율 진행, 사용자 승인 불필요)
3. 복수 계획이면 `preprocessing_plan_a.json`, `_b.json`, ... 으로 출력

### Stage 2: Metric (`/kaggle-metric`)

1. 전처리 계획에서 타겟 변수 읽기
2. 문제 유형 판단 + 평가 지표 선정
3. `metric_definition.json` 저장

### Stage 3: Baseline (`/kaggle-baseline`)

1. 타겟과 최강 상관 피처 식별
2. 단순 규칙 베이스라인 CV 평가
3. `baseline_result.json` 저장
4. **여기까지 `proj/<project>` 브랜치에서 커밋**

### Stage 3.5: PR 생성

1. autopilot 브랜치를 push하고 `proj/<project>`로의 PR을 생성한다
2. PR 본문에 Stage 1~3 요약을 포함한다
3. 이후 Stage마다 PR 코멘트로 결과를 기록한다

### Stage 4: Solve ↔ Evaluate 루프

각 iteration은 **pre → 실행 → 커밋 → post** 순서를 엄격히 따르며, 코멘트 작성이 실행보다 선행한다. 이는 사후 합리화를 방지하고, pre-iteration의 계획이 실제 실행에 영향을 주는 진정한 단계별 진행을 보장한다.

```
반복 N:
  1. PR 코멘트: pre-iteration (계획 + 가설) ← 실행 전에 반드시 먼저 작성
  2. solve + evaluate 실행 ← pre-iteration 계획대로 실행
  3. 커밋 + push: iteration_N 결과
  4. PR 코멘트: post-iteration (결과 분석 + 가설 검증)
  5. post-iteration의 "다음 계획"이 다음 pre-iteration의 입력이 됨

수렴 조건 (하나라도 충족 시 종료):
  - 주 평가 지표 개선폭 < 0.005 (2회 연속)
  - evaluate의 남은 개선안이 모두 low
  - 최대 반복 횟수(5) 도달
```

**중요: 실행 순서를 지킬 것.** pre 코멘트를 쓰지 않고 실행하거나, 모든 iteration을 한번에 돌린 뒤 코멘트를 사후 작성하면 안 된다. 코멘트가 실행의 입력이 되는 흐름을 유지해야 한다.

#### 1. pre-iteration PR 코멘트 (실행 전에 반드시 작성)

무엇을 시도하고 왜 그런지 설명. 이 코멘트의 내용이 이후 실행의 설계 문서가 된다:
- **피처 변경**: 어떤 피처를 추가/수정/제거할 것인지 + 각각의 근거
- **모델 선정**: 새 모델 추가 시 선정 이유 (이전 iteration의 구체적 한계와 연결), 대안을 제외한 이유
- **가설**: 이 변경으로 기대하는 효과와 수치적 근거. 결과를 보기 전에 작성하므로 틀려도 됨

#### 2. solve + evaluate 실행

- pre-iteration 계획대로 실행 (계획에 없는 변경을 임의로 추가하지 않음)
- solve: 전처리 적용 + 모델 학습 + 피처 인사이트 추출
- evaluate: 오분류 분석 + 피처 개선안 + 모델 검토 + 수렴 판단

#### 3. 커밋 + push

- iteration 결과 JSON + 시각화 PNG 커밋
- push하여 PR에 diff 반영

#### 4. post-iteration PR 코멘트 (실행 후 작성)

결과 분석과 다음 방향:
- **결과 요약**: 모델별 F1, 이전 iteration 대비 변화, 오분류 건수
- **가설 검증**: pre-iteration에서 세운 가설이 맞았는지 수치로 확인. 틀렸으면 왜 틀렸는지 분석
- **오분류 분석**: FN/FP 프로필, 오분류 집중 구간 변화
- **시각화**: 모델 비교 차트, confusion matrix, 피처 중요도 (이미지 첨부)
- **다음 계획**: 수렴이면 종료 선언, 아니면 다음 iteration의 방향 → 이것이 다음 pre-iteration의 입력

### Stage 5: Submit (`/kaggle-submit`)

1. test.csv에 대해 최종 모델로 예측 생성
2. submission CSV 저장 + 검증 (행 수, 결측, 포맷)
3. 커밋 + PR 코멘트 (예측 분포, 검증 결과)

### Stage 6: 완료

1. 전체 반복 중 주 평가 지표가 가장 높았던 iteration을 `best/`에 저장
2. 최종 리포트 PR 코멘트 출력 (아래 PR 품질 가이드라인 참조)
3. `proj/<project>` 브랜치에 최종 커밋
4. 사용자에게 결과를 보고한다

## PR 품질 가이드라인

PR 하나만으로 에이전트가 꼼꼼한 분석과 실험을 수행했는지 판단할 수 있어야 한다.

### 시각화 (필수)

각 Stage/iteration의 PR 코멘트에 시각화를 포함한다. matplotlib로 생성하여 `<project>/outputs/figures/` 에 PNG로 저장하고, git에 커밋한 뒤 PR 코멘트에서 GitHub 이미지 URL로 참조한다.

**Stage 1 (Insight)**:
- 타겟 변수 분포 (bar chart)
- 주요 수치형 피처 분포 (히스토그램, 변환 전후 비교)
- 결측률 히트맵 또는 바 차트
- 상관관계 히트맵

**Stage 3 (Baseline)**:
- 베이스라인 Confusion Matrix 히트맵

**각 Iteration (Solve + Evaluate)**:
- 모델별 F1 비교 바 차트
- Confusion Matrix 히트맵 (최선 모델)
- 피처 중요도 바 차트 (상위 10개)
- Pclass×Sex 오분류율 히트맵

**최종 리포트 (Stage 6)**:
- 반복 간 F1 추이 라인 차트
- 최종 모델 Confusion Matrix
- 피처 중요도 최종 바 차트
- submission 예측 분포 (있을 경우)

### PR 코멘트 이미지 참조 형식

```markdown
![Chart Title](https://github.com/<owner>/<repo>/blob/<branch>/<project>/outputs/figures/<filename>.png?raw=true)
```

### 모델 선정 근거 (필수)

각 pre-iteration 코멘트에 반드시 포함:
- 선정한 모델의 구조적 특성과 현재 데이터/문제에 적합한 이유
- 대안 모델을 제외한 이유 (데이터 크기, 피처 특성, 인사이트 제공 여부 등)
- 이전 iteration의 구체적 한계와 연결

### 결과 파일 링크 (필수)

최종 리포트에 모든 iteration의 solve_result.json + best + submission.csv 다운로드 링크를 포함한다.

## Output

```
<project>/outputs/
├── profiling/
│   ├── train_summary.json
│   ├── train_profile.html (gitignored)
│   └── preprocessing_plan_a.json (복수 시 _b, _c, ...)
├── metric/
│   ├── metric_definition.json
│   └── baseline_result.json
├── solve/
│   ├── iteration_1/ ~ iteration_N/
│   │   ├── solve_result.json
│   │   ├── feature_insights.json
│   │   └── ablation.json (있을 경우)
│   └── best/
│       └── solve_result.json
├── evaluate/
│   └── iteration_1/ ~ iteration_N/
│       └── evaluate_result.json
├── submission/
│   ├── submission.csv
│   └── submission_meta.json
└── figures/
    └── *.png (시각화 차트)
```

## 실행 원칙

- **매 실행은 새로 시작**: autopilot 호출 시 기존 outputs/결과를 확인하지 않는다. 새 브랜치에서 처음부터 전체 파이프라인을 실행한다.
- **기존 상태 무시**: 이전 autopilot 실행의 결과물(JSON, CSV, figures)은 참조하지 않는다. 각 실행은 독립적이다.
- **브랜치 격리**: 각 실행은 고유 브랜치에서 진행되므로 서로 간섭하지 않는다.

## Error Handling

- 스킬 실행 중 에러 발생 시 해당 단계에서 중단하고 사용자에게 보고한다.
- 부분 완료된 결과는 그대로 유지하여 재실행 시 이어서 진행할 수 있게 한다.

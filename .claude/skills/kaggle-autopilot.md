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
        └── proj/<project>/autopilot-YYYYMMDD-HHMM (실행 브랜치)
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

1. **autopilot 시작 시**: `proj/<project>`에서 `proj/<project>/autopilot-YYYYMMDD-HHMM` 브랜치 생성
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

```
반복 N=1:
  solve: 전처리 적용 + 선형/비선형 모델 학습 + 피처 인사이트 추출
  evaluate: 오분류 분석 + 피처 개선안 + 모델 검토 + 수렴 판단

반복 N=2~5:
  solve: evaluate 피드백 반영 (피처 검증 → 모델 추가 → 학습 → ablation)
  evaluate: 반복 간 비교 + 수렴 판단

수렴 조건 (하나라도 충족 시 종료):
  - 주 평가 지표 개선폭 < 0.005 (2회 연속)
  - evaluate의 남은 개선안이 모두 low
  - 최대 반복 횟수(5) 도달
```

### Stage 5: 완료

1. 전체 반복 중 주 평가 지표가 가장 높았던 iteration을 `best/`에 저장
2. 최종 리포트 출력:
   - 최종 모델명, 피처 목록, 주 평가 지표 (CV 평균 ± 표준편차)
   - baseline 대비 개선폭
   - 반복 간 성능 추이 테이블
   - 잔존 오분류 집중 구간
3. `proj/<project>` 브랜치에 최종 커밋
4. 사용자에게 결과를 보고한다

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
└── evaluate/
    └── evaluate_result.json
```

## Error Handling

- 스킬 실행 중 에러 발생 시 해당 단계에서 중단하고 사용자에게 보고한다.
- 부분 완료된 결과는 그대로 유지하여 재실행 시 이어서 진행할 수 있게 한다.
- 이미 완료된 단계의 출력 파일이 존재하면 해당 단계를 건너뛴다 (재실행 지원).

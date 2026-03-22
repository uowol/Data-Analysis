---
name: kaggle-insight
description: Data profiling and quality analysis for Kaggle project datasets
user-invocable: true
---

# Kaggle Insight Skill

다운로드된 Kaggle 데이터에 대해 프로파일링을 실행하고, 품질 분석 및 전처리 계획을 수립한다.

## CLI Usage

```bash
# 데이터 프로파일링 실행
uv run python -m kaggle_projects.profile kaggle_projects/<project>/data

# 커스텀 출력 경로
uv run python -m kaggle_projects.profile kaggle_projects/<project>/data --output kaggle_projects/<project>/outputs/profiling

# JSON 요약 출력 (파싱용)
uv run python -m kaggle_projects.profile kaggle_projects/<project>/data --json
```

## Rules

- 모든 인사이트와 주장은 반드시 현재 데이터의 수치 근거(프로파일링 결과, 직접 계산한 통계량)에서만 도출한다.
- 유명한 문제라도 사전 지식이나 웹상의 알려진 정답을 분석 결과로 포장하지 않는다.
- 근거 없는 해석이나 도메인 상식에 기반한 추측을 인사이트로 제시하지 않는다.

## Workflow

### Phase 1: 프로파일링 + 선제 분석 (자율 진행)

1. `--json`으로 프로파일링 실행하여 요약 JSON을 파싱한다
2. summary JSON에서 핵심 품질 이슈를 파악한다:
   - 결측률이 높은 컬럼 (>5%)
   - 이상치가 의심되는 컬럼 (skewness > 2, zeros > 30%)
   - 중복 행
   - 고유값 비율 이상 (unique ID vs 낮은 cardinality)
   - 주요 상관관계
3. **품질 이슈별 선제 분석을 자동 수행한다:**
   - 높은 왜도 (skewness > 2): 분포 시각화 + log 변환 전후 비교 (skewness, 구간별 빈도)
   - 높은 결측률 (>5%): 결측 여부 vs 타겟 상관성 + 다른 주요 변수와의 교차 분석 (Pclass 통제 등)
   - 영값 과다 (zeros > 30%): 영값 케이스의 전체 프로필 패턴 (Sex, Pclass, Embarked 등 주요 변수 분포)
   - 관련 컬럼 쌍: 합산/파생 피처 후보 생성 + 타겟별 분포 확인
4. 데이터 품질 이슈를 표로 정리하고, 선제 분석 결과와 함께 보고한다

### Phase 2: 전처리 계획 수립 + JSON 출력

5. 품질 이슈 + 선제 분석 기반으로 전처리 계획을 수립한다:
   - 결측치 처리 전략 (삭제/대체/모델 기반)
   - 이상치 처리 방안
   - 인코딩 전략 (범주형)
   - 피처 엔지니어링 (합산, 파생, drop 대상)
   - 스케일링 필요성
6. 전처리 계획을 JSON으로 저장한다:
   - 단일 계획: `preprocessing_plan_a.json`
   - 복수 계획 (처리 전략이 분기될 때): `preprocessing_plan_a.json`, `_b.json`, ...
   - 각 계획은 독립적으로 `/kaggle-solve`에서 실행 가능해야 한다
7. autopilot에서 호출 시: 자율 진행 (사용자 승인 불필요)
8. 단독 실행 시: 사용자에게 전처리 계획을 제시하고 승인을 받은 후 진행한다

## Output

- HTML 리포트: `<project>/outputs/profiling/<filename>_profile.html` (gitignored)
- 요약 JSON: `<project>/outputs/profiling/<filename>_summary.json`
- 전처리 계획: `<project>/outputs/profiling/preprocessing_plan_a.json` (복수 시 `_b.json`, ...)
- 터미널: 품질 요약 테이블 + 선제 분석 결과 + 전처리 계획

## Preprocessing Plan JSON Schema

```json
{
  "project": "titanic",
  "target": "Survived",
  "drop_columns": ["PassengerId", "Name", "Ticket", "Cabin", "SibSp", "Parch"],
  "preprocessing": {
    "<column>": {
      "strategy": "log1p | group_median_impute | binary_flag | mode_impute_and_onehot | binary_encode | combine",
      "note": "수치 근거 기반 선정 이유 (결측 시 생존율 차이, 교란 변수 통제 결과 등 구체적 수치 포함)",
      ...strategy별 추가 필드
    }
  },
  "final_features": ["최종 피처 목록 — 전처리 후 모델에 입력될 피처를 명시"],
  "scaling": "모델에 따라 결정 (트리 기반: 불필요, 선형 모델: StandardScaler)"
}
```

## Summary JSON Fields

```json
{
  "filename": "train.csv",
  "overview": { "rows", "columns", "missing_cells", "missing_pct", "duplicate_rows" },
  "columns": {
    "<col_name>": { "type", "missing", "missing_pct", "distinct", "mean", "std", "skewness", ... }
  },
  "top_correlations": [{ "columns": ["A", "B"], "correlation": 0.85 }],
  "alerts": ["High correlation", "Missing values", ...]
}
```

---
name: kaggle-insight
description: Data profiling and quality analysis for Kaggle project datasets
user_invocable: true
---

# Kaggle Insight Skill

다운로드된 Kaggle 데이터에 대해 프로파일링을 실행하고, 데이터 품질 인사이트를 제공한다.

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

데이터를 다운로드한 후 인사이트를 추출할 때:

### Phase 1: 프로파일링 (자율 진행)
1. `--json`으로 프로파일링 실행하여 요약 JSON을 파싱한다
2. summary JSON에서 핵심 품질 이슈를 파악한다:
   - 결측률이 높은 컬럼 (>5%)
   - 이상치가 의심되는 컬럼 (skewness > 2, zeros > 30%)
   - 중복 행
   - 고유값 비율 이상 (unique ID vs 낮은 cardinality)
   - 주요 상관관계
3. 데이터 품질 이슈를 표로 정리하여 사용자에게 보고한다

### Phase 2: 전처리 계획 (사용자 검수 필요)
4. 품질 이슈 기반으로 전처리 계획을 수립한다:
   - 결측치 처리 전략 (삭제/대체/모델 기반)
   - 이상치 처리 방안
   - 인코딩 전략 (범주형)
   - 스케일링 필요성
5. **사용자에게 전처리 계획을 제시하고 승인을 받은 후 진행한다**

### Phase 3: 문제 정의 및 모델링 방향 (사용자와 논의)
6. 사용자와 함께 해결할 문제를 정의한다:
   - 타겟 변수 선정
   - 분류/회귀/클러스터링 등 문제 유형
   - 평가 지표
7. 문제에 맞는 모델링 기법을 추천한다:
   - 기본 모델 후보
   - 앙상블 전략
   - 교차 검증 방법
8. **여기까지만 진행. 실제 모델 구현은 별도 스킬에서 처리.**

## Output

- HTML 리포트: `<project>/outputs/profiling/<filename>_profile.html`
- 요약 JSON: `<project>/outputs/profiling/<filename>_summary.json`
- 터미널: 컬럼별 품질 요약 테이블 + 상관관계 + 알림

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

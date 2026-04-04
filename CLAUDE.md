# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kaggle 데이터셋을 대상으로 EDA를 통해 인사이트를 도출하고, 주어진 문제에 대해 유의미한 ML 모델을 적합시켜 해결하는 데이터 분석 프로젝트. 각 Kaggle 프로젝트(titanic, base 등)를 표준화된 Component/Pipeline 구조로 실행한다.

## Repository Structure

- `kaggle_projects/` — 데이터 분석 파이프라인 프레임워크 및 개별 프로젝트 코드
- `Dockerfile`, `.devcontainer/` — 개발 환경 (VS Code Dev Container 기반)
- `.claude/skills/` — Claude Code 커스텀 스킬 (kaggle-browse 등)

## Commands

```bash
# 의존성 설치
uv sync

# 프로젝트별 추가 의존성 설치
uv pip install -r kaggle_projects/<project>/requirements.txt

# 프로젝트 파이프라인 실행
uv run python -m kaggle_projects.run --project_name=titanic
uv run python -m kaggle_projects.run --project_name=titanic --pipeline_name=default

# Kaggle 대회/데이터셋 검색
uv run python -m kaggle_projects.run --browse --type dataset --search "keyword"
uv run python -m kaggle_projects.run --browse --type competition --search "keyword"
uv run python -m kaggle_projects.browse --type dataset --search "keyword" --json
uv run python -m kaggle_projects.browse --type dataset --search "keyword" --detail 1 --download

# 데이터 프로파일링
uv run python -m kaggle_projects.profile kaggle_projects/<project>/data
uv run python -m kaggle_projects.profile kaggle_projects/<project>/data --json

# 전체 테스트 실행
uv run pytest kaggle_projects/base/tests kaggle_projects/titanic/tests

# 단일 테스트 실행
uv run pytest kaggle_projects/titanic/tests/test_modeling.py

# 포매팅
uv run black .
uv run isort .
```

## Architecture

### Component-Pipeline 패턴

모든 프로젝트는 `base` 프로젝트의 추상 클래스를 상속하는 구조:

- **`base/src/pipelines/base.py`** — `Pipeline` ABC: `init(**config)` + `call()` 메서드 구현 필요
- **`base/src/components/base.py`** — `Component` ABC: `init(**config)` + `call(RequestMessage) -> ResponseMessage` 구현 필요
- **`base/src/formats.py`** — Pydantic 기반 `RequestMessage`/`ResponseMessage` 베이스 모델

### 프로젝트 구조 (kaggle_projects/)

```
kaggle_projects/
├── run.py                  # 엔트리포인트: --project_name으로 파이프라인 실행, --browse로 Kaggle 검색
├── browse.py               # Kaggle 대회/데이터셋 검색 CLI (rich 테이블 + JSON 출력)
├── profile.py              # 데이터 프로파일링 CLI (ydata-profiling + 핵심 요약 추출)
├── base/                   # 공통 컴포넌트 (download_data, extract_data_info)
│   └── src/
│       ├── components/     # 각 컴포넌트는 component.py + component.yaml
│       ├── pipelines/      # pipeline.py + pipeline.yaml (config)
│       └── formats.py      # Pydantic request/response 모델
└── <project>/              # 개별 프로젝트 (예: titanic)
    └── src/
        ├── components/     # 프로젝트 고유 컴포넌트
        ├── pipelines/      # base Pipeline 상속, 컴포넌트 조합
        ├── models/         # ML 모델 구현
        └── formats.py      # 프로젝트 고유 request/response 모델
```

### 실행 흐름

1. `run.py`가 `--project_name`에 해당하는 `pipelines/default/pipeline.yaml` 설정을 로드
2. Pipeline의 `call()`이 설정에 따라 Component들을 순차 실행
3. 각 Component는 `RequestMessage`를 받아 `ResponseMessage`를 반환
4. `upstream_events` 리스트로 이전 Component의 결과를 다음에 전달

### 새 프로젝트 추가 시

1. `kaggle_projects/<name>/` 디렉토리 생성
2. `src/formats.py`에 Pydantic request/response 모델 정의
3. `src/components/`에 Component 구현 (base.Component 상속)
4. `src/pipelines/default/pipeline.py` + `pipeline.yaml` 작성 (base.Pipeline 상속)
5. `requirements.txt`에 프로젝트 고유 의존성 추가
6. `tests/`에 컴포넌트별 테스트 작성

## Environment

- Python >=3.10, <3.13 (CI: 3.12)
- uv로 의존성 관리
- `pythonpath`는 `pyproject.toml`의 `[tool.pytest.ini_options]`에서 설정됨 (런타임은 `run.py`에서 처리)
- Kaggle API 사용 시 `~/.kaggle/kaggle.json` 필요

## CI

- `dev` 브랜치 push 및 `main` PR 시 GitHub Actions 실행
- base와 titanic 프로젝트의 pytest를 각각 실행

## Code Style

- black (line-length=88), isort (profile=black)

## Branch Strategy

- `dev` — 프레임워크 공통 기능 개발 + autopilot 실행 결과 수집
- `autopilot/<project>-YYYYMMDD-HHMM` — autopilot 실행 브랜치 (dev에서 분기, PR to dev)
- `main` — 안정 브랜치. PR을 통해서만 merge

## Automation Pipeline (목표)

데이터만 지정하면 end-to-end로 자동 수행하는 스킬 파이프라인을 점진적으로 구축한다.
상세 로드맵은 `TODO.md` 참조. 각 스킬은 titanic 프로젝트로 검증 후 범용화.

```
다운로드 → 인사이트 추출 → metric 정의 → baseline 모델 → 문제 해결 → 결과 분석 → 개선 반복 → 제출 → 알림
(browse)   (insight)       (metric)      (baseline)     (solve)      (evaluate)   (solve↔evaluate)  (submit) (autopilot)
```

### 스킬 현황

| 스킬 | 상태 | 설명 |
|------|------|------|
| `/kaggle-browse` | 완료 | Kaggle 검색 및 다운로드 |
| `/kaggle-insight` | 완료 | 프로파일링 및 품질 분석 |
| `/kaggle-metric` | 완료 | metric 정의, 평가 기준 설정 |
| `/kaggle-baseline` | 완료 | baseline 모델 + 목표 metric |
| `/kaggle-solve` | 완료 | 전처리 + 모델링 |
| `/kaggle-evaluate` | 완료 | 결과 분석 + 개선 방향 |
| `/kaggle-submit` | 완료 | test 예측 + submission CSV 생성 |
| `/kaggle-autopilot` | 완료 | 전체 파이프라인 자동 실행 |

### 개발 방침

- **TDD**: 테스트 먼저 작성 → 실패 확인 → 최소 구현 → 검증 반복
- **점진적 자동화**: 처음은 사용자와 논의하며 의사결정, 스킬이 성숙하면 자동화 수준을 높임
- **스킬 독립성**: 각 스킬은 단독 실행 가능, 스킬 간 데이터 전달은 파일 기반 (JSON/CSV)
- **데이터 기반**: 모든 인사이트/결정은 데이터 수치 근거에서만 도출 (사전 지식 사용 금지)

## Workflow

- 커밋 시 `/commit` 스킬을 사용할 것 (simplify → 수정 → 커밋을 하나의 흐름으로 처리)
- 사용자와 워크플로우 정렬이나 요구사항 정리가 필요할 때 `/oh-my-claudecode:deep-interview` 스킬을 사용할 것

## Skill Triggers

사용자 요청에 아래 키워드가 포함되면, 직접 작업하지 말고 해당 스킬을 먼저 호출할 것.

| 키워드 | 스킬 |
|--------|------|
| 인사이트, EDA, 프로파일링, 데이터 분석, 데이터 품질, 탐색적 분석 | `/kaggle-insight` |
| 캐글 검색, 데이터셋 검색, 대회 검색 | `/kaggle-browse` |
| 커밋, 마무리 | `/commit` |
| 인터뷰, 워크플로우 정렬, 요구사항 정리 | `/oh-my-claudecode:deep-interview` |
| metric, 평가 지표, 타겟 변수, 문제 정의 | `/kaggle-metric` |
| 베이스라인, baseline, 기준 모델 | `/kaggle-baseline` |
| 전처리, 모델링, 학습, solve | `/kaggle-solve` |
| 결과 분석, 오분류, 개선 방향, evaluate | `/kaggle-evaluate` |
| 제출, submission, 예측, submit | `/kaggle-submit` |
| autopilot, 자동 실행, end-to-end | `/kaggle-autopilot` |

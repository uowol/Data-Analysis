# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kaggle 데이터셋을 대상으로 EDA를 통해 인사이트를 도출하고, 주어진 문제에 대해 유의미한 ML 모델을 적합시켜 해결하는 데이터 분석 프로젝트. 각 Kaggle 프로젝트(titanic, base 등)를 표준화된 Component/Pipeline 구조로 실행한다.

## Repository Structure

- `kaggle_projects/` — 데이터 분석 파이프라인 프레임워크 및 개별 프로젝트 코드
- `Dockerfile`, `.devcontainer/` — 개발 환경 (VS Code Dev Container 기반)
- `.claude/skills/` — Claude Code 활용을 위한 커스텀 스킬 (향후 확장 예정)

## Commands

```bash
# 의존성 설치
uv sync

# 프로젝트별 추가 의존성 설치
uv pip install -r kaggle_projects/<project>/requirements.txt

# 프로젝트 파이프라인 실행
uv run python -m kaggle_projects.run_project --project_name=titanic
uv run python -m kaggle_projects.run_project --project_name=titanic --pipeline_name=default

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
├── run_project.py          # 엔트리포인트: --project_name으로 프로젝트 선택
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

1. `run_project.py`가 `--project_name`에 해당하는 `pipelines/default/pipeline.yaml` 설정을 로드
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
- `pythonpath`는 `pyproject.toml`의 `[tool.pytest.ini_options]`에서 설정됨 (런타임은 `run_project.py`에서 처리)
- Kaggle API 사용 시 `~/.kaggle/kaggle.json` 필요

## CI

- `dev` 브랜치 push 및 `main` PR 시 GitHub Actions 실행
- base와 titanic 프로젝트의 pytest를 각각 실행

## Code Style

- black (line-length=88), isort (profile=black)

## Workflow

- 커밋 전 반드시 `/simplify` 스킬을 실행하여 변경된 코드의 재사용성, 품질, 효율성을 점검할 것

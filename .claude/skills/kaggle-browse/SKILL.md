---
name: kaggle-browse
description: Search, recommend, and download Kaggle competitions/datasets
user_invocable: true
---

# Kaggle Browse Skill

Kaggle에서 대회(competition)나 데이터셋(dataset)을 검색, 추천, 다운로드한다.

## CLI Usage

```bash
# 데이터셋 검색
uv run python -m kaggle_projects.browse --type dataset --search "<keyword>" --limit 10

# 대회 검색
uv run python -m kaggle_projects.browse --type competition --search "<keyword>" --limit 10

# 상세 정보 (1-based index)
uv run python -m kaggle_projects.browse --type dataset --search "<keyword>" --detail 1

# JSON 출력 (파싱용)
uv run python -m kaggle_projects.browse --type dataset --search "<keyword>" --json

# 정렬 옵션
# competition: latestDeadline, numberOfTeams, recentlyCreated
# dataset: hottest, votes, updated, active
uv run python -m kaggle_projects.browse --type dataset --sort votes --search "<keyword>"

# 다운로드 (--detail과 함께 사용)
uv run python -m kaggle_projects.browse --type dataset --search "<keyword>" --detail 1 --download
uv run python -m kaggle_projects.browse --type competition --search "<keyword>" --detail 1 --download --download-path "kaggle_projects/<project>/data"
```

## Workflow

사용자가 새 프로젝트를 시작하고 싶거나 데이터셋/대회를 찾고 싶을 때:

1. 사용자의 관심 주제를 파악한다
2. `--json` 플래그로 검색하여 결과를 파싱한다
3. 결과를 분석하여 사용자에게 적합한 항목을 추천한다 (난이도, 데이터 크기, 인기도 등 고려)
4. 사용자가 선택하면 `--detail`로 상세 정보를 보여준다
5. 사용자가 승인하면 `--download`로 데이터를 다운로드한다
6. 다운로드 경로는 기본값 `kaggle_projects/<slug>/data` 또는 `--download-path`로 지정

## Download Notes

- 기본 다운로드 경로: `kaggle_projects/<dataset-slug>/data`
- `--download-path`로 커스텀 경로 지정 가능
- ZIP 파일은 자동으로 해제 후 삭제됨
- 대회(competition)는 사전에 규칙 동의(Accept Rules)가 필요할 수 있음 — 실패 시 사용자에게 Kaggle 웹에서 동의하도록 안내

## Output Fields

### Dataset
- `ref`: 데이터셋 식별자 (예: `heptapod/titanic`)
- `title`, `description`, `size`, `downloads`, `votes`, `usability`, `tags`, `url`

### Competition
- `ref`: 대회 식별자 (예: `titanic`)
- `title`, `description`, `deadline`, `reward`, `category`, `team_count`, `tags`, `url`

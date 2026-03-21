# Data-Analysis

Kaggle 데이터셋을 대상으로 EDA와 ML 모델링을 수행하는 데이터 분석 프로젝트.
Claude Code 에이전트를 적극 활용하여 데이터 탐색부터 인사이트 추출까지 자동화된 워크플로우를 제공한다.

## Requirements

- Python >=3.11, <3.13
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- [Claude Code](https://claude.ai/code) + [oh-my-claudecode](https://github.com/anthropics/oh-my-claudecode) (에이전트 오케스트레이션)
- Kaggle API 인증: `~/.kaggle/kaggle.json`

## Setup

```bash
# 의존성 설치
uv sync

# Claude Code 실행 (프로젝트 루트에서)
claude
```

## Usage

### CLI 직접 사용

```bash
# 파이프라인 실행
uv run python -m kaggle_projects.run --project_name=titanic

# Kaggle 검색
uv run python -m kaggle_projects.browse --type dataset --search "titanic" --limit 5
uv run python -m kaggle_projects.browse --type competition --search "nlp" --json

# 검색 → 다운로드
uv run python -m kaggle_projects.browse --type dataset --search "housing" --detail 1 --download

# 데이터 프로파일링
uv run python -m kaggle_projects.profile kaggle_projects/titanic/data
```

### Claude Code 스킬

이 프로젝트는 Claude Code 에이전트가 스킬을 통해 자율적으로 작업을 수행할 수 있도록 설계되었다.

| 스킬 | 설명 |
|------|------|
| `/kaggle-browse` | Kaggle 대회/데이터셋 검색, 추천, 다운로드 |
| `/kaggle-insight` | ydata-profiling 기반 데이터 품질 분석 및 전처리 계획 수립 |
| `/commit` | /simplify 코드 리뷰 후 커밋 (품질 점검 일체형) |
| `/interview` | 사용자와 워크플로우 정렬을 위한 구조화된 인터뷰 |

#### 에이전트 워크플로우 예시

```
사용자: "시계열 예측 프로젝트를 시작하고 싶어"
  → /kaggle-browse로 관련 데이터셋/대회 검색 및 추천
  → 사용자 선택 후 다운로드
  → /kaggle-insight로 데이터 프로파일링 및 품질 분석
  → 전처리 계획 수립 → 사용자 승인 → 실행
  → 문제 정의 논의 → 모델링 기법 추천
```

## Project Structure

```
kaggle_projects/
├── run.py              # 엔트리포인트 (파이프라인 실행 / 브라우징)
├── browse.py           # Kaggle 검색·다운로드 CLI
├── profile.py          # 데이터 프로파일링 CLI
├── base/               # 공통 컴포넌트 (Component/Pipeline ABC)
└── <project>/          # 개별 Kaggle 프로젝트 (예: titanic)

.claude/skills/         # Claude Code 스킬 정의
```

## Branch Strategy

- `proj/<name>` — 개별 Kaggle 프로젝트 (분석, 모델링)
- `dev` — 프레임워크 공통 기능 개발
- `main` — 안정 브랜치 (PR을 통해서만 merge)

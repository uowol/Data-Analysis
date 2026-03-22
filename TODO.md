# TODO — 자동화 파이프라인 로드맵

데이터만 지정하면 end-to-end로 분석→모델링→개선→목표 달성까지 자동 수행하는 스킬 파이프라인 구축.
개발 방식: TDD (테스트 → 구현 → 검증 반복). 각 스킬은 titanic 프로젝트로 검증 후 범용화.

## 완료된 스킬

- [x] `/kaggle-browse` — Kaggle 대회/데이터셋 검색 및 다운로드
- [x] `/kaggle-insight` — 프로파일링 + 선제 분석 + 전처리 계획 JSON 출력
- [x] `/kaggle-metric` — 타겟 변수 확정, 문제 유형 판단, 평가 지표 선정
- [x] `/kaggle-baseline` — 베이스라인 모델 CV 평가, 목표 metric 설정
- [x] `/kaggle-solve` — 전처리 + 모델 학습 + 피처 인사이트 + iteration 기록
- [x] `/kaggle-evaluate` — 오분류 분석 + 피처/모델 개선안 + 수렴 판단
- [x] `/kaggle-submit` — test 예측 + submission CSV 생성 (data leakage 방지)
- [x] `/kaggle-autopilot` — 전체 파이프라인 자동 오케스트레이션 (strict pre→execute→post, 시각화, PR 코멘트)

## 다음 작업

- [ ] titanic에서 autopilot end-to-end 검증 (strict pre→execute→post 워크플로우)
- [ ] 다른 캐글 프로젝트에서 범용성 검증
- [ ] insight 스킬 복수 전처리 계획 생성 실전 검증

## 원칙

- 각 스킬은 독립적으로 실행 가능해야 함
- 스킬 간 데이터 전달은 파일 기반 (JSON/CSV)
- 새 스킬 개발 시 titanic으로 먼저 검증
- 모든 인사이트/결정은 데이터 수치 근거에서만 도출

# TODO — 자동화 파이프라인 로드맵

데이터만 지정하면 end-to-end로 분석→모델링→개선→목표 달성까지 자동 수행하는 스킬 파이프라인 구축.
개발 방식: TDD (테스트 → 구현 → 검증 반복). 각 스킬은 titanic 프로젝트로 검증 후 범용화.

## 완료된 스킬

- [x] `/kaggle-browse` — Kaggle 대회/데이터셋 검색 및 다운로드
- [x] `/kaggle-insight` — 데이터 프로파일링 및 품질 분석 (Phase 1~3)

## 다음 스킬 (구현 순서)

- [x] `/kaggle-metric` — 인사이트 기반 metric 정의, 평가 기준 설정
  - 타겟 변수 확정, 문제 유형(분류/회귀) 판단
  - 적절한 평가 지표 선정 (accuracy, F1, RMSE 등)
  - 사용자와 논의하여 확정

- [x] `/kaggle-baseline` — baseline 모델 학습 및 목표 metric 설정
  - 최소한의 전처리로 빠른 baseline 구축
  - 현실적으로 달성 가능한 초기 목표값 설정 (낮게 시작)
  - baseline 결과를 기준점으로 저장

- [x] `/kaggle-solve` — 전처리 + 모델링으로 문제 해결
  - 전처리 계획 JSON 기반 자동 적용
  - 선형 + 비선형 모델 최소 1개씩 선정, CV 평가
  - 해석 가능 모델로 피처 인사이트 추출
  - 복수 전처리 계획 시 브랜치 분기 실행

- [x] `/kaggle-evaluate` — 결과 분석 및 개선 방향 도출
  - 오분류 집중 구간 식별 (FN/FP 프로필, 피처 조합별 오분류율)
  - 피처 인사이트와 교차 검증하여 개선 방향 도출
  - solve 재실행 판단 (high/medium이면 재실행, low/수렴이면 확정)

- [x] `/kaggle-autopilot` — 전체 파이프라인 자동 실행
  - insight → metric → baseline → solve↔evaluate 루프 → 완료
  - solve↔evaluate 루프 최대 5회, 수렴 조건 자동 감지
  - 최종 모델은 전체 반복 중 주 평가 지표 최고 iteration 선택
  - 이미 완료된 단계 건너뛰기 (재실행 지원)

## 원칙

- 각 스킬은 독립적으로 실행 가능해야 함
- 스킬 간 데이터 전달은 파일 기반 (JSON/CSV)
- 새 스킬 개발 시 titanic으로 먼저 검증
- 모든 인사이트/결정은 데이터 수치 근거에서만 도출

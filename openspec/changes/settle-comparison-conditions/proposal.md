# Proposal

## Why

`ddi_agent_proposal.md` v0.5의 4장은 조건 B를 "CodeActAgent 그대로 + 같은 런타임 + DSN-DDI 저장소"라고만 적고 있어, 해석이 여러 가지로 갈린다. 이 문장대로라면 B는 관계 설명 파일(SSI-DDI 저장소에만 있음)을 받지 못해 처음부터 틀릴 수밖에 없고, 그러면 비교가 공정하지 않다. 또 C의 `lookup_known`은 테스트셋 정답을 그대로 돌려주기 때문에, "모델 출력을 올바르게 해석했는가"를 잴 수 없게 만든다. 실험 코드를 만들기 전에 탐색 대화에서 확정한 결정을 문서에 반영해야 한다.

## What Changes

- **조건별로 받는 것 명시 (4장)**
  - A: 환경 없음. API로 바로 답함
  - B·C 공통: 환경 ①(코드 실행)과 ②(DSN-DDI, 파이썬 3.7), 가중치 2개, 압축을 푼 데이터, SSI-DDI 설명 파일, 환경 ② 위치 안내 한 줄
  - C에게만: 예측 서버, `ddi` skill, micro agent 프롬프트
  - B를 실행할 때는 `ddi` 패키지와 서버 코드를 컨테이너에 두지 않음
- **BREAKING: `lookup_known` 삭제 (2.3절)**: 에이전트는 정답을 볼 수 없음. 사람용 답변 항목에서 "② 기록된 상호작용"도 삭제 (6.2절)
- **CSV에 `description` 칼럼 추가 (6.2절)**: 약물 방향 오류를 채점하기 위함
- **C′ ablation 삭제 (4장, 8장 #4)**: 하지 않음
- **6.4절 ⚠️ 문단과 8장 #2를 해결됨으로 정리**
- **문서 버전**: v0.5 → v0.6, 변경 내역 추가
- 채점 기준은 그대로 둔다: 원 DSN-DDI 스크립트 실행 결과 (6.3절)

## Capabilities

### New Capabilities
- `comparison-conditions`: 비교 조건 A·B·C가 각각 받는 것과 받지 않는 것, 정답 차단 규칙, 채점용 CSV 형식

### Modified Capabilities
(없음)

## Impact

- `ddi_agent_proposal.md`: 2.3, 4, 6.2, 6.4, 8장과 머리말의 버전·변경 내역
- 앞으로 만들 것: 도커 이미지와 실행 설정(B·C 구분), `ddi` 패키지(`lookup_known` 없음), 채점 스크립트(`description` 비교)

# Proposal

## Why

조건 C(specialist agent)가 B와 다른 점은 domain-specific ACI 하나뿐이다(`comparison-conditions` spec). 그 ACI의 핵심인 예측 서버와 DDI skill(`ddi` 패키지)이 아직 없다. 원 DSN-DDI 스크립트는 테스트셋 전체의 이진 지표만 계산하므로, "이 약물 쌍은 어떤 관계인가"에 답하는 기능이 따로 필요하다. 또 이 연구가 다루는 함정(번호 체계, 약물 방향, 학습셋 밖 약물)을 도구 안에서 처리해야 C가 의미적으로 맞는 결과를 낼 수 있다. 문서 7장 일정의 3~4일 차 작업이다.

## What Changes

- **예측 서버 (환경 ②, 파이썬 3.7)**
  - 가중치 2개(transductive, inductive)를 GPU에 올려두고 localhost HTTP로 요청을 받음
  - 약물 쌍 하나에 대해 86개 관계 점수를 모두 계산해 상위 관계와 확률을 돌려줌
  - 두 약물이 모두 transductive 학습셋(fold0 train)에 있으면 transductive 모델, 아니면 inductive 모델을 씀
  - SMILES 입력(신약)을 받아 원 저장소와 같은 방식으로 분자 그래프를 만듦
- **DDI skill (`ddi` 패키지, 환경 ①에서 import)**
  - `resolve_drug`, `predict`, `predict_many`, `explain`, `save_results` (문서 2.3절, `lookup_known` 없음)
  - `explain`은 `Interaction type == t + 1` 행을 쓰고, `Subject == 2`이면 약물 순서를 뒤집음
  - 가드레일: 모르는 약물 거부, 학습셋 밖 약물이면 inductive 전환 + 경고, 원자 특징 unknown 경고
- **C 전용 이미지**: `ddi-runtime` 위에 서버와 `ddi` 패키지, 약물 이름 사전을 더한 별도 이미지. `ddi-runtime`(B용)에는 아무것도 추가하지 않음
- **약물 이름 사전**: DrugBank Vocabulary (`ferrangoeh/DrugLinker`의 `druglinker/dbvocab.csv`, 13,475개, CC0). 문서에 적힌 `fgh95/DrugLinker`는 이 이름으로 옮겨졌음
- micro agent 프롬프트는 이번 범위가 아님 (OpenHands 연결 change에서 다룸)

## Capabilities

### New Capabilities
- `prediction-server`: 환경 ②에서 DSN-DDI 가중치로 약물 쌍의 관계 점수를 계산해 돌려주는 로컬 서버
- `ddi-skill`: 환경 ①에서 에이전트가 호출하는 DDI 함수 모음 (약물 식별, 예측, 관계 해석, 결과 저장, 가드레일)

### Modified Capabilities
(없음 — `comparison-conditions`의 "ACI는 C에게만" 규칙과 `runtime-image`의 "이미지에 ACI 없음" 규칙을 C 전용 이미지를 따로 만드는 방식으로 지킨다)

## Impact

- 새 코드: `server/` (환경 ②), `ddi/` (환경 ①용 패키지), `docker/Dockerfile.specialist`
- 새 데이터: `dbvocab.csv` (이미지 빌드 때 받음)
- `ddi_agent_proposal.md`: 2.3절 함수 설명, 3.2절 사전 출처 갱신
- 다음 change(OpenHands 연결)가 C 전용 이미지와 `ddi` 패키지를 사용

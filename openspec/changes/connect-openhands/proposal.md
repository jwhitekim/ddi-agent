# Proposal

## Why

B와 C를 실행할 이미지(`ddi-runtime`, `ddi-specialist`)와 C의 도구(예측 서버, `ddi` 패키지)는 준비됐다. 그런데 이것들을 실제 에이전트(OpenHands CodeActAgent)에 연결해 질문 하나를 끝까지 돌려 본 적이 아직 없다. 또 문서가 전제한 OpenHands 구조(CodeActAgent, IPython 셀 실행, AgentSkills 방식 자동 import, micro agent)는 V0의 것인데, V0은 1.0부터 deprecated되었고 이후 제거되었다. 그래서 인용 논문과 같은 구조인 마지막 V0 릴리스로 버전을 고정하고 연결해야 한다. 문서 7장 일정의 5일 차 작업이다.

## What Changes

- **OpenHands `openhands-ai==0.62.0`(마지막 V0, 2025-11-11) 고정**: 호스트에 별도 가상환경으로 설치하고, 헤드리스 모드(`python -m openhands.core.main`)로 CodeActAgent를 실행
- **조건별 실행 설정 (B, C)**
  - 공통: 같은 LLM 설정, 최대 상호작용 턴 10, GPU 사용, 같은 질문 문장과 환경 ② 위치 안내 한 줄
  - B: `ddi-runtime`을 기본 이미지로 사용, 작업 폴더는 비어 있음
  - C: `ddi-specialist`를 기본 이미지로 사용. 작업 폴더에 `.openhands/setup.sh`(예측 서버 시작)와 `.openhands/microagents/`(micro agent 프롬프트)를 둠. 주피터 시작 시 `ddi`가 자동 import됨
- **실행기 `agent/run_agent.py`**: 조건, 질문, 출력 폴더를 받아 작업 폴더와 설정을 만들고, OpenHands를 실행하고, 결과 CSV와 대화 기록(trajectory)을 모음
- **micro agent 프롬프트 작성** (C 전용): `ddi` 함수 사용법과 "모델을 직접 돌리지 말고 `ddi`를 쓸 것"
- **스모크 테스트**: B와 C로 같은 질문을 실제 LLM으로 한 번씩 실행해, 환경·GPU·서버·자동 import·턴 제한·LLM 설정 적용을 확인 (문서 5장 ⚠️ 항목)
- **문서 갱신**: 5장 OpenHands 버전을 "0.62.0 고정"으로, 2.1·2.3절에 V0 고정 이유와 micro agent·setup 방식을 적음

## Capabilities

### New Capabilities
- `agent-runner`: 조건(B, C)과 질문 하나를 받아 OpenHands CodeActAgent를 정해진 설정으로 실행하고 결과를 모으는 실행기

### Modified Capabilities
(없음 — `comparison-conditions`가 정한 조건별 재료를 실행 설정으로 구현한다)

## Impact

- 새 코드: `agent/` (실행기, 조건별 설정 템플릿, C용 setup 스크립트와 micro agent 프롬프트, IPython 시작 파일)
- 호스트: OpenHands 0.62.0 가상환경(파이썬 3.12), Docker
- 외부: Vercel AI Gateway API 키가 필요 (스모크 테스트에 실제 LLM 호출)
- `ddi-draft.md`: 2.1, 2.3, 5장

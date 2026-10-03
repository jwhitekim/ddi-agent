# Spec Delta

## Purpose

조건(B 또는 C)과 질문 하나를 받아 OpenHands CodeActAgent를 정해진 설정으로 실행하고, 결과 CSV와 대화 기록을 모으는 실행기를 정의한다. B와 C는 domain-specific ACI를 제외한 모든 실행 설정이 같아야 한다.

## ADDED Requirements

### Requirement: OpenHands 버전과 에이전트를 고정한다
실행기는 `openhands-ai==0.62.0`의 CodeActAgent를 헤드리스 모드로 실행해야 한다(SHALL). 실행 기록에는 OpenHands 버전이 남아야 한다(SHALL).

#### Scenario: 버전 기록
- **WHEN** 실행이 끝나면
- **THEN** 출력 폴더의 실행 정보에 `openhands-ai 0.62.0`과 `CodeActAgent`가 기록되어 있다

### Requirement: B와 C는 ACI 외의 설정이 같다
B와 C 실행은 같은 LLM 설정(모델, temperature 0.0, 확장 추론 없음), 같은 최대 상호작용 턴(30), 같은 GPU 설정, 같은 질문 문장을 써야 한다(SHALL). 질문 문장 뒤에는 두 조건 모두 같은 환경 ② 위치 안내 한 줄(`/opt/conda/envs/dsn/bin/python`, `/opt/DSN-DDI`)을 붙여야 한다(SHALL). 두 조건의 차이는 기본 이미지(`ddi-runtime` / `ddi-specialist`), 작업 폴더의 `.openhands/` 내용, C 전용 마운트(`ddi` 패키지, 예측 서버 코드)뿐이어야 한다(MUST).

#### Scenario: 설정 비교
- **WHEN** 같은 질문으로 B와 C의 OpenHands 설정 파일과 질문 파일을 만들면
- **THEN** 설정 파일의 차이는 실행 폴더 경로 외에는 기본 이미지와 C 전용 마운트뿐이고, 질문 파일은 같다

### Requirement: 최대 상호작용 턴을 넘기면 실패로 기록한다
실행기는 `max_iterations = 30`으로 실행해야 한다(SHALL). 턴 제한에 걸려 끝나면 실행 정보에 턴 초과 실패로 기록해야 한다(SHALL).

#### Scenario: 턴 초과
- **WHEN** 에이전트가 30턴 안에 끝내지 못하면
- **THEN** 실행 정보의 종료 상태가 턴 초과로 기록된다

### Requirement: C는 시작할 때 도구가 준비된다
C 실행에서는 에이전트의 첫 행동 전에 예측 서버가 떠 있어야 하고(SHALL), 주피터 커널에 `ddi`가 import되어 있어야 하며(SHALL), micro agent 프롬프트가 에이전트에게 전달되어야 한다(SHALL).

#### Scenario: C의 첫 셀
- **WHEN** C의 에이전트가 IPython 셀에서 `ddi.predict("Warfarin", "Aspirin")`을 실행하면
- **THEN** import 없이 바로 관계 5의 문장이 돌아온다

### Requirement: B에는 ACI가 없다
B 실행의 컨테이너에는 예측 서버, `ddi` 패키지, micro agent 프롬프트가 없어야 한다(MUST NOT). B도 환경 ②와 GPU는 쓸 수 있어야 한다(SHALL).

#### Scenario: B 컨테이너 확인
- **WHEN** B 실행 중 컨테이너에서 `import ddi`, 서버 포트, `.openhands/microagents`를 확인하면
- **THEN** 셋 다 없고, `/opt/conda/envs/dsn/bin/python -c "import torch; print(torch.cuda.is_available())"`는 `True`를 출력한다

### Requirement: 결과와 기록을 출력 폴더에 모은다
실행기는 실행마다 출력 폴더에 대화 기록(trajectory), 에이전트가 작업 폴더에 저장한 결과 CSV(있다면), 실행 정보(조건, 질문, 버전, 종료 상태, 상호작용 턴 수, 걸린 시간, 토큰 사용량)를 남겨야 한다(SHALL).

#### Scenario: 실행 산출물
- **WHEN** 질문 하나를 실행하면
- **THEN** 출력 폴더에 trajectory 파일, 실행 정보 JSON, (에이전트가 저장했다면) 결과 CSV가 있다

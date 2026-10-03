# Tasks

## 1. OpenHands 설치

- [x] 1.1 `uv venv -p 3.12 .venv-openhands`에 `openhands-ai==0.62.0`을 설치하고(런타임 빌드가 소스 폴더 구조를 요구하므로 sdist를 `.venv-openhands/src/`에 풀어 editable 설치, 사전 릴리스 의존성 `openhands-{agent-server,sdk,tools}==1.0.0a6` 명시), 설치된 패키지 목록을 `agent/requirements.lock.txt`로 저장한다(`.venv-openhands/`는 `.gitignore`에 추가). 확인: `.venv-openhands/bin/python -c "import openhands, importlib.metadata as m; print(m.version('openhands-ai'))"`가 `0.62.0`을 출력한다

## 2. 조건별 설정과 작업 폴더

- [x] 2.1 `agent/config.toml.j2`(공통: LLM, `max_iterations=30`(처음 10에서 스모크 테스트 후 30으로 변경), `enable_gpu=true`, 브라우징·MCP 끔, 작업 폴더와 DrugBank 약물 사전 마운트, `save_trajectory_path`)와 조건별 값(B: `base_container_image="ddi-runtime"`, C: `"ddi-specialist"` + 현재 `ddi/`·`server/` 읽기 전용 마운트)을 만든다. 확인: 같은 질문으로 만든 B·C 설정 파일의 `diff`가 실행 폴더 경로 외에는 기본 이미지와 C 전용 마운트뿐이다
- [x] 2.2 C 준비물을 만든다: `ddi`가 import될 때 예측 서버를 백그라운드로 띄우고 첫 요청 때 준비를 기다리는 기능(이미지의 IPython 시작 파일이 커널 시작 시 `import ddi` — setup.sh는 헤드리스 모드에서 실행되지 않아 대체)과 `agent/c_workspace/.openhands/microagents/ddi.md`(repo 타입, `ddi` 함수 사용법, 모델을 직접 실행하지 말 것, `save_results`로 CSV 저장). 확인: micro agent 파일의 frontmatter를 OpenHands 0.62.0의 `BaseMicroagent.load`로 읽으면 repo 타입으로 파싱된다
- [x] 2.3 질문 문장 뒤에 붙일 공통 안내(환경 ② 위치, `/workspace`에 CSV 저장, 칼럼 `drug_a, drug_b, relation, prob, model_used, description`)를 `agent/task_suffix.txt`로 만든다. 확인: B·C의 질문 파일이 바이트 단위로 같다

## 3. 실행기

- [x] 3.1 `agent/run_agent.py --condition {B,C} --task "<질문>" --out <폴더>`를 만든다: 작업 폴더 생성(C는 `c_workspace` 복사), 설정·질문 파일 생성, OpenHands 헤드리스 실행, 결과 CSV·trajectory 수집, `run_info.json`(조건, 질문, 버전, 종료 상태, 턴 수, 시간, 토큰) 저장. 확인: 아래 스모크 테스트에서 산출물 3종이 생긴다

## 4. 스모크 테스트 (실제 LLM, `AI_GATEWAY_API_KEY` 필요)

- [x] 4.1 C로 "Warfarin이랑 Aspirin 상호작용 예측해줘"를 실행한다. 확인: trajectory에서 import 없이 `ddi` 호출, micro agent 적용이 보이고, 결과 CSV 1행 이상에 관계 5와 방향이 맞는 문장이 있으며, 턴 제한 안에 끝난다
- [x] 4.2 B로 같은 질문을 실행한다. 확인: 컨테이너에 `ddi`·서버·micro agent가 없고, 환경 ② 파이썬에서 `torch.cuda.is_available()`이 `True`이며, 종료 상태와 턴 수가 `run_info.json`에 기록된다 (B의 정답 여부는 상관없음)
- [x] 4.3 LLM 설정 적용을 확인한다: trajectory/게이트웨이 응답에서 모델 이름, temperature 0.0, 추론 강도, 캐시 사용 여부를 확인해 기록한다. 확인: `agent/SMOKE_TEST.md`에 두 실행의 결과, 턴 수, 토큰, 시간과 네 가지 설정의 적용 여부가 적혀 있다

## 5. 문서 반영

- [x] 5.1 `ddi-draft.md` 5장 OpenHands 버전을 "0.62.0(마지막 V0) 고정"으로 바꾸고 이유(V0 제거, 인용 논문 구조)를 적는다. 2.1·2.3절에 micro agent·setup 스크립트·IPython 시작 파일 방식을 적고, 5장 ⚠️ 스모크 테스트 항목에 4.3 결과를 반영한다. 확인: `grep -n "0.62.0" ddi-draft.md`가 5장과 2.1절에서 보인다

# Design

## Context

- OpenHands V0(CodeActAgent, IPython, AgentSkills, micro agent)은 1.0부터 deprecated되었고 이후 제거되었다. 마지막 V0 릴리스는 `openhands-ai 0.62.0`(2025-11-11, 파이썬 `>=3.12,<3.14`, litellm `>=1.74.3,<1.78`)이다. 연구 문서와 인용 논문(OpenHands ICLR 2025, CodeAct)이 이 구조를 전제한다.
- 0.62.0 소스에서 확인한 것:
  - `[sandbox]`: `base_container_image`, `enable_gpu`, `cuda_visible_devices`, `runtime_extra_deps`(런타임 이미지 마지막에 openhands 사용자로 `RUN`, 단 이미지 태그 계산에 들어가지 않음), `runtime_startup_env_vars`, `volumes`(쉼표로 여러 개), `use_host_network`
  - 런타임 이미지: 기본 이미지 위에 apt `python3`, micromamba 환경 `openhands`(poetry, 주피터), 실행 서버를 설치한다(환경 ①). `ENV PATH="/usr/bin:/bin:..."`를 앞에 붙여서, 우리 이미지의 `PATH=/opt/conda/envs/dsn/bin:...` 설정보다 시스템 파이썬이 먼저 잡힌다.
  - 저장소를 고르지 않으면, 작업 폴더의 `.openhands/microagents/`에서 micro agent를 읽는다. `.openhands/setup.sh`는 헤드리스 모드에서 저장소를 지정했을 때만 실행된다.
  - 헤드리스: `python -m openhands.core.main --config-file <toml> -f <task file> -c CodeActAgent -i 30` (실행기는 같은 모듈을 `agent/oh_main.py`를 통해 실행). 대화 기록은 `save_trajectory_path`로 저장한다.
- 호스트: 파이썬 3.13.7, `uv` 있음, V100 2장, nvidia-container-toolkit.

## Goals / Non-Goals

**Goals:**
- B와 C가 같은 실행기, 같은 설정 틀로 돌아가고, 차이는 ACI뿐
- 질문 하나를 실행해 결과 CSV와 trajectory를 얻는 흐름을 끝까지 확인

**Non-Goals:**
- 질문 세트, 정답 생성, 채점 (다음 change)
- A 조건 스크립트 (질문 세트 change)
- 교차 검증 모델(GPT) 연결 (실행 단계에서 설정만 바꿔 사용)

## Decisions

- **OpenHands는 호스트의 별도 가상환경에 소스(sdist)로 설치한다.** `uv venv -p 3.12 .venv-openhands`를 만들고, 0.62.0 sdist를 `.venv-openhands/src/`에 풀어 editable로 설치한다. OpenHands가 호스트 Docker로 런타임 컨테이너를 띄운다.
  - 이유: 런타임 이미지를 빌드할 때 `openhands/` 옆의 `microagents/`, `pyproject.toml`, `poetry.lock`을 복사하는데, wheel 설치본에는 이 파일들이 없어 빌드가 실패한다(구현 중 확인).
  - 0.62.0은 사전 릴리스 `openhands-agent-server/sdk/tools==1.0.0a6`에 의존하므로, 이 세 패키지를 명시해서 설치한다.
- **조건별 설정은 템플릿 하나에서 만든다.** `agent/config.toml.j2`에 공통 값(LLM, `max_iterations=30`, `enable_gpu=true`, `run_as_openhands`, `volumes`)을 두고, 조건별로 `base_container_image`와 C 전용 줄만 바꾼다. 이렇게 하면 "차이는 ACI뿐"이라는 점을 설정 파일 비교로 확인할 수 있다.
- **LLM은 Vercel AI Gateway의 OpenAI 호환 엔드포인트로 부른다.** litellm `<1.78`이 새 모델 이름을 모를 수 있다. 그래서 `model = "openai/anthropic/claude-sonnet-5.5"`, `base_url = "https://ai-gateway.vercel.sh/v1"`, `api_key = $AI_GATEWAY_API_KEY`로 둔다. temperature, 추론 강도, 캐싱이 실제로 적용되는지는 스모크 테스트에서 게이트웨이 응답과 사용량으로 확인한다(문서 5장 ⚠️).
- **작업 폴더는 실행마다 새로 만들어 `/workspace`로 마운트한다.** B는 빈 폴더다. C는 `.openhands/microagents/ddi.md`를 둔다. 에이전트가 저장한 CSV는 이 폴더에서 가져온다.
- **C의 예측 서버는 `ddi`가 import될 때 띄운다.** C 런타임 이미지에는 처음 빌드 때 넣은 IPython 시작 파일(`~/.ipython/profile_default/startup/00-ddi.py`: `/opt/ddi-skill`을 경로에 넣고 `import ddi`)이 있다. 주피터 커널이 시작될 때 이 파일이 `import ddi`를 하고, `ddi`는 import될 때 서버가 없으면 `/opt/ddi-server/app.py`를 환경 ② 파이썬으로 백그라운드 실행한다. 기다리지는 않고, 첫 요청 때 서버가 준비될 때까지(최대 180초) 기다린다. 서버 파일이 없는 환경(예: B, 일반 파이썬)에서는 아무것도 하지 않는다.
  - 처음 계획은 `.openhands/setup.sh`였다. 그런데 0.62.0 헤드리스 모드(`core/main.py`)는 `sandbox.selected_repo`가 있을 때만 setup 스크립트를 실행해서 서버가 뜨지 않았다(Gemini 첫 스모크 테스트에서 확인). `ddi-specialist`의 `CMD`도 OpenHands가 시작 명령을 바꾸므로 쓰이지 않는다.
  - import 시점에 서버 준비까지 기다리게 했더니, 커널 시작이 막혀 OpenHands 런타임이 커널 연결 시간 초과로 시작되지 않았다. 그래서 띄우기만 하고, 기다림은 첫 요청으로 미뤘다.
  - 검토한 대안: `IPYTHONDIR` 환경 변수로 시작 파일 폴더를 바꾸기. 변수는 커널까지 전달됐지만, 커널은 여전히 `~/.ipython`을 프로필로 써서 효과가 없었다.
- **C는 현재 `ddi/`와 `server/` 폴더를 읽기 전용으로 마운트한다 (`/opt/ddi-skill/ddi`, `/opt/ddi-server`).** OpenHands 0.62.0은 런타임 이미지 태그를 기본 이미지 이름과 소스 해시로 정하고, `runtime_extra_deps`나 기본 이미지 내용이 바뀌어도 태그가 같으면 옛 런타임을 재사용한다(구현 중 확인). 이미지에 굳어진 옛 코드 대신 항상 현재 코드를 쓰고, 런타임 재빌드(약 1시간)를 피하려고 마운트한다. `runtime_extra_deps`는 쓰지 않는다.
- **DrugBank 약물 이름 사전은 B·C 공통 재료다.** DSN-DDI 데이터에는 약물 이름이 없어서, 사전이 없으면 B는 질문의 "Warfarin"을 ID로 바꾸지 못해 식별 단계에서 막힌다(Gemini B 스모크 테스트에서 확인). 설명 파일과 같은 이유로 B·C 모두에게 `/opt/DSN-DDI/drugbank_vocabulary.csv`를 준다. `docker/Dockerfile`에도 넣고, 이미 만든 런타임에 반영되도록 공통 설정에서 같은 경로로 읽기 전용 마운트한다.
- **micro agent는 항상 켜지는 repo 타입 하나로 둔다.** `.openhands/microagents/ddi.md`에 `ddi` 함수 5개의 사용법, "모델을 직접 실행하지 말고 `ddi`를 쓸 것", 결과는 `save_results`로 CSV에 저장할 것을 적는다. 관계 번호 해석 규칙(`t+1`, Subject)은 적지 않는다. 그 규칙은 `explain` 안에 들어 있다.
- **함수 호출 모드를 강제한다 (`native_tool_calling = true`, B·C 공통).** 0.62.0은 모델 이름으로 함수 호출 지원 여부를 판단하는데, `openai/anthropic/claude-sonnet-5.5`를 몰라 텍스트 도구 호출 모드로 돌아갔다. 그러자 Sonnet이 자기 형식(`<invoke>`)으로 도구 호출을 글로 써서 C는 출력 토큰을 낭비하고 B는 반복 감지로 중단됐다(Sonnet 스모크 테스트에서 확인).
- **확장 추론은 쓰지 않는다.** litellm 1.77.7은 Sonnet 5.5의 `reasoning_effort`를 지원하지 않아 OpenHands가 조용히 빼고, 강제로 보내도 추론 토큰이 0이었다. 설정만 남기면 "Low로 돌렸다"고 오해할 수 있어 설정에서 뺐다(사용자 결정).
- **프롬프트 캐싱은 게이트웨이 자동 캐싱으로 켠다 (`agent/oh_main.py`).** 0.62.0은 캐싱 대상 모델 목록이 `claude-sonnet-4*`까지라 Sonnet 5.5에 캐시 표시를 붙이지 않고, litellm 프록시가 아니면 `extra_body`도 지운다. 게이트웨이의 OpenAI 호환 API는 `providerOptions.gateway.caching = "auto"`를 주면 캐시 표시를 직접 붙이므로, 진입 파일이 OpenHands의 litellm 호출을 감싸 게이트웨이 요청에만 이 옵션을 넣는다. OpenHands 소스를 고치면 런타임 이미지가 다시 빌드되므로 소스는 그대로 둔다. 캐싱은 비용·속도에만 영향을 준다.
  - 검토한 대안: OpenHands의 캐싱 목록에 `claude-sonnet-5*` 추가. OpenHands는 메시지 내용 조각에 `cache_control`을 붙이는데 게이트웨이를 거치며 효과가 없었다.
- **환경 ② 위치 안내 한 줄은 질문 문장 뒤에 붙인다 (B와 C 같음).** 예: "참고: DSN-DDI 저장소는 /opt/DSN-DDI, 그 실행용 파이썬은 /opt/conda/envs/dsn/bin/python 에 있습니다. 결과는 /workspace 에 CSV로 저장하세요." CSV 저장 안내도 두 조건에 똑같이 들어간다.
- **실행 정보는 trajectory에서 뽑는다.** 종료 상태(완료, 턴 초과, 에러), 상호작용 턴 수, 걸린 시간, 토큰 사용량(trajectory의 llm_metrics)을 `run_info.json`에 저장한다.

## Risks / Trade-offs

- [0.62.0은 더 이상 지원되지 않아 의존성 설치나 런타임 이미지 빌드가 깨질 수 있음] → 설치한 패키지 목록을 고정해 기록한다. 빌드가 실패하면 원인을 보고하고 멈춘다
- [OpenHands 런타임 빌드가 Ubuntu 22.04 기본 이미지에서 실패할 수 있음] → 런타임 Dockerfile 템플릿은 Debian/Ubuntu를 지원한다. 실패하면 로그를 보고 기본 이미지 조정을 제안한다
- [서버가 모델을 올리는 데 약 20초 걸림] → 커널 시작 때 서버를 띄우므로 보통 에이전트의 첫 LLM 응답 동안 준비된다. 아니면 첫 `ddi` 호출이 준비될 때까지 기다린다
- [마운트에 의존하므로, 마운트 없이 `ddi-specialist`만 쓰면 이미지에 굳어진 옛 `ddi`가 쓰임] → 실험은 항상 `run_agent.py`로 실행한다. 이미지를 다시 빌드하면 이 차이는 없어진다
- [B의 턴이 빠듯했음: Gemini·Sonnet B 스모크 테스트 모두 10턴을 다 씀(Gemini는 10턴 중 4턴을 작업 계획 도구에 사용)] → **최대 턴을 B·C 모두 30으로 늘림**(사용자 결정). B가 턴이 모자라 결과를 못 내면 정확성을 비교할 수 없기 때문. C는 3~6턴이라 영향이 거의 없음. 실제 쓴 턴 수는 효율 지표로 보고
- [Vercel AI Gateway에서 temperature나 추론 강도가 무시될 수 있음] → 스모크 테스트에서 확인해 문서 5장에 기록한다
- [B가 질문 문장의 CSV 저장 안내 때문에 C와 다른 칼럼으로 저장할 수 있음] → 칼럼 이름 안내는 두 조건 모두에 같은 문장으로 넣는다. 형식이 다른 것은 채점 단계에서 처리한다

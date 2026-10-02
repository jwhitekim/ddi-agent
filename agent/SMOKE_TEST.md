# 스모크 테스트 기록

기록일: 2026-10-01 · OpenHands `openhands-ai 0.62.0` CodeActAgent · 질문: "Warfarin이랑 Aspirin 상호작용 예측해줘"

> ⚠️ 주력 모델(Vercel AI Gateway `anthropic/claude-sonnet-5.5`)의 API 키가 아직 없어서, 임시로 `gemini/gemini-3.5-flash`(Google AI Studio 키, 직접 호출)로 실행했다. 연결 흐름은 모델과 무관하게 확인됐지만, LLM 설정 적용 여부(아래 3절)는 Sonnet 5.5로 다시 확인해야 한다.

## 1. 실행 명령

```bash
.venv-openhands/bin/python agent/run_agent.py --condition C \
    --task "Warfarin이랑 Aspirin 상호작용 예측해줘" --out runs/smoke_C \
    --model gemini/gemini-3.5-flash --base-url "" --api-key-env GEMINI_API_KEY
# B 는 --condition B --out runs/smoke_B
```

사전 점검(LLM 없이 런타임만): `agent/check_runtime.py --condition {B,C}`

## 2. 결과

| | C (specialist) | B (generalist) |
|---|---|---|
| 종료 상태 | `finished` | `max_iterations` (10턴 초과) |
| 상호작용 턴 | 6 | 10 |
| 걸린 시간 | 81.6초 | 96.8초 |
| 토큰 (입력 / 캐시 읽기 / 출력) | 57,398 / 24,418 / 2,008 | 111,350 / 65,092 / 1,769 |
| 비용 (litellm 집계) | $0.071 | $0.095 |
| 결과 CSV | `result.csv` (상위 3개) | 없음 |

**C 결과 CSV**

| drug_a | drug_b | relation | prob | model_used | description |
|---|---|---|---|---|---|
| DB00682 | DB00945 | 5 | 0.9979 | transductive | Acetylsalicylic acid may increase the anticoagulant activities of Warfarin. |
| DB00682 | DB00945 | 72 | 0.9687 | transductive | The serum concentration of Warfarin can be increased when it is combined with Acetylsalicylic acid. |
| DB00682 | DB00945 | 65 | 0.9393 | transductive | The risk or severity of bleeding can be increased when Warfarin is combined with Acetylsalicylic acid. |

**C 행동:** 작업 폴더 확인 → `ddi.predict("Warfarin", "Aspirin")` → `ddi.save_results(...)` → CSV 확인 → 요약 후 종료. micro agent 안내대로 움직였고 모델을 직접 실행하지 않았다.

**B 행동:** `/opt/DSN-DDI` 탐색, README·설명 파일 읽기, DrugBank 약물 사전에서 Warfarin·Aspirin 검색 → 추론 스크립트 작성 전에 10턴 초과. 10턴 중 4턴을 작업 계획 도구(`task_tracking`)에 썼다.

**환경 점검 (`check_runtime.py`)**

| 항목 | C | B |
|---|---|---|
| IPython에 `ddi` 미리 import | 있음 (첫 호출에서 관계 5) | 없음 (`NameError`) |
| 예측 서버 | 커널 시작 시 기동, 모델 2개, `cuda:0` | 없음 |
| micro agent | `.openhands/microagents/ddi.md` | 없음 |
| `/opt/ddi-skill`, `/opt/ddi-server` | 있음 (현재 코드 마운트) | 없음 |
| 환경 ② GPU | `torch.cuda.is_available()` = True | True |
| 환경 ① 파이썬 (터미널) | OpenHands Python 3.12 | 같음 |
| 설명 파일, DrugBank 약물 사전 | 있음 | 있음 |

## 3. LLM 설정 적용 확인 (Gemini 기준)

| 설정 | 결과 |
|---|---|
| 모델 | `gemini/gemini-3.5-flash` 호출 확인 (litellm 1.77.7, 함수 호출 지원) |
| temperature 0.0 | 설정은 전달됨. 그러나 **같은 요청을 두 번 보내면 temperature 0.0에서도 답이 달랐다** (생각 기능이 있는 모델의 비결정성으로 보임) → 실험 결과가 실행마다 다를 수 있음 |
| 추론 강도 `low` | 적용되는 것으로 보임 (같은 요청에서 출력 토큰 90 → 60) |
| 캐싱 | 적용됨 (C 입력의 43%, B 입력의 58%가 캐시 읽기) |

**Sonnet 5.5로 다시 확인할 것:** 모델 이름, temperature 0.0에서의 결정성, 추론 강도, 캐싱(Vercel AI Gateway 경유).

## 4. 구현 중 발견하고 고친 것

1. OpenHands 0.62.0은 wheel 설치본으로는 런타임 이미지를 빌드하지 못함 → sdist를 풀어 editable 설치
2. 헤드리스 모드는 저장소를 지정하지 않으면 `.openhands/setup.sh`를 실행하지 않음 → `ddi`가 import될 때 예측 서버를 띄우도록 변경 (첫 C 실행은 서버가 없어서 10턴 초과)
3. import 시점에 서버 준비를 기다리면 커널 시작이 막혀 런타임이 뜨지 않음 → 띄우기만 하고 첫 요청 때 기다림
4. 런타임 이미지 태그가 `runtime_extra_deps`와 기본 이미지 내용을 반영하지 않아 옛 런타임이 재사용됨 → C는 현재 `ddi/`·`server/`를 마운트
5. B가 약물 이름을 ID로 바꿀 방법이 없음 → DrugBank 약물 사전을 B·C 공통 재료로 추가 (이미지 + 마운트)

## 5. 남은 결정

- **B의 10턴:** 작업 계획 도구가 턴을 많이 씀. 도구를 끌지(B·C 모두), 턴 수를 늘릴지, 그대로 둘지 정해야 함
- **비결정성:** temperature 0.0에서도 결과가 달라질 수 있으면, 질문마다 여러 번 실행할지 정해야 함

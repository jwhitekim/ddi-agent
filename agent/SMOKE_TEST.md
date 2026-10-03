# 스모크 테스트 기록

기록일: 2026-10-01 · OpenHands `openhands-ai 0.62.0` CodeActAgent · 질문: "Warfarin이랑 Aspirin 상호작용 예측해줘"

처음에는 Vercel 키가 없어 임시로 `gemini/gemini-3.5-flash`로 연결 흐름을 확인했고(2~3절), 이후 주력 모델 `anthropic/claude-sonnet-5.5`(Vercel AI Gateway)로 다시 실행했다(6절).

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

## 3. LLM 설정 적용 확인 (Gemini 기준, 참고용)

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

## 6. Sonnet 5.5 (Vercel AI Gateway, 주력 모델)

설정(처음 실행 시): `model = "openai/anthropic/claude-sonnet-5.5"`, `base_url = "https://ai-gateway.vercel.sh/v1"`, temperature 0.0, `reasoning_effort = "low"`, `caching_prompt = true`, `native_tool_calling = true`

| | C | B |
|---|---|---|
| 종료 상태 | `finished` | `max_iterations` (CSV는 저장함) |
| 상호작용 턴 | 3 | 10 |
| 걸린 시간 | 62.6초 | 128.9초 |
| 토큰 (입력 / 캐시 읽기 / 출력) | 47,695 / 0 / 1,328 | 256,715 / 0 / 5,118 |
| 결과 | 관계 5·72·65, 방향 정답 | 관계 번호는 맞지만 **방향이 뒤집힌 문장** |

**B의 결과 (가설한 오류가 실제로 나옴)**

| 관계 | B의 문장 | 올바른 문장 |
|---|---|---|
| 5 | Warfarin may increase the anticoagulant activities of Aspirin. ✗ | Acetylsalicylic acid may increase the anticoagulant activities of Warfarin. |
| 72 | The serum concentration of Aspirin can be increased when it is combined with Warfarin. ✗ | The serum concentration of Warfarin can be increased when it is combined with Acetylsalicylic acid. |
| 65 | The risk or severity of bleeding can be increased when Warfarin is combined with Aspirin. ✓ | (대칭 관계) |

- B는 `Subject` 칸을 무시하고 #Drug1에 늘 첫 약물을 넣었다 → 표 1의 "잘못된 해석 ②(방향 무시)". 에러 없이 그럴듯한 CSV를 냈다.
- B의 확률(관계 5: 0.99750)이 C(0.99787)와 조금 다르다 → 여러 쌍을 묶어 계산한 배치 섞임으로 보임.
- B는 두 순서(Warfarin–Aspirin, Aspirin–Warfarin)를 모두 계산해 저장했다.

**LLM 설정 적용 확인 (Sonnet 5.5)**

| 설정 | 결과 |
|---|---|
| 모델 | 응답 모델 `anthropic/claude-sonnet-5.5` 확인 |
| 함수 호출 | 0.62.0이 모델 이름을 몰라 텍스트 도구 호출 모드로 돌아감 → Sonnet이 `<invoke>` 형식 글을 써서 C는 출력 48,665토큰을 낭비하고, B는 반복 감지로 중단됨. `native_tool_calling = true`로 해결 |
| temperature 0.0 | 전달됨. 같은 요청 3번 중 2번 같은 답 (Gemini보다 일관되지만 완전히 결정적이지는 않음) |
| 추론 강도 `low` | **적용되지 않음.** litellm 1.77.7이 이 모델의 `reasoning_effort`를 지원하지 않아 거부하고, OpenHands는 `drop_params`로 조용히 뺀다. 강제로 보내도(`allowed_openai_params`, `extra_body.reasoning`) 추론 토큰이 0 → 사실상 확장 추론 없이 동작 |
| 캐싱 | **적용되지 않음** (캐시 읽기 0). 0.62.0의 캐싱 대상 모델 목록이 `claude-sonnet-4*`까지라 `cache_control`을 붙이지 않는다 |

**결정과 조치 (2026-10-03)**
- 추론 강도: **확장 추론 없음**으로 확정. 설정 파일에서 `reasoning_effort`를 뺐다
- 캐싱: **켬.** 게이트웨이의 OpenAI 호환 API에 `providerOptions.gateway.caching = "auto"`를 주면 캐시가 동작함을 확인했다(1만 토큰 요청 두 번: 두 번째에 10,223토큰 캐시 읽기). OpenHands는 litellm 프록시가 아니면 `extra_body`를 지우므로, `agent/oh_main.py`가 OpenHands의 litellm 호출을 감싸 게이트웨이 요청에만 이 옵션을 넣는다(OpenHands 소스는 그대로). 메시지에 `cache_control`을 직접 붙이는 방식은 litellm을 거치며 효과가 없었다
- 캐싱 적용 후 C 재실행: `finished`, 3턴, 63.2초, 입력 48,168 중 **캐시 읽기 35,724 (74%)**, 결과 동일(관계 5·72·65, 방향 정답)
- temperature 0.0의 비결정성: 원래 LLM에 있는 성질이라 별도 대응하지 않기로 함

## 7. 최대 턴 30으로 변경 후 B 재실행 (Sonnet 5.5, 캐싱 켬)

최대 턴을 B·C 모두 10 → 30으로 늘렸다(B가 10턴 안에 결과를 마무리하지 못해서, 사용자 결정).

| | B (30턴) |
|---|---|
| 종료 상태 | `finished` (스스로 종료) |
| 상호작용 턴 | 13 |
| 걸린 시간 | 380.7초 |
| 토큰 (입력 / 캐시 읽기 / 출력) | 1,132,526 / 1,088,288 (96%) / 30,220 |

**B의 결과 (세 가지 오류, 모두 에러 없이 그럴듯한 CSV)**

| B의 행 | 문제 |
|---|---|
| `model_used = inductive` | 두 약물 모두 학습셋에 있는데 inductive 모델 사용 |
| 81, "Warfarin may increase the thrombogenic activities of Aspirin." (1위) | 정답 1위(관계 5)와 다름 |
| 6, "Warfarin may increase the anticoagulant activities of Aspirin." | 항응고 관계를 DSN-DDI 번호 5가 아니라 설명 파일의 `Interaction type`(6)으로 적음(1칸 밀림) + 방향 뒤집힘 |

- 10턴 실행 때와 오류 양상이 달랐다 → B 쪽 비결정성이 큼
- 질문 하나에 입력 약 113만 토큰. 본 실험 전에 비용을 어림할 필요가 있음

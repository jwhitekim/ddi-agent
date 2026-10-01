# DSN-DDI 과학 에이전트 — 실험 설정 (초안 v0.5)

작성일: 2026-09-30 · 목표 기간: 2주

> ✅ = 합의됨 · ⚠️ = 확인 필요 · ❓ = 아직 안 정함
>
> v0.5 변경: 4편 원문(SWE-agent, CodeAct, OpenHands, Zero-shot Planner) 대조로 용어 점검 — ACI 구성 요소를 SWE-agent 원어(commands, documentation, environment feedback, guardrails)로 교체, "행동 공간·관찰 공간 재설계" 표현 삭제, "스텝" → "상호작용 턴", "semantic error" → "semantically incorrect", 용어 점검표(0.2) 추가
>
> v0.4 변경: OpenHands·Zero-shot Planner 논문의 용어로 통일 — 범용/제안 에이전트 → **generalist / specialist agent**, (가)/(나) → **실행 가능성(executability) / 정확성(correctness)**, 함수 라이브러리 → OpenHands **AgentSkills**, 명령 문서 → **micro agent** 프롬프트. 용어집(0장) 추가
>
> v0.3 변경: "도메인 인터페이스(도구 + 지침)" → **domain-specific ACI** (행동 공간·관찰 공간 재설계), 참고문헌 추가
>
> v0.2 변경: 대상 사용자를 일반인 → 인접 분야 연구자로 변경, AI for Science 프레이밍, "서비스층" → 도메인 인터페이스(ACI), 작업 유형 4종, 결과 CSV 채점, 안전성 지표 축소, 관계 대응표 86종 완성 반영

---

## 0. 용어집 (에이전트 분야 표현)

### 0.1 용어 대응

| 이전 표현 | 논문에서 쓸 표현 | 출처 |
|---|---|---|
| 범용 에이전트 | **generalist agent** (예: CodeActAgent) | OpenHands — "generalist and specialist AI agents" |
| 제안 에이전트 / 전문 에이전트 | **specialist agent** — generalist agent의 구현을 재사용하고 특정 작업에 특화 | OpenHands — "micro agent ... specialized towards a particular task" |
| 모델을 돌리는 작업 | 에이전트가 **환경(environment)** 을 **관찰(observation)** 하고 **행동(action)** 을 생성 | OpenHands 2.1 |
| 코드 실행 방식 | **통합 행동 공간(unified action space)** — 실행 가능한 코드 행동(CodeAct) | CodeAct 초록, OpenHands 2.1 |
| 스텝 | **상호작용 턴(interaction turn)** | CodeAct 2.3 (최대 10턴 설정) |
| 에러 메시지·실행 결과 | **자동 피드백(automated feedback)** / **환경 피드백(environment feedback)** | CodeAct 표 1, SWE-agent 2장 |
| 스스로 에러를 고침 | **self-debug** | CodeAct 1장 |
| 같은 LLM으로 비교 | **고정된 LM(fixed LM)을 두고 ACI를 설계** | SWE-agent 2장 |
| 도커 환경 | **런타임(runtime)** / **샌드박스(sandbox)** | OpenHands 2.2 |
| 함수 라이브러리 | **AgentSkills** 형태의 도메인 skill — IPython 환경에 자동 import, `IPythonRunCellAction`으로 호출 | OpenHands 2.3 |
| 명령 문서(지침) | **micro agent**의 특화 프롬프트 | OpenHands 3 |
| domain-specific ACI | 동일 — "carefully crafted ACI (specialized tools for particular tasks)" | SWE-agent, OpenHands 2.3 |
| (가) 실행 장애 | **실행 가능성(executability)** 실패 | Zero-shot Planner 2.2 |
| (나) 결과 해석 오류 | **정확성(correctness)** 실패 / **의미적으로 틀린(semantically incorrect)** 출력 | Zero-shot Planner 2.2 ("semantic correctness") |
| 파이프라인 고유의 사실 | **암묵적 규약(implicit conventions)** — ⚠️ 4편 어디에도 없는 이 연구의 용어. 처음 쓸 때 정의 필요 | (신규) |
| 모델 출력을 올바른 뜻으로 연결 | **그라운딩(grounding)** — ⚠️ 원 논문은 "고수준 작업을 허용 행동에 연결"하는 뜻. 이 연구의 "출력을 파이프라인 규약에 연결"은 확장된 용법이라 처음 쓸 때 정의 필요 | Zero-shot Planner 초록 |

**Zero-shot Planner와의 대응 (논문 논리의 뼈대)**
- Zero-shot Planner: LLM이 만든 계획은 **그럴듯하지만(correct) 실행되지 않는다(not executable)** → 허용 행동(admissible actions)으로 번역해 실행 가능성을 높임
- 이 연구: generalist agent가 만든 결과는 **실행되지만(executable) 의미가 틀릴 수 있다(not correct)** → domain-specific ACI로 파이프라인 규약에 그라운딩해 정확성을 높임
- 즉 같은 두 축(executability, correctness)을 쓰되, **문제가 반대쪽 축에서 발생**한다는 점이 차별점

**OpenHands와의 대응**
- OpenHands 스스로 "generalist와 specialist 에이전트 모두를 위한 플랫폼"이라고 밝힘 → 이 연구는 그 위에서 과학 파이프라인용 specialist agent를 구현
- AgentSkills의 포함 기준: "(1) LLM이 코드를 직접 짜서 하기 어려운 것, (2) 외부 모델을 호출하는 것" → DDI skill은 **두 기준을 모두 충족** (파이프라인 규약은 LLM이 알 수 없고, DSN-DDI는 외부 모델)

### 0.2 원문 대조 점검표 (v0.5)

| 문서에서 쓰던 표현 | 원문 확인 결과 | 조치 |
|---|---|---|
| domain-specific ACI | SWE-agent는 "custom ACI", "ACIs tailored specifically for LMs"라고 씀. "domain-specific ACI"는 원문에 없는 조합 | 유지 — 이 연구의 명칭으로 정의하고 SWE-agent 인용 |
| ACI 구성 = 행동 공간·관찰 공간·행동 제약·도메인 지식 주입 | SWE-agent 원어는 **commands(actions), documentation, environment feedback, guardrails**. "관찰 공간·행동 제약·도메인 지식 주입"은 원문에 없음 | **교체** — SWE-agent 원어 사용 (2.3) |
| "행동 공간과 관찰 공간의 재설계" | SWE-agent: "we shape the actions, their documentation, and environment feedback" | **교체** — "행동·문서·환경 피드백을 설계" |
| generalist / specialist agent | OpenHands 원문 그대로 | 유지 |
| micro agent, AgentSkills | OpenHands 원문 그대로 | 유지 |
| executability / correctness | Zero-shot Planner 원문 그대로 (단, 원 논문의 correctness는 사람 평가) | 유지 — 이 연구는 라벨로 자동 채점한다고 명시 |
| 의미적 오류(semantic error) | 4편에 없음. Zero-shot Planner는 "semantic correctness" | **교체** — "semantically incorrect" |
| 그라운딩 | Zero-shot Planner와 뜻이 다름 | 사용 시 정의, 가급적 생략 |
| 환경 고유의 규약 / 암묵적 규약 | 4편에 없음 | 이 연구의 용어로 정의 |
| 검증 신호 | 4편에 없음. CodeAct·SWE-agent는 automated/environment feedback | **교체** — "자동 피드백", "환경 피드백" |
| 스텝 | CodeAct는 interaction turns, OpenHands 설정은 iterations | **교체** — "상호작용 턴" |
| 성공률 | CodeAct "success rate" | 유지 |
| 같은 LLM으로 비교 | SWE-agent "we assume a fixed LM and focus on designing the ACI" | 이 문장을 그대로 인용하면 실험 설계 정당화가 됨 |
| 연구자 = 새로운 사용자 | SWE-agent "LM agents represent a new category of end user" | 인트로에서 활용 가능 (ACI가 필요한 이유) |

추가로 원문에서 확인한 것
- CodeAct도 코드 기반 행동의 선행(로봇·게임 제어)을 인정하고 "pre-specified primitives에 의존한다"고 한계를 지적함 → 이 문서의 "처음 제안이라고 쓰지 않음"과 일치
- CodeAct는 LLM 에이전트의 적용 예로 "performing scientific experiments (Bran et al., 2023 = ChemCrow)"를 듦 → 과학 에이전트 프레이밍의 근거로 인용 가능
- CodeAct M³ToolEval의 최대 10턴 설정 → 이 연구의 최대 10턴과 같은 기준으로 인용 가능
- SWE-agent의 ACI 설계 원칙 4가지(간단한 행동, 압축된 행동, 유익하지만 간결한 피드백, 가드레일)는 DDI skill 설계를 설명하는 틀로 그대로 쓸 수 있음 (2.3)

---

## 1. 연구 개요

### 1.1 첫 문단 (초안) ✅
> LLM 기반 에이전트는 코드를 작성하고 실행하는 방식으로 환경과 상호작용하며, 소프트웨어 공학을 넘어 과학 연구로 활용 범위를 넓히고 있다. 그러나 공개된 딥러닝 연구 모델은 저마다 독자적인 실행 환경과 입출력 규약을 지니며, 이는 LLM의 사전학습 데이터에 거의 포함되어 있지 않다. DSN-DDI와 SSI-DDI는 서로 다른 관계 번호 체계를 사용하며, DSN-DDI의 86개 관계 유형 중 42개는 SSI-DDI와 비교했을 때 약물의 순서가 반대로 정의되어 있다. 이로 인해 generalist agent는 연구 파이프라인을 오류 없이 끝까지 실행하더라도(실행 가능성, executability), 모델 고유의 암묵적 규약을 알지 못해 겉보기엔 정상이지만 의미적으로 틀린 출력(정확성 결여, correctness)을 내놓을 수 있다. 본 연구는 연구 파이프라인용 domain-specific ACI를 갖춘 specialist agent를 제안하고, 약물 상호작용 예측 모델 DSN-DDI를 사례로 같은 LLM과 에이전트 구조에서 generalist agent보다 도메인 작업을 더 정확하게 수행하는지 검증한다.

### 1.2 위치 ✅
- 분야: **AI for Science** — 과학 에이전트(scientific agent)
- 큰 목적: 연구실이 만든 연구 파이프라인을 에이전트로 감싸서, **자연어 요청 → 에이전트가 도메인 도구로 코드를 짜서 실행 → 표·그래프·파일로 결과 전달**
- DSN-DDI: 이 목적을 보이는 **사례 연구 1건** (다른 파이프라인으로 확장은 향후 연구)
- 두 관점
  - 사용자 관점: 자연어로 다양한 요청을 할 수 있어 겉보기엔 generalist agent
  - 도메인 관점: 특정 파이프라인을 올바르게 실행·해석하는 일을 자동화

### 1.3 가설과 핵심 주장 ✅

**가설**: 약리학처럼 좁은 도메인의 연구 파이프라인에서는 generalist agent가 더 많이 틀리고, domain-specific ACI를 갖춘 specialist agent는 더 많이 맞힐 것이다. 차이는 실행 가능성보다 **정확성** 축에서 클 것이다.

가설의 근거 — LLM 지식이 통하는 곳과 통하지 않는 곳이 다르다:

| 구분 | 예시 | 범용 LLM이 알 수 있나 |
|---|---|---|
| 일반 능력 | 코드 작성, 에러 수정, 요청 이해 | 알 수 있음 — 좋은 LLM일수록 잘함 |
| 널리 알려진 약리학 지식 | Aspirin–Warfarin 같은 유명한 조합의 방향 | 알 수 있음 — 학습 중 많이 본 조합이면 틀린 결과를 알아챌 수 있음 |
| 덜 알려진 약리학 지식 | 잘 알려지지 않은 약물 쌍 | 알기 어려움 |
| 환경 고유의 규약 | 관계 번호 체계, 올바른 번호 칸, 42종 방향 뒤집힘, 학습셋 범위 | **알 수 없음** — 이 저장소에만 있는 사실이라 LLM 성능과 무관 |

→ generalist와 specialist agent의 차이는 아래 두 행(롱테일 지식, 환경 고유 규약)에서 커질 것으로 예상한다.
→ 좋은 LLM으로도 환경 고유의 규약은 대신할 수 없다.
→ 인트로 근거: 롱테일 지식에 약하다는 선행 연구(Kandpal et al., 2023) + 환경 고유 규약은 사전 관찰(1.5)로 제시. 표 자체는 인트로가 아니라 방법론·논의 장에 둠.

**핵심 주장**: 같은 LLM, 같은 에이전트 구조(OpenHands CodeActAgent)에서, **파이프라인에 맞춘 domain-specific ACI** 를 주면 generalist agent보다 **그 도메인 작업을 더 정확하게** 수행한다.
- 이름: **domain-specific ACI** — SWE-agent의 ACI(agent-computer interface) 개념을 인용·확장
- 근거: 에이전트용 인터페이스 설계가 같은 LLM의 성능을 바꾼다 — SWE-agent는 "고정된 LM(fixed LM)을 두고 ACI 설계에 집중"하는 설정으로 이를 보임. 이 연구도 같은 설정
- 행동 형식: CodeAct를 그대로 사용 (코드 실행을 generalist agent의 통합 행동 공간으로 체계화하고 JSON·텍스트 대비 효과 검증). "처음 제안"이라고 쓰지 않음 — 선행: PAL, PoT, Code as Policies, ViperGPT, Voyager, TaskWeaver
- 관련 연구: ChemCrow(화학 도구 에이전트), Paper2Agent(논문 코드 → 에이전트 도구, 범용)

### 1.4 대상 사용자 ✅
**DDI 도메인 지식은 있지만 ML 모델을 직접 다루기 어려운 연구자** (약학, 임상, 실험 연구자)
- "전문가는 필요 없지 않냐"에 대한 답: 모델 저자·ML 연구자는 직접 스크립트를 짜는 게 빠르지만, 인접 분야 연구자는 모델 결과가 가장 필요한데도 쓸 수 없음
- 전문가도 놓치기 쉬운 "에러 없는 함정"을 인터페이스에 담아두는 것 자체가 가치 (1.5)

### 1.5 문제 지적 ✅
1. **연구자가 모델을 돌리기 어렵다**: 옛날 환경, 가중치 형식, LFS 데이터
2. **출력을 올바르게 해석하기 어렵다**: 관계 번호, 번호 체계 불일치, 방향 뒤집힘
3. **요청이 매번 달라 고정 스크립트로 해결 안 된다**: 원 스크립트는 테스트셋 평가만 가능
4. **generalist agent로는 틈이 안정적으로 메워지지 않는다**: 비교 실험의 실패 사례로 채움

실제로 확인된 문제는 두 종류로 나뉜다.

**(가) 실행 가능성(executability) 실패 — 돌리려고 하면 막힌다 (에러 메시지가 나옴)**

| 문제 | 증상 |
|---|---|
| 가중치가 모델 객체째 저장(`.pkl`) | 최신 PyTorch/PyG에서 로드 에러 |
| 데이터 zip이 Git LFS | 그냥 클론하면 134바이트 포인터만 받아져 압축 해제 에러 |

→ 에러가 관찰(observation)로 돌아오므로 generalist agent도 고칠 수 있다. 시간·상호작용 턴이 많이 드는 문제.

**(나) 정확성(correctness) 실패 — 실행은 되고 결과도 그럴듯한데, 의미가 틀리다 (에러 메시지 없음)**

| 문제 | 무엇이 틀리게 나오나 |
|---|---|
| 설명 파일 하나에 번호 체계가 두 개 공존 (`Interaction type`: DSN-DDI용, `DDI type N`: SSI-DDI용) — 문서화 없음 | 다른 칸을 쓰면 설명 문장이 다른 관계로 바뀜 |
| DSN-DDI 번호는 0부터, `Interaction type` 칸은 1부터 | 1칸 밀리면 전부 다른 관계로 바뀜 |
| 42종(`Subject` = 2)은 약물 순서가 템플릿과 반대로 저장됨 — 문서화 없음 | 누가 누구에게 영향을 주는지 반대로 나옴 |
| 학습셋 밖 약물을 transductive 모델에 넣음 / 원자 특징 unknown | 신뢰할 수 없는 예측이 평소와 똑같은 형식으로 나옴 |

**표 1 (논문 삽입용). DSN-DDI 출력의 올바른 해석과 흔한 잘못된 해석**

DSN-DDI는 약물 쌍 (d1, d2)에 대해 관계 번호만 출력한다. 관계 설명은 선행 연구 SSI-DDI의 설명 파일에만 있다.

| 입력 (d1, d2) | DSN-DDI 출력 | 올바른 해석 | 잘못된 해석 ① 다른 번호 체계 사용 | 잘못된 해석 ② 방향 무시 |
|---|---|---|---|---|
| Warfarin, Aspirin | 5 | **Aspirin**이 Warfarin의 **항응고 효과를 높인다** | Warfarin이 Aspirin의 **대사를 낮춘다** | **Warfarin**이 Aspirin의 항응고 효과를 높인다 |
| Simvastatin, Clarithromycin | 72 | Clarithromycin이 **Simvastatin**의 혈중 농도를 높인다 | Simvastatin이 Clarithromycin의 **신경근 차단 효과를 높인다** | Simvastatin이 **Clarithromycin**의 혈중 농도를 높인다 |
| Carbamazepine, Simvastatin | 3 | Carbamazepine이 Simvastatin의 **대사를 높인다** | Carbamazepine이 Simvastatin의 **생체이용률을 낮춘다** | (올바른 해석과 같음 — 방향이 같은 44종에 속함) |

- 잘못된 해석 ①: DSN-DDI 번호를 SSI-DDI용 번호 칸(`DDI type N`−1)으로 대응시킨 경우 → **관계 자체가 바뀜**
- 잘못된 해석 ②: 관계 번호는 올바르게 대응시켰지만 약물 순서를 그대로 쓴 경우 → **영향을 주는 쪽과 받는 쪽이 바뀜** (86종 중 42종)
- 세 해석 모두 문법적으로 맞고 약 이름도 맞으며, 실행 오류가 나지 않는다.
- 원문(영어) 확인: 올바른 해석 1행 = "Acetylsalicylic acid may increase the anticoagulant activities of Warfarin." (`dsn_relation_map.csv`에서 재현 가능)

→ 에러 메시지가 없으므로 **출력만 보고는 알아차리기 어렵다.**
- 연구자: 잘 알려진 조합(예: Aspirin–Warfarin)은 도메인 지식으로 잡을 수 있지만, 낯선 약물이나 수십 쌍을 한꺼번에 예측한 결과는 하나하나 확인하기 어렵다.
- generalist agent: 환경 고유의 규약(번호 체계, 방향)을 알 방법이 없고, 에러가 관찰로 돌아오지 않아 같은 오류를 낼 **가능성이 높다** (가설 — 실험의 실패 원인 분류로 확인).

→ 논문 용어: **정확성(correctness) 실패** — 실행은 성공하지만 결과가 **의미적으로 틀린(semantically incorrect)** 경우 (Zero-shot Planner의 semantic correctness에 대응).
→ Zero-shot Planner가 "correct but not executable"을 다뤘다면, 이 연구는 **"executable but not correct"** 를 다룬다.
→ 이 연구는 domain-specific ACI로 이 오류를 줄일 수 있는지 확인한다.

---

## 2. 시스템 구성

### 2.1 에이전트 ✅
- generalist agent: **OpenHands CodeActAgent** 그대로 사용 (에이전트 루프를 새로 만들지 않음)
- specialist agent: CodeActAgent 구현을 재사용하는 **micro agent** + **domain-specific ACI** (구성은 2.3)
- 입력: 자연어 (한국어 요청, 약 이름은 영어 또는 DrugBank ID, 신약은 SMILES)

### 2.2 실행 환경 ✅
Dockerfile 1개, 이미지 1개, 컨테이너 1개. 안에 파이썬 환경 2개.

| 환경 | 파이썬 | 역할 | 누가 설치 |
|---|---|---|---|
| ① 코드 실행 환경 | 최신 | 에이전트가 쓴 코드 실행, `ddi` 모듈 import | OpenHands가 자동 |
| ② DSN-DDI 환경 | 3.7 (PyTorch 1.9.0, PyG 2.0.3) | 예측 서버만 실행 | Dockerfile에서 직접 |

```
LLM이 코드 작성 → 실행 서버(①)가 실행 → ddi.predict()가 예측 서버(②, localhost)에 요청 → 결과 반환
```

- 예측 서버는 가중치 **두 개**를 모두 올려둠
  - `transductive_drugbank.pkl`: 두 약물 모두 학습셋에 있을 때
  - `inductive_drugbank.pkl`: 한쪽이라도 학습셋 밖(신약)일 때

### 2.3 domain-specific ACI (연구의 핵심 기여) ✅

정의: **고정된 LM을 두고, 연구 파이프라인에 맞춰 행동(commands)·문서(documentation)·환경 피드백(environment feedback)·가드레일(guardrails)을 설계한 ACI** (SWE-agent의 ACI 개념을 과학 파이프라인으로 확장)

| 구성 요소 (SWE-agent 원어) | 구현 | 대응하는 SWE-agent 설계 원칙 |
|---|---|---|
| 행동 (commands) | 아래 DDI skill (OpenHands **AgentSkills** 형태) | 1. 간단하고 이해하기 쉬운 행동 / 2. 압축되고 효율적인 행동 (`predict_many`) |
| 문서 (documentation) | 각 skill의 사용법 + OpenHands **micro agent** 프롬프트 | 1. 간결한 문서 |
| 환경 피드백 (environment feedback) | 방향이 맞춰진 관계 문장, 확률·사용 모델 표시 | 3. 유익하지만 간결한 피드백 |
| 가드레일 (guardrails) | 모르는 약물 거부, 신약이면 inductive 전환 + 경고, 원자 특징 unknown 경고 | 4. 오류 전파를 막고 복구를 돕는 가드레일 |

본문에서는 "고정된 LM에 대해 ACI를 설계했다"로 설명하고, 구성 요소 구분은 방법론 장의 구현 설명에서만 사용.

구현 방식: OpenHands의 AgentSkills와 같은 방식 — 파이썬 패키지로 만들어 IPython 환경에 자동 import, 에이전트는 기존 행동(`IPythonRunCellAction`)으로 호출. 새 행동 유형을 추가하지 않으므로 **generalist와 specialist의 행동 형식이 동일** → 차이는 인터페이스뿐.

DDI skill:
| 함수 | 하는 일 |
|---|---|
| `resolve_drug(x)` | 영어 이름·동의어·DrugBank ID·SMILES → 표준 약물 정보 |
| `lookup_known(a, b)` | 데이터에 기록된 상호작용 조회 |
| `predict(a, b, top_k=3)` | DSN-DDI 예측, transductive/inductive 자동 선택, 학습셋 포함 여부 반환 |
| `predict_many(pairs, relation=None)` | 여러 쌍 일괄 예측, 특정 관계로 필터 |
| `explain(rel, a, b)` | 관계 번호 → 문장 (방향 반영) |
| `save_results(df, path)` | 결과를 채점용 CSV로 저장 |
| 검사 기능 | 모르는 약물, 학습셋 밖 약물, 원자 특징 unknown 경고 |

---

## 3. 데이터

### 3.1 DSN-DDI 공식 데이터 ✅
- 출처: `microsoft/Drug-Interaction-Research` 브랜치 `DSN-DDI-for-DDI-Prediction` 의 `DSN-DDI-dataset.zip` (176MB, LFS)
- `dataset/drugbank/fold0/`: train 153,446건 / **test 38,362건**, 관계 86종
- `dataset/inductive_data/fold0/`: s1(두 약 모두 신약), s2(한쪽만 신약)

### 3.2 약 이름 ✅
- DrugBank Vocabulary (CC0) — 공식 다운로드가 중단 상태라 `fgh95/DrugLinker` 사본 사용
- 약물 13,475개, DSN-DDI 약물 1,706개 중 **1,701개 커버** (빠진 5개 DB09323, DB13450, DB09396, DB09162, DB11106 → 평가에서 제외)
- 한국어 이름 매핑: 하지 않음

### 3.3 관계 번호 → 문장 대응표 ✅ (완료, `dsn_relation_map.csv`)
- 설명 출처: SSI-DDI `data/Interaction_information.csv`
- 결과: **86종 전부 1:1 대응**, 최소 일치율 97.4%, 방향 일치율 99.3% 이상 → 제외 없음
- **규칙 (데이터로 100% 확인됨)**: DSN-DDI 관계 번호 `t` → 설명 파일에서 `Interaction type == t + 1` 인 행
  - 그 행의 `Subject` = 1 또는 3 → 약물 순서 그대로 (#Drug1 = d1)
  - `Subject` = 2 → 약물 순서 반대 (#Drug1 = d2) — 86종 중 42종
  - `Subject` = 3은 "위험이 증가한다"처럼 방향이 없는 대칭 관계 (7종)
- SSI-DDI 데이터용 번호는 `DDI type N`의 N−1 (DSN-DDI에는 쓰면 안 됨)
- 처음에는 SSI-DDI와 같은 약물 쌍을 대조해서 대응표를 만들었고, 이후 위 규칙과 **86종 모두 일치**함을 확인

**왜 순서가 다른가 (추정)**
- DSN-DDI는 원 데이터의 번호(`Interaction type`)와 약물 저장 순서를 그대로 사용하고, SSI-DDI는 약물 순서를 설명 문장의 #Drug1/#Drug2에 맞게 재정렬하고 번호를 새로 매긴 것으로 보인다.
- 즉 어느 한쪽의 버그가 아니라 **전처리 관례가 두 가지**이고, 이를 풀 수 있는 정보(`Subject` 칸)가 파일에 있지만 **어디에도 설명되어 있지 않다.**
- 원 데이터는 DeepDDI(86종 DDI 유형)로 추정되나, 원본과 직접 대조는 하지 않음 ⚠️
- 확인 예시
  - Warfarin + Aspirin (관계 5) → "Aspirin may increase the anticoagulant activities of Warfarin." ✔
  - Simvastatin + Clarithromycin (관계 72) → "The serum concentration of Simvastatin can be increased when it is combined with Clarithromycin." ✔

---

## 4. 비교 조건 ✅

| 조건 | 구성 | 보여주는 것 |
|---|---|---|
| A. LLM 단독 | 툴 없이 API로 바로 답함 | "모델 없이 LLM 지식으로 충분한가" |
| B. generalist agent | OpenHands CodeActAgent 그대로 + 같은 런타임 + DSN-DDI 저장소 | generalist agent의 한계 |
| C. specialist agent | B + domain-specific ACI (DDI skill + micro agent 프롬프트) | domain-specific ACI의 효과 |

- A는 확률 계산이 불가능하므로 **작업 유형 ①(단일 쌍)에만** 적용
- A도 API로 실행 (웹 채팅 사용 안 함)
- ❓ 여유 시: C′ 단계별 ablation — documentation만 → + commands·environment feedback → + guardrails(전체)

---

## 5. LLM·실행 설정 ✅

| 항목 | 값 |
|---|---|
| 호출 경로 | Vercel AI Gateway |
| 주력 모델 | `anthropic/claude-sonnet-5.5` — 전체 실험 |
| 교차 검증 모델 | `openai/gpt-6-sol` — 일부(예: 100개) |
| 추론 강도 | Low (비용 절약, 향후 변경 가능) |
| temperature | 0.0 고정 (temperature 실험 제외) |
| 최대 상호작용 턴 | 10 (OpenHands `max_iterations`), 초과 시 실패 — CodeAct M³ToolEval과 같은 기준 |
| OpenHands 버전 | 시작 시점 최신, 버전 번호 기록 후 고정 |

⚠️ 스모크 테스트: Sonnet 5.5 동작, temperature·추론 강도 실제 적용 여부, 캐싱 적용 여부

---

## 6. 평가

### 6.1 작업 유형과 질문 세트 ❓ (개수는 제안)
| 유형 | 예시 요청 | 개수(안) | 적용 조건 |
|---|---|---|---|
| ① 단일 쌍 예측 | "Warfarin이랑 Aspirin 상호작용 예측해줘" | 100 | A, B, C |
| ② 다중 조합 | "이 약물 6개의 모든 조합(15쌍)을 예측해서 표로 정리해줘" | 30 | B, C |
| ③ 관계 필터 | "이 목록에서 혈중 농도를 높이는 조합만 찾아줘" | 30 | B, C |
| ④ 신약 입력 | "이 SMILES 구조와 Warfarin의 상호작용 예측해줘" | 20 | B, C |

- ①: fold0 test에서 관계 86종이 고르게 나오도록 층화 추출
- ②③: fold0 test에 기록된 약물로 목록 구성
- ④: inductive s1/s2에서 추출
- 요청 문장: 한국어, 약 이름은 영어
- (선택) 질문마다 "유명한 조합인지" 표시 → 채점 후 유명/비유명으로 나눠 성공률 비교 (1.3 가설 확인용, 추가 실험 없음)

### 6.2 결과 형식 ✅
- **채점용**: 모든 결과를 CSV로 저장 (`drug_a, drug_b, relation, prob, model_used`)
- **사람용**: 답변에 ① 확인된 약물 ② 기록된 상호작용 ③ 모델 예측(상위 관계·확률·신뢰도) ④ 한계 표시(예측값임, 신약은 신뢰도 낮음)
- 표·그래프 이미지는 **채점하지 않음** → 대표 사례만 논문 그림으로 제시

### 6.3 정답 만들기 ✅
- 정답은 같은 약물 쌍을 **원 DSN-DDI 스크립트로 직접 실행**해서 계산
- 에이전트의 CSV와 비교

### 6.4 지표 ✅
| 지표 | 정의 |
|---|---|
| **성공률 (주 지표)** | 약물 모두 올바르게 식별 AND 정답 관계가 top-3 안 (①④) / 표의 쌍·관계·확률이 정답과 일치 (②③) |
| top-1 정확도 | 보조 지표 (①④) |
| 충실도 | 에이전트 경로 예측 = 원 스크립트 예측 비율 |
| 실행 가능성 (executability) | 결과(CSV)까지 도달했는지 — (가) 유형 실패 측정 |
| 해석 정확도 (correctness) | 관계 번호가 맞았을 때, 최종 문장(관계 종류와 약물 방향)도 맞았는지 — 번호 채점만으로는 (나) 유형 오류가 안 잡힘 |
| 한계 표시 | 신약·학습셋 밖 입력에서 신뢰도 경고를 했는지 (④) |
| 효율 | 평균 상호작용 턴 수, 토큰, 시간, 턴 초과 실패 비율 |

- 안전성(심각도) 지표: **제외** (대상이 연구자로 바뀌어 한계 표시로 대체)
- ⚠️ ①은 테스트셋에서 뽑아서 `lookup_known`이 정답을 바로 찾을 수 있음 → 조회 결과와 모델 예측을 따로 채점하거나, 조회 대상에서 테스트셋을 빼야 함

### 6.5 A 조건 채점 ✅
- A는 문장으로 답하므로 86종 중 하나로 분류 필요
- Claude, GPT 두 채점기가 각각 분류 → 같으면 채택, 다르면 그 건만 사람이 확인
- 논문에 채점기 일치율 보고
- ⚠️ 채점기 모델을 실험 모델과 같은 걸로 쓸지

---

## 7. 2주 일정 (안)

| 기간 | 할 일 |
|---|---|
| 1~2일 | 도커 이미지(환경 ②) 빌드, 원 테스트 스크립트로 논문 수치 재현 |
| 3~4일 | 예측 서버(가중치 2개) + `ddi` 도구 |
| 5일 | OpenHands에 이미지 연결, micro agent 지침, 스모크 테스트 |
| 6~7일 | 작업 유형별 질문 세트와 정답 생성, A 조건 스크립트 |
| 8~10일 | A, B, C 실행 (주력 모델) + 교차 검증 모델 일부 |
| 11~12일 | 채점, 실패 사례 정리 |
| 13~14일 | 결과표·사례 그림, 여유분 |

---

## 8. 결정이 남은 것

| # | 항목 | 상태 |
|---|---|---|
| 1 | 작업 유형별 질문 개수 (6.1) | ❓ |
| 2 | 테스트셋 정답이 조회에 섞이는 문제 처리 (6.4) | ⚠️ 중요 |
| 3 | 채점기 모델 선택 (6.5) | ⚠️ |
| 4 | C′ 단계별 ablation 여부 | ❓ 여유 시 |
| 5 | 스모크 테스트 결과 | ⚠️ |

---

## 9. 핵심 참고문헌 (⚠️ 서지 정보는 원문으로 재확인)

- **SWE-agent**: Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering," NeurIPS 2024. arXiv:2405.15793
- **CodeAct**: Wang et al., "Executable Code Actions Elicit Better LLM Agents," ICML 2024. arXiv:2402.01030
- **OpenHands**: Wang et al., "OpenHands: An Open Platform for AI Software Developers as Generalist Agents," ICLR 2025. arXiv:2407.16741
- **DSN-DDI**: Li et al., "DSN-DDI: an accurate and generalized framework for drug–drug interaction prediction by dual-view representation learning," Briefings in Bioinformatics 24(1), 2023. doi:10.1093/bib/bbac597
- **SSI-DDI** (관계 설명 출처): Nyamabo et al., Briefings in Bioinformatics 22(6), 2021. doi:10.1093/bib/bbab133
- **ChemCrow**: Bran et al., "Augmenting large language models with chemistry tools," Nature Machine Intelligence, 2024
- **Paper2Agent**: Miao et al., Nature, 2026 (arXiv:2509.06917)
- **DrugBank**: Knox et al., "DrugBank 6.0," Nucleic Acids Research 52(D1), 2024
- **Zero-shot Planner**: Huang et al., "Language Models as Zero-Shot Planners: Extracting Actionable Knowledge for Embodied Agents," ICML 2022. arXiv:2201.07207 — executability/correctness 두 축, admissible actions
- **Long-tail knowledge**: Kandpal et al., "Large Language Models Struggle to Learn Long-Tail Knowledge," ICML 2023

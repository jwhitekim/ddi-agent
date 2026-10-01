# comparison-conditions Specification

## Purpose

비교 실험의 세 조건(A: LLM 단독, B: generalist agent, C: specialist agent)이 각각 무엇을 받는지 정한다. 그래서 B와 C의 차이가 domain-specific ACI 하나뿐이 되게 하고, 결과를 같은 형식으로 채점할 수 있게 한다.

## Requirements

### Requirement: 조건 A는 실행 환경 없이 답한다
조건 A는 LLM API만으로 답해야 한다(SHALL). 코드 실행 환경(①), DSN-DDI 환경(②), 예측 서버, `ddi` skill, micro agent 프롬프트 중 어느 것도 받지 않아야 한다(MUST NOT). A는 작업 유형 ①(단일 쌍)에만 적용한다(SHALL).

#### Scenario: A에게 단일 쌍 질문
- **WHEN** 작업 유형 ①의 질문이 A에게 주어지면
- **THEN** A는 코드 실행 없이 텍스트로만 답하고, 그 답은 6.5절 방식으로 86개 관계 중 하나로 분류해 채점한다

### Requirement: B와 C는 같은 런타임 재료를 받는다
조건 B와 C는 모두 다음을 받아야 한다(SHALL): 환경 ①, 환경 ②(파이썬 3.7, PyTorch 1.9.0, PyG 2.0.3), DSN-DDI 저장소 코드(가중치를 불러오는 데 필요한 모델 정의 포함), 가중치 2개(transductive, inductive), 압축을 푼 DSN-DDI 데이터(저장소의 LFS 포인터 파일 대신), SSI-DDI 관계 설명 파일, 그리고 환경 ② 인터프리터 위치를 알려주는 안내 한 줄.

#### Scenario: B가 모델을 직접 실행
- **WHEN** B가 상호작용을 예측하려고 하면
- **THEN** B는 안내 한 줄로 환경 ②를 찾아 직접 쓴 추론 스크립트를 실행할 수 있고, LFS 다운로드나 환경 설치 없이 관계 번호 출력까지 도달할 수 있다

#### Scenario: B가 관계를 해석
- **WHEN** B가 관계 번호를 문장으로 바꾸려고 하면
- **THEN** 컨테이너 안에 SSI-DDI 설명 파일이 있어서 B가 그 파일을 읽을 수 있다

### Requirement: domain-specific ACI는 C에게만 준다
예측 서버, `ddi` skill, micro agent 프롬프트는 C에게만 주어야 한다(SHALL). B를 실행할 때는 예측 서버를 켜지 않아야 하고(MUST NOT), `ddi` 패키지와 서버 코드가 컨테이너 안에 없어야 한다(MUST NOT).

#### Scenario: B 컨테이너 안에 ACI 흔적이 없음
- **WHEN** B를 실행하는 컨테이너의 파일과 포트를 확인하면
- **THEN** `ddi` 패키지, 예측 서버 코드, 실행 중인 예측 서버가 하나도 없다

#### Scenario: C 실행
- **WHEN** C를 실행하면
- **THEN** 예측 서버가 환경 ②에서 떠 있고, 환경 ①에서 `ddi` 함수가 미리 import되어 있으며, micro agent 프롬프트가 적용되어 있다

### Requirement: 에이전트는 정답을 볼 수 없다
어떤 조건의 에이전트도 정답(기록된 상호작용 label)을 돌려주는 기능을 받지 않아야 한다(MUST NOT). `ddi` skill에 기록 조회 기능(`lookup_known`)을 넣지 않아야 한다(MUST NOT).

#### Scenario: C가 테스트셋 쌍을 질문받음
- **WHEN** C가 테스트셋에서 뽑은 약물 쌍을 질문받으면
- **THEN** C는 모델 예측(`predict`)과 해석(`explain`)으로만 답하고, 정답을 조회할 수 있는 함수는 제공되지 않는다

### Requirement: 채점용 CSV는 최종 문장을 포함한다
B와 C의 결과 CSV는 `drug_a, drug_b, relation, prob, model_used, description` 칼럼을 가져야 한다(SHALL). `description`은 약물 방향이 반영된 최종 관계 문장이다. 정답은 원 DSN-DDI 스크립트 실행 결과에서 만들어야 한다(SHALL).

#### Scenario: 방향 오류 채점
- **WHEN** 관계 번호는 정답과 같지만 `description`의 약물 방향이 정답 문장과 반대이면
- **THEN** 그 행은 해석 정확도(correctness)에서 오답으로 채점된다

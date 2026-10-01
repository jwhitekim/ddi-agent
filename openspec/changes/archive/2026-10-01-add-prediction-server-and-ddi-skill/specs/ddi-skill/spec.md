# Spec Delta

## Purpose

조건 C의 에이전트가 환경 ①에서 호출하는 DDI 함수 모음(domain-specific ACI의 commands·environment feedback·guardrails)을 정의한다. 약물 식별부터 결과 저장까지, 관계 번호 해석의 함정을 함수 안에서 처리한다.

## ADDED Requirements

### Requirement: resolve_drug는 약물 표기를 표준 약물로 바꾼다
`resolve_drug(x)`는 영어 이름, 동의어, DrugBank ID, SMILES를 받아 DrugBank ID, 대표 이름, DSN-DDI 데이터 포함 여부를 돌려줘야 한다(SHALL). 이름 비교는 대소문자를 구분하지 않고 대표 이름과 동의어 전체가 일치해야 한다(SHALL). 일치하는 약물이 여러 개이면 후보 목록과 함께 에러를 내야 한다(SHALL). DSN-DDI 데이터에 없는 약물 이름이면 거부해야 한다(SHALL).

#### Scenario: 이름으로 식별
- **WHEN** `resolve_drug("Aspirin")`을 호출하면
- **THEN** `DB00945`와 대표 이름 `Acetylsalicylic acid`가 돌아온다

#### Scenario: 모르는 약물
- **WHEN** 사전에 없는 이름이나 DSN-DDI 데이터에 없는 약물을 넣으면
- **THEN** 예측하지 않고, 이유를 설명하는 에러가 난다

#### Scenario: SMILES 입력
- **WHEN** SMILES 문자열을 넣으면
- **THEN** 신약으로 표시된 결과가 돌아온다 (DrugBank ID 없음)

### Requirement: predict는 방향이 반영된 상위 관계를 돌려준다
`predict(a, b, top_k=3)`는 두 약물을 식별한 뒤 예측 서버에 요청하고, 상위 k개 관계마다 관계 번호, 확률, 방향이 반영된 문장(`explain` 결과)을 돌려줘야 한다(SHALL). 결과에는 사용한 모델과 경고 목록이 들어 있어야 한다(SHALL).

#### Scenario: Warfarin과 Aspirin
- **WHEN** `predict("Warfarin", "Aspirin")`의 상위 관계가 5이면
- **THEN** 문장은 "Acetylsalicylic acid may increase the anticoagulant activities of Warfarin."이다

### Requirement: 학습셋 밖 입력에는 경고를 붙인다
두 약물 중 하나라도 transductive 학습셋 밖이거나 SMILES 신약이면, `predict`와 `predict_many`는 inductive 모델을 썼다는 것과 신뢰도가 낮다는 경고를 붙여야 한다(SHALL). 서버가 unknown 원자를 표시하면 그 경고도 붙여야 한다(SHALL).

#### Scenario: 신약 경고
- **WHEN** SMILES 신약과 Warfarin을 `predict`하면
- **THEN** 결과의 `model_used`가 inductive이고, 경고 목록에 신뢰도가 낮다는 문장이 있다

### Requirement: explain은 DSN-DDI 번호를 올바른 문장으로 바꾼다
`explain(rel, a, b)`는 설명 파일에서 `Interaction type == rel + 1`인 행을 써야 한다(SHALL). 그 행의 `Subject`가 2이면 #Drug1에 b, #Drug2에 a를 넣고, 1 또는 3이면 #Drug1에 a, #Drug2에 b를 넣어야 한다(SHALL). `DDI type N` 칸은 쓰지 않아야 한다(MUST NOT).

#### Scenario: 방향이 같은 관계
- **WHEN** `explain(3, "Carbamazepine", "Simvastatin")`을 호출하면
- **THEN** Carbamazepine이 Simvastatin의 대사를 높인다는 문장이 나온다

#### Scenario: 방향이 반대인 관계
- **WHEN** `explain(72, "Simvastatin", "Clarithromycin")`을 호출하면
- **THEN** "The serum concentration of Simvastatin can be increased when it is combined with Clarithromycin."이 나온다

#### Scenario: 86종 전부
- **WHEN** 관계 0~85에 대해 `explain`을 호출하면
- **THEN** 86개 모두 문장이 나오고, 그중 42개는 약물 순서가 뒤집혀 들어간다

### Requirement: predict_many는 여러 쌍을 한 번에 예측하고 관계로 거른다
`predict_many(pairs, relation=None)`는 약물 쌍 목록을 예측해 쌍마다 한 행씩 표로 돌려줘야 한다(SHALL). `relation`에 관계 번호(하나 또는 목록)를 주면, 상위 k개 안에 그 관계가 있는 쌍만 남겨야 한다(SHALL). 식별에 실패한 쌍은 표에서 빼지 않고 에러 내용을 표시해야 한다(SHALL).

#### Scenario: 6개 약물의 모든 조합
- **WHEN** 약물 6개로 만든 15쌍을 `predict_many`하면
- **THEN** 15행이 돌아온다

#### Scenario: 관계 필터
- **WHEN** `relation=72`로 `predict_many`하면
- **THEN** 상위 관계에 72가 있는 쌍만 남는다

### Requirement: save_results는 채점용 CSV를 저장한다
`save_results(df, path)`는 `drug_a, drug_b, relation, prob, model_used, description` 칼럼으로 CSV를 저장해야 한다(SHALL). `predict`와 `predict_many` 결과를 그대로 넘기면 이 형식이 되어야 한다(SHALL).

#### Scenario: CSV 저장
- **WHEN** `predict_many` 결과를 `save_results`로 저장하면
- **THEN** 파일의 칼럼이 정확히 위 6개이고, `description`에 방향이 반영된 문장이 들어 있다

### Requirement: 정답 조회 기능이 없다
`ddi` 패키지에는 데이터에 기록된 상호작용(label)을 돌려주는 함수가 없어야 한다(MUST NOT).

#### Scenario: 공개 함수 확인
- **WHEN** `ddi` 패키지의 공개 함수 목록을 보면
- **THEN** `resolve_drug, predict, predict_many, explain, save_results`만 있다

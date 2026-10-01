# prediction-server Specification

## Purpose

환경 ②(파이썬 3.7)에서 DSN-DDI 가중치를 올려두고, 환경 ①의 `ddi` 패키지가 보내는 약물 쌍 요청에 86개 관계 점수를 계산해 돌려주는 로컬 예측 서버를 정의한다.

## Requirements

### Requirement: 서버는 두 가중치를 올려두고 localhost에서 요청을 받는다
예측 서버는 시작할 때 `transductive_drugbank.pkl`과 `inductive_drugbank.pkl`을 모두 GPU에 올려야 한다(SHALL). 서버는 컨테이너 안의 localhost에서만 HTTP JSON 요청을 받아야 한다(SHALL).

#### Scenario: 서버 상태 확인
- **WHEN** 서버가 시작된 뒤 상태 확인 요청을 보내면
- **THEN** 두 모델이 모두 올라가 있다는 응답이 돌아온다

### Requirement: 약물 쌍에 대해 86개 관계 점수를 모두 계산한다
서버는 약물 쌍 (d1, d2) 하나에 대해 관계 0~85 각각의 점수를 계산하고, 각 점수에 sigmoid를 씌운 값을 확률로 돌려줘야 한다(SHALL). 응답은 확률이 높은 순서로 상위 k개(기본 3)의 관계 번호와 확률을 포함해야 한다(SHALL). 관계 번호는 DSN-DDI 번호(0부터)여야 한다(MUST).

#### Scenario: 알려진 쌍 예측
- **WHEN** fold0 test에 있는 쌍 (d1, d2)를 top_k=3으로 요청하면
- **THEN** 서로 다른 관계 번호 3개와 각 확률(0~1)이 확률 내림차순으로 돌아온다

#### Scenario: 원 모델과 일치
- **WHEN** 같은 쌍과 관계 r을 원 저장소의 데이터 처리(`DrugDataset.collate_fn`의 양성 샘플, 배치 크기 1)로 만든 입력으로 모델에 넣으면
- **THEN** 서버가 돌려준 r의 확률과 소수점 4자리까지 같다

### Requirement: 쌍마다 독립적으로 계산한다
서버는 약물 쌍 하나만 넣은 입력(배치 크기 1)으로 계산해야 하며, 다른 쌍과 한 배치로 묶어 계산하지 않아야 한다(MUST NOT). 같은 쌍에 대한 응답은 다른 요청과 상관없이 항상 같아야 한다(SHALL). 결합이 없는 약물(원자 1개)도 예측할 수 있어야 한다(SHALL).

#### Scenario: 반복 요청
- **WHEN** 같은 쌍을 다른 쌍 요청 사이사이에 여러 번 요청하면
- **THEN** 매번 같은 관계와 확률이 돌아온다

#### Scenario: 결합이 없는 약물
- **WHEN** 원자가 하나뿐인 DSN-DDI 약물이 포함된 쌍을 요청하면
- **THEN** 에러 없이 예측 결과가 돌아온다

### Requirement: 학습셋 포함 여부로 모델을 고른다
두 약물이 모두 transductive 학습셋(`drugbank/fold0/train.csv`에 나온 약물)에 있으면 transductive 모델을, 하나라도 없으면 inductive 모델을 써야 한다(SHALL). 응답에는 사용한 모델과 각 약물의 학습셋 포함 여부가 들어 있어야 한다(SHALL).

#### Scenario: 학습셋 밖 약물
- **WHEN** fold0 train에 나오지 않는 DSN-DDI 약물(20개 중 하나)이 포함된 쌍을 요청하면
- **THEN** inductive 모델로 예측하고, 응답에 `model_used = inductive`와 해당 약물이 학습셋 밖이라는 표시가 있다

### Requirement: SMILES로 신약을 입력받는다
서버는 DrugBank ID 대신 SMILES 문자열을 받아, 원 저장소의 `atom_features`와 같은 방식으로 분자 그래프를 만들어야 한다(SHALL). SMILES를 해석할 수 없으면 에러를 돌려줘야 한다(SHALL). 원자 기호가 원 저장소의 원자 목록에 없어서 `Unknown`으로 처리된 원자가 있으면, 응답에 그 사실을 표시해야 한다(SHALL).

#### Scenario: SMILES 입력
- **WHEN** 유효한 SMILES와 DrugBank ID 쌍을 요청하면
- **THEN** inductive 모델로 예측한 결과가 돌아온다

#### Scenario: 해석할 수 없는 SMILES
- **WHEN** RDKit이 읽지 못하는 문자열을 SMILES로 보내면
- **THEN** 예측 없이 에러 메시지가 돌아온다

#### Scenario: 원자 특징 unknown
- **WHEN** 원 저장소의 원자 목록에 없는 원소가 들어 있는 SMILES를 보내면
- **THEN** 예측 결과와 함께 unknown 원자가 있다는 표시가 돌아온다

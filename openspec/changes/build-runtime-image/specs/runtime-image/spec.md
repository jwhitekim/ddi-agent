# Spec Delta

## Purpose

B와 C가 공통으로 쓰는 DSN-DDI 런타임 이미지를 정의한다. 원 DSN-DDI 스크립트가 이 이미지 안에서 GPU로 논문 수치를 재현해야 하고, domain-specific ACI는 이미지에 들어가지 않아야 한다.

## ADDED Requirements

### Requirement: 이미지는 DSN-DDI 실행 환경을 고정 경로에 제공한다
이미지는 파이썬 3.7, PyTorch 1.9.0(CUDA 10.2), PyTorch Geometric 2.0.3, rdkit 2020.09.2가 설치된 DSN-DDI 환경(환경 ②)을 제공해야 한다(SHALL). 환경 ②의 파이썬 인터프리터는 문서에 적을 수 있는 고정 경로에 있어야 한다(SHALL).

#### Scenario: 환경 ② 버전 확인
- **WHEN** 컨테이너에서 환경 ② 파이썬으로 torch, torch_geometric, rdkit 버전을 출력하면
- **THEN** 각각 1.9.0, 2.0.3, 2020.09.2가 나오고 파이썬은 3.7이다

### Requirement: 이미지는 B·C 공통 재료를 포함한다
이미지는 다음을 포함해야 한다(SHALL): 고정 커밋의 DSN-DDI 저장소 코드, 가중치 2개(`transductive_drugbank.pkl`, `inductive_drugbank.pkl`), 압축을 푼 DSN-DDI 데이터, SSI-DDI 설명 파일 `Interaction_information.csv`. 데이터는 LFS 포인터 파일이 아니라 실제 파일이어야 한다(MUST).

#### Scenario: 데이터가 실제 파일임
- **WHEN** 컨테이너에서 원 스크립트가 읽는 `drugbank_test/drugbank/fold0/test.csv`를 열면
- **THEN** LFS 포인터 문자열이 아니라 `d1, d2, type` 칼럼을 가진 38,362행의 표가 나온다

#### Scenario: 설명 파일 존재
- **WHEN** 컨테이너에서 설명 파일을 열면
- **THEN** `Interaction type, Description, Subject, DDI type` 칼럼을 가진 86행이 나온다

### Requirement: 이미지는 domain-specific ACI를 포함하지 않는다
이미지 안에는 `ddi` 패키지, 예측 서버 코드, micro agent 프롬프트가 없어야 한다(MUST NOT). 그래야 이 이미지를 B 실험에 그대로 쓸 수 있다.

#### Scenario: ACI 흔적 없음
- **WHEN** 컨테이너 파일 시스템에서 `ddi` 패키지와 예측 서버 코드를 찾으면
- **THEN** 아무것도 나오지 않는다

### Requirement: 원 테스트 스크립트가 GPU로 논문 수치를 재현한다
원 DSN-DDI 테스트 스크립트(`drugbank_test/transductive_test.py`, `drugbank_test/inductive_test.py`)는 코드 수정 없이 컨테이너 안 GPU에서 실행되어야 한다(SHALL). 출력 지표는 논문 보고값과 비교해 기록해야 한다(SHALL).

#### Scenario: transductive 재현
- **WHEN** 컨테이너에서 GPU를 붙여 `python -u drugbank_test/transductive_test.py`를 실행하면
- **THEN** 에러 없이 test_acc 등 지표가 출력되고, 그 값이 논문의 DrugBank transductive 결과와 함께 재현 기록에 남는다

#### Scenario: inductive 재현
- **WHEN** 컨테이너에서 GPU를 붙여 `python -u drugbank_test/inductive_test.py`를 실행하면
- **THEN** 에러 없이 s1, s2 지표가 출력되고, 그 값이 논문의 inductive 결과와 함께 재현 기록에 남는다

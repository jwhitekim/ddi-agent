# Spec Delta

## MODIFIED Requirements

### Requirement: 이미지는 B·C 공통 재료를 포함한다
이미지는 다음을 포함해야 한다(SHALL): 고정 커밋의 DSN-DDI 저장소 코드, 가중치 2개(`transductive_drugbank.pkl`, `inductive_drugbank.pkl`), 압축을 푼 DSN-DDI 데이터, SSI-DDI 설명 파일 `Interaction_information.csv`, DrugBank 약물 이름 사전 `drugbank_vocabulary.csv`. 데이터는 LFS 포인터 파일이 아니라 실제 파일이어야 한다(MUST).

#### Scenario: 데이터가 실제 파일임
- **WHEN** 컨테이너에서 원 스크립트가 읽는 `drugbank_test/drugbank/fold0/test.csv`를 열면
- **THEN** LFS 포인터 문자열이 아니라 `d1, d2, type` 칼럼을 가진 38,362행의 표가 나온다

#### Scenario: 설명 파일 존재
- **WHEN** 컨테이너에서 설명 파일을 열면
- **THEN** `Interaction type, Description, Subject, DDI type` 칼럼을 가진 86행이 나온다

#### Scenario: 약물 이름 사전 존재
- **WHEN** 컨테이너에서 `/opt/DSN-DDI/drugbank_vocabulary.csv`를 열면
- **THEN** `DrugBank ID, Common name, Synonyms` 등의 칼럼을 가진 13,475개 약물이 나온다

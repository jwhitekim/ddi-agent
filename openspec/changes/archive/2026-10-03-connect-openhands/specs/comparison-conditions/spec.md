# Spec Delta

## MODIFIED Requirements

### Requirement: B와 C는 같은 런타임 재료를 받는다
조건 B와 C는 모두 다음을 받아야 한다(SHALL): 환경 ①, 환경 ②(파이썬 3.7, PyTorch 1.9.0, PyG 2.0.3), DSN-DDI 저장소 코드(가중치를 불러오는 데 필요한 모델 정의 포함), 가중치 2개(transductive, inductive), 압축을 푼 DSN-DDI 데이터(저장소의 LFS 포인터 파일 대신), SSI-DDI 관계 설명 파일, DrugBank 약물 이름 사전(`/opt/DSN-DDI/drugbank_vocabulary.csv`, 약물 이름·동의어 → DrugBank ID), 그리고 환경 ② 인터프리터 위치를 알려주는 안내 한 줄.

#### Scenario: B가 모델을 직접 실행
- **WHEN** B가 상호작용을 예측하려고 하면
- **THEN** B는 안내 한 줄로 환경 ②를 찾아 직접 쓴 추론 스크립트를 실행할 수 있고, LFS 다운로드나 환경 설치 없이 관계 번호 출력까지 도달할 수 있다

#### Scenario: B가 관계를 해석
- **WHEN** B가 관계 번호를 문장으로 바꾸려고 하면
- **THEN** 컨테이너 안에 SSI-DDI 설명 파일이 있어서 B가 그 파일을 읽을 수 있다

#### Scenario: B가 약물 이름을 찾음
- **WHEN** B가 질문의 영어 약물 이름(예: Warfarin)을 DrugBank ID로 바꾸려고 하면
- **THEN** 컨테이너 안의 DrugBank 약물 이름 사전에서 `DB00682`를 찾을 수 있다

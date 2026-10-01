# Tasks

## 1. 예측 서버

- [x] 1.1 `server/predictor.py`에 원 `data_preprocessing`을 재사용해 쌍 하나(배치 크기 1)에 `rels=[[0..85]]`를 넘겨 86개 관계 확률을 계산하는 함수를 만든다(모델 선택, SMILES 입력, unknown 원자 표시, 결합 없는 약물의 빈 간선 `(2,0)` 처리 포함). 확인: `ddi-runtime` 컨테이너(GPU)에서 fold0 test 쌍 20개에 대해, 원 `DrugDataset.collate_fn` 양성 샘플(배치 크기 1)로 얻은 확률과 소수점 4자리까지 같다
- [x] 1.2 `server/app.py`에 `http.server` 기반 `GET /health`, `POST /predict`(127.0.0.1:8765)를 만든다. 확인: 컨테이너 안에서 `curl`로 health가 두 모델 로드를 보고하고, Warfarin(DB00682)–Aspirin(DB00945) 예측이 확률 내림차순 3개를 돌려준다
- [x] 1.3 경계 입력을 시험한다: fold0 train 밖 약물(20개 중 하나), 유효한 SMILES, 잘못된 SMILES, 목록 밖 원소가 든 SMILES, 결합 없는 약물, 가장 큰 약물 쌍, 같은 쌍 반복 요청. 확인: 각각 inductive+학습셋 밖 표시 / inductive / 에러 / unknown 표시 / 에러 없이 응답 / GPU 메모리 에러 없이 응답 / 매번 같은 결과

## 2. ddi 패키지

- [x] 2.1 `ddi/` 패키지에 `dbvocab.csv`(sha256 확인)와 `Interaction_information.csv`, DSN-DDI 약물 목록을 패키지 데이터로 넣고 `resolve_drug`를 만든다. 확인: `python:3.11`에서 "Aspirin"→DB00945, "warfarin"→DB00682, 없는 이름→에러, DSN-DDI에 없는 약물→에러
- [x] 2.2 `explain`을 만든다. 확인: 관계 5·72·3 예시 문장이 spec과 같고, 0~85 전부 문장이 나오며 순서가 뒤집힌 관계가 42개다
- [x] 2.3 `predict`, `predict_many(relation=...)`를 만든다(경고 포함). 확인: 서버 컨테이너에 붙인 `python:3.11`에서 Warfarin–Aspirin 결과에 문장·확률·`model_used`가 있고, 6개 약물 15쌍이 15행으로 나오며, `relation` 필터가 동작하고, SMILES 신약에 경고가 붙는다
- [x] 2.4 `save_results`를 만든다. 확인: `predict_many` 결과를 저장한 CSV의 칼럼이 정확히 `drug_a, drug_b, relation, prob, model_used, description`이다
- [x] 2.5 공개 함수가 5개뿐인지 확인한다. 확인: `ddi.__all__`이 `resolve_drug, predict, predict_many, explain, save_results`이고, label을 돌려주는 함수가 없다

## 3. C 전용 이미지

- [x] 3.1 `docker/Dockerfile.specialist`(`FROM ddi-runtime`)에 `server/`와 `ddi/`를 넣고, 컨테이너 시작 시 서버를 띄운다. 확인: `docker run --gpus all ddi-specialist` 후 health가 정상이고, `ddi-runtime` 이미지에는 여전히 서버 코드와 `ddi` 패키지가 없다

## 4. 문서 반영

- [x] 4.1 `ddi-draft.md` 2.3절 함수 표에 확률의 의미(관계별 sigmoid, 합이 1이 아님), 모델 선택 기준(fold0 train), 쌍 하나씩 계산하는 이유(배치 섞임), 에러/경고 구분을 적고, 6.3절에 채점 기준도 쌍 하나씩 계산한다고 적고, 3.2절의 사전 출처를 `ferrangoeh/DrugLinker`(`druglinker/dbvocab.csv`)로 고친다. 확인: `grep -n "ferrangoeh" ddi-draft.md`와 `grep -n "sigmoid" ddi-draft.md`가 해당 절에서 보인다

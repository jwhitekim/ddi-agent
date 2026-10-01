# Tasks

## 1. 호스트 GPU 준비 (관리자 권한 필요 — 사용자가 직접 실행)

- [ ] 1.1 재부팅 등으로 NVIDIA 드라이버 불일치(커널 580.173 / 라이브러리 580.178)를 해소한다. 확인: 호스트에서 `nvidia-smi`가 V100 2장을 표시한다
- [ ] 1.2 nvidia-container-toolkit을 설치하고 Docker 런타임을 설정한다. 확인: `docker run --rm --gpus all ubuntu nvidia-smi`가 컨테이너 안에서 GPU를 표시한다

## 2. Dockerfile 작성 — 환경 ②

- [ ] 2.1 `docker/Dockerfile`에 Ubuntu + Miniconda 베이스와 conda 환경 `dsn`(파이썬 3.7)을 만들고, 원 `Install` 순서대로 pytorch 1.9.0 + cudatoolkit 10.2, PyG cu102 휠, torch-geometric 2.0.3, rdkit 2020.09.2, pandas, scikit-learn을 설치한다. 확인: `docker build`가 성공하고, `/opt/conda/envs/dsn/bin/python`으로 출력한 버전이 spec과 같다

## 3. Dockerfile 작성 — 공통 재료

- [ ] 3.1 저장소를 커밋 `6f23522`로 `/opt/DSN-DDI`에 클론한다. 확인: 컨테이너에서 `git -C /opt/DSN-DDI rev-parse --short HEAD`가 `6f23522`이고 가중치 2개의 크기가 6,391,544바이트다
- [ ] 3.2 LFS 미디어 URL에서 `DSN-DDI-dataset.zip`을 받아 sha256 `aab91c7f4cd9562bfe1af1e2a23b8d6747e701199ff4292b14cef33c82f97011`을 확인하고(다르면 빌드 실패), 압축을 풀어 스크립트가 읽는 경로(`drugbank_test/drugbank/`, `drugbank_test/inductive_data/`)에 배치한다. 확인: `drugbank_test/drugbank/fold0/test.csv`가 38,362행이고 `drugbank_test/inductive_data/fold3/s1.csv`가 존재한다
- [ ] 3.3 프로젝트 루트의 `Interaction_information.csv`를 `/opt/DSN-DDI/Interaction_information.csv`로 `COPY`한다. 확인: 컨테이너에서 86행과 4개 칼럼이 보인다
- [ ] 3.4 이미지에 `ddi` 패키지, 서버 코드, 프롬프트가 없는지 확인한다. 확인: 컨테이너에서 `find / -name "ddi*" -not -path "/proc/*"` 결과에 해당 파일이 없다

## 4. 원 스크립트 재현

- [ ] 4.1 `--gpus all`로 컨테이너를 띄우고 `/opt/DSN-DDI`에서 `python -u drugbank_test/transductive_test.py`를 실행한다. 확인: 에러 없이 test_acc, test_auc_roc 등이 출력된다
- [ ] 4.2 같은 방식으로 `python -u drugbank_test/inductive_test.py`를 실행한다. 확인: 에러 없이 s1, s2 지표가 출력된다
- [ ] 4.3 `docker/REPRODUCTION.md`에 빌드·실행 명령, 실제 지표, 논문 보고값(DSN-DDI 논문의 DrugBank transductive·inductive 표), 차이, 설치 중 대체한 패키지를 기록한다. 확인: 문서에 두 스크립트의 결과와 논문값이 나란히 있다

## 5. 문서 반영

- [ ] 5.1 `ddi_agent_proposal.md` 2.2절에 이미지의 고정 경로(저장소, 환경 ② 파이썬, 설명 파일)와 GPU(V100, CUDA 10.2) 사용을 적는다. 확인: `grep -n "/opt/conda/envs/dsn/bin/python" ddi_agent_proposal.md`가 2.2절에서 보인다

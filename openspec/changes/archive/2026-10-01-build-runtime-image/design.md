# Design

## Context

- 저장소(`microsoft/Drug-Interaction-Research`, 브랜치 `DSN-DDI-for-DDI-Prediction`, 최신 커밋 `6f23522`)를 확인한 결과:
  - 가중치 2개는 저장소에 일반 파일로 들어 있다(각 6.4MB). 둘은 서로 다른 파일이다.
  - 데이터 zip은 LFS 포인터다. 원본은 sha256 `aab91c7f…f97011`, 크기 175,585,526바이트다.
  - 가중치는 모델 객체째 저장(`torch.load`)되어 있고, 안의 텐서 79개가 모두 `cuda` 텐서다. 그래서 GPU가 없으면 원 스크립트가 로드 단계에서 실패한다.
  - 원 스크립트는 저장소 루트를 작업 폴더로 두고 `drugbank_test/...` 상대 경로로 데이터를 읽는다.
- 호스트: Tesla V100 32GB 2장(sm_70, CUDA 10.2 지원). 드라이버는 커널 모듈 580.173과 라이브러리 580.178이 맞지 않아 `nvidia-smi`가 실패한다. Docker에는 nvidia 런타임이 없다.
- 동기는 proposal.md의 Why를 참고한다.

## Goals / Non-Goals

**Goals:**
- `docker build` 한 번으로 재현 가능한 이미지를 만든다 (로컬 클론에 의존하지 않음)
- 원 스크립트를 수정하지 않고 GPU로 재현한다

**Non-Goals:**
- 환경 ①, OpenHands 연결 (다음 change)
- 예측 서버, `ddi` 패키지 (다음 change, C 전용)
- 재학습, twosides 데이터 평가

## Decisions

- **GPU로 실행한다.** 가중치가 cuda 텐서라서 GPU가 있으면 원 스크립트를 한 줄도 고치지 않아도 된다. 그러면 6.3절의 "원 스크립트로 정답 생성"을 그대로 지킬 수 있다.
  - 검토한 대안: CPU로 돌리면서 `map_location="cpu"`를 추가하기. 원 스크립트를 수정해야 해서 채택하지 않음.
- **CUDA 런타임은 `torch==1.9.0+cu102` pip 휠에 들어 있는 것을 쓴다.** 베이스 이미지는 CUDA 이미지 대신 일반 Ubuntu + Miniforge(conda-forge만 사용)를 쓴다. 이렇게 하면 호스트에는 드라이버만 있으면 된다. 오래된 `nvidia/cuda:10.2` 태그는 Docker Hub에서 사라졌을 수 있어 그 위험도 피한다.
  - 대안 1: `nvidia/cuda:10.2-*` 베이스. 위 이유로 채택하지 않음.
  - 대안 2: 원 `Install`처럼 conda `pytorch==1.9.0 cudatoolkit=10.2` + Miniconda. Anaconda 기본 채널은 이용약관 동의 절차가 필요하고, pip 휠 주소가 살아 있음을 확인해서 채택하지 않음 (구현 중 변경, `docker/REPRODUCTION.md` 참고).
- **버전은 원 `Install`과 같게 맞춘다.** conda로 python 3.7, rdkit 2020.09.2, pandas, scikit-learn을 설치하고, pip로 torch 1.9.0+cu102, PyG 휠(cu102, cp37), torch-geometric 2.0.3을 설치한다.
- **저장소는 빌드할 때 고정 커밋 `6f23522`로 클론한다.** 로컬 `Drug-Interaction-Research/` 클론은 분석용으로만 쓰고 이미지에 복사하지 않는다. 그래야 이미지가 로컬 상태에 의존하지 않는다.
- **데이터는 GitHub LFS 미디어 URL에서 직접 받는다.** 받은 뒤 sha256을 확인하고, 압축을 풀어 README대로 `drugbank_test/` 아래에 배치한다. `git lfs`는 설치하지 않는다.
  - 주의: README는 `dataset/inductive`를 복사하라고 하지만, 스크립트는 `drugbank_test/inductive_data/fold3/`을 읽는다. 압축을 푼 실제 폴더 이름을 보고 스크립트가 읽는 경로에 맞춘다.
- **고정 경로를 둔다.** 저장소는 `/opt/DSN-DDI`, 환경 ② 파이썬은 `/opt/conda/envs/dsn/bin/python`, 설명 파일은 `/opt/DSN-DDI/Interaction_information.csv`에 둔다. B·C에게 줄 "안내 한 줄"은 이 경로를 가리킨다.
- **설명 파일은 프로젝트 루트의 `Interaction_information.csv`를 `COPY`한다.** 파일이 작고(86행) SSI-DDI 저장소를 통째로 클론할 이유가 없다.

## Risks / Trade-offs

- [호스트 드라이버 복구에 재부팅과 관리자 권한이 필요함] → tasks 1번 그룹에서 먼저 처리하고, `docker run --gpus all ... nvidia-smi`로 확인한 뒤 진행한다
- [오래된 패키지(파이썬 3.7, PyG cu102 휠, rdkit 2020.09.2)를 받지 못할 수 있음] → 빌드 로그에서 실패 단계를 확인하고, pip 휠이나 다른 채널로 대체한다. 대체했다면 REPRODUCTION.md에 기록한다
- [DrugDataset이 negative 샘플을 무작위로 뽑아서 실행할 때마다 지표가 조금씩 다름] → 재현 기준은 정확히 같은 값이 아니라 "논문값과 비슷함"으로 두고, 실제 값과 차이를 기록한다
- [inductive 스크립트는 fold3을 읽는데, 문서 3.1·6.1절은 inductive fold0을 가정함] → 이번 change에서는 원 스크립트대로 fold3으로 재현만 한다. 작업 ④ 질문 세트를 어느 fold에서 뽑을지는 질문 세트 change에서 정한다
- [로컬 `Drug-Interaction-Research/`가 프로젝트 git에 추적되지 않은 채 남아 있음] → `.gitignore`에 추가할지는 사용자에게 따로 묻는다 (이번 change 범위 밖)

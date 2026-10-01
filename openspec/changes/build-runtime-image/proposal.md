# Proposal

## Why

B와 C 실험은 모두 DSN-DDI 모델이 돌아가는 같은 런타임 위에서 진행한다(`comparison-conditions` spec). 그런데 DSN-DDI는 파이썬 3.7, PyTorch 1.9.0, PyG 2.0.3이라는 옛날 환경이 필요하다. 데이터 zip은 Git LFS 포인터라 그냥 클론하면 받아지지 않고, 가중치는 GPU(cuda) 텐서로 저장되어 있다. 에이전트 연결이나 `ddi` 도구를 만들기 전에, 원 스크립트가 논문 수치를 재현하는 이미지부터 있어야 한다. 문서 7장 일정의 1~2일 차 작업이다.

## What Changes

- DSN-DDI 런타임 도커 이미지를 만든다 (Dockerfile 1개)
  - 환경 ②: 파이썬 3.7, PyTorch 1.9.0(CUDA 10.2), PyG 2.0.3, rdkit 2020.09.2
  - DSN-DDI 저장소 코드 (고정 커밋), 가중치 2개
  - 압축을 푼 데이터 (LFS 원본을 받아 해시 확인 후 압축 해제, README대로 배치)
  - SSI-DDI 설명 파일 `Interaction_information.csv`
  - 환경 ② 파이썬 위치를 고정 경로로 둠 (B·C에게 알려줄 "안내 한 줄"의 근거)
- 이미지 안에서 원 테스트 스크립트(transductive, inductive)를 GPU로 실행해 논문 수치를 재현하고 결과를 기록한다
- 호스트 준비: 드라이버 불일치 해소, nvidia-container-toolkit 설치
- 이미지에는 `ddi` 패키지와 예측 서버를 넣지 않는다. 이것들은 다음 change에서 C 전용으로 추가한다
- 환경 ①(코드 실행 환경)은 이번 change에서 만들지 않는다. OpenHands가 이 이미지를 바탕으로 자동 설치한다 (OpenHands 연결 change에서 확인)

## Capabilities

### New Capabilities
- `runtime-image`: B·C가 공통으로 쓰는 DSN-DDI 런타임 이미지에 들어가는 것, 들어가지 않는 것, 그리고 원 스크립트 재현 기준

### Modified Capabilities
(없음)

## Impact

- 새 파일: `docker/Dockerfile`, 재현 결과 기록 `docker/REPRODUCTION.md`
- 호스트: NVIDIA 드라이버 상태, nvidia-container-toolkit (관리자 권한 필요)
- 네트워크: 빌드할 때 GitHub(저장소, LFS 데이터 176MB), conda/pip 저장소 접근
- 다음 change(예측 서버와 `ddi` 도구, OpenHands 연결)가 이 이미지를 바탕으로 만들어짐

# DSN-DDI 재현 기록

기록일: 2026-10-01 · 이미지: `ddi-runtime` (`docker/Dockerfile`) · 저장소 커밋 `6f23522`

## 실행 환경

- 호스트: Ubuntu 22.04, Tesla V100-PCIE-32GB ×2, 드라이버 580.178.04, nvidia-container-toolkit
- 환경 ②: Python 3.7.12, torch 1.9.0+cu102, torch-geometric 2.0.3, rdkit 2020.09.2 (conda 패키지 기준)

## 명령

```bash
# 프로젝트 루트에서
docker build -f docker/Dockerfile -t ddi-runtime .
docker run --rm --gpus all --shm-size=8g ddi-runtime python -u drugbank_test/transductive_test.py
docker run --rm --gpus all --shm-size=8g ddi-runtime python -u drugbank_test/inductive_test.py
```

- 원 스크립트는 수정하지 않았다.
- `--shm-size=8g`: 스크립트의 DataLoader(`num_workers=2`)가 공유 메모리를 쓰기 때문에 넉넉하게 준다.
- transductive 1회 실행에 약 30초가 걸린다.

## 결과

**DrugBank transductive (fold0 test, 38,362건)** — 3회 실행

| 지표 | 1회 | 2회 | 3회 | 논문 |
|---|---|---|---|---|
| ACC | 0.9731 | 0.9733 | 0.9741 | 0.9694 |
| AUROC | 0.9957 | 0.9957 | 0.9958 | 0.9947 |
| AP | 0.9953 | – | – | 0.9937 (AUPR) |
| F1 | 0.9729 | 0.9732 | 0.9740 | 0.9693 |

**DrugBank inductive (스크립트 기본값 fold3)** — 1회 실행

| 지표 | S1 (신약–신약) | 논문 S1 | S2 (신약–기존 약) | 논문 S2 |
|---|---|---|---|---|
| ACC | 0.7466 | 0.7342 | 0.8248 | 0.8192 |
| AUROC | 0.8319 | 0.8179 | 0.9027 | 0.9101 |
| AP | 0.8353 | 0.8182 (AUPR) | 0.9014 | 0.9109 (AUPR) |
| F1 | 0.7143 | 0.7034 | 0.8223 | 0.8018 |

- 차이: 대부분 논문값보다 0.3~1.3%p 높고, S2의 AUROC와 AP만 약 0.8~1%p 낮다. 논문값은 여러 fold의 평균으로 보이고, 우리는 fold 하나(transductive fold0, inductive fold3)만 돌렸다. 또 negative 샘플을 무작위로 뽑아서 실행할 때마다 값이 조금씩 달라진다(transductive ACC 0.9731~0.9741). → **재현된 것으로 판단**
- README 요약의 "transductive 99% 이상"은 정확도가 아니라 AUROC(0.9947)를 말한다.
- 논문값 출처: 원 논문(Li et al., Brief. Bioinform. 2023)을 직접 열람하지 못했다. 대신 그 값을 비교 기준선으로 인용한 HDN-DDI(BMC Bioinformatics 2025)의 Table 2(warm-start)와 Table 3(cold-start)에서 가져왔다. ⚠️ 원문 표로 다시 확인할 것

## 계획(design.md)과 다르게 한 것

| 항목 | 계획 | 실제 | 이유 |
|---|---|---|---|
| conda 배포판 | Miniconda | Miniforge (conda-forge만 사용) | Anaconda 기본 채널의 이용약관 동의 절차를 피하려고 |
| PyTorch / CUDA | conda `pytorch==1.9.0 cudatoolkit=10.2` | pip `torch==1.9.0+cu102` 휠 (CUDA 10.2 런타임 포함) | design.md에서 허용한 대체 방식. 휠 주소가 살아 있음을 확인 |
| 데이터 폴더 | README: `dataset/inductive` | `dataset/inductive_data` | zip 안의 실제 이름이 이것이고, 스크립트도 이 이름을 읽음 |

## 참고 사항

- rdkit: 설치된 conda 패키지는 2020.09.2인데, `rdkit.__version__`은 `2020.09.1`로 출력된다(빌드의 버전 문자열 문제로 보임).
- 이미지 안에 `ddi` 패키지, 예측 서버 코드, 프롬프트가 없음을 확인했다(B 실험에 그대로 사용 가능).

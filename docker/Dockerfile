# DSN-DDI 런타임 이미지 (B·C 공통). 프로젝트 루트에서 빌드:
#   docker build -f docker/Dockerfile -t ddi-runtime .
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git unzip libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Miniforge (conda-forge 채널만 사용)
RUN curl -fsSL -o /tmp/miniforge.sh \
        https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh \
    && bash /tmp/miniforge.sh -b -p /opt/conda && rm /tmp/miniforge.sh

# 환경 ②: python 3.7 + rdkit (conda), PyTorch 1.9.0 cu102 + PyG 2.0.3 (pip, 원 Install 스크립트의 휠)
RUN /opt/conda/bin/conda create -y -n dsn python=3.7 rdkit=2020.09.2 pandas scikit-learn \
    && /opt/conda/bin/conda clean -afy
ARG PYG=https://data.pyg.org/whl/torch-1.9.0%2Bcu102
RUN /opt/conda/envs/dsn/bin/pip install --no-cache-dir \
        https://download.pytorch.org/whl/cu102/torch-1.9.0%2Bcu102-cp37-cp37m-linux_x86_64.whl \
    && /opt/conda/envs/dsn/bin/pip install --no-cache-dir \
        ${PYG}/torch_scatter-2.0.9-cp37-cp37m-linux_x86_64.whl \
        ${PYG}/torch_sparse-0.6.12-cp37-cp37m-linux_x86_64.whl \
        ${PYG}/torch_cluster-1.5.9-cp37-cp37m-linux_x86_64.whl \
        ${PYG}/torch_spline_conv-1.2.1-cp37-cp37m-linux_x86_64.whl \
        torch-geometric==2.0.3

# DSN-DDI 저장소 (고정 커밋). zip은 LFS 포인터라 아래에서 따로 받음
RUN git clone -b DSN-DDI-for-DDI-Prediction \
        https://github.com/microsoft/Drug-Interaction-Research.git /opt/DSN-DDI \
    && git -C /opt/DSN-DDI checkout 6f23522264ccd1efee202f4949e150a156181edc

# 데이터: LFS 원본을 받아 해시 확인 후 스크립트가 읽는 경로에 배치
RUN cd /tmp \
    && curl -fsSL -o ds.zip \
        https://media.githubusercontent.com/media/microsoft/Drug-Interaction-Research/DSN-DDI-for-DDI-Prediction/DSN-DDI-dataset.zip \
    && echo "aab91c7f4cd9562bfe1af1e2a23b8d6747e701199ff4292b14cef33c82f97011  ds.zip" | sha256sum -c - \
    && unzip -q ds.zip \
    && cp -r dataset/drugbank dataset/inductive_data /opt/DSN-DDI/drugbank_test/ \
    && rm -rf ds.zip dataset

# SSI-DDI 관계 설명 파일
COPY ddi/data/Interaction_information.csv /opt/DSN-DDI/Interaction_information.csv
# DrugBank 약물 이름 사전 (약물 이름·동의어 -> DrugBank ID, CC0, ferrangoeh/DrugLinker)
COPY ddi/data/dbvocab.csv /opt/DSN-DDI/drugbank_vocabulary.csv

WORKDIR /opt/DSN-DDI
ENV PATH=/opt/conda/envs/dsn/bin:$PATH

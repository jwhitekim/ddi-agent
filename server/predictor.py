"""DSN-DDI 관계 점수 계산 (환경 ②, 작업 폴더 /opt/DSN-DDI 에서 import).

원 저장소의 data_preprocessing 을 그대로 재사용해 그래프를 만들므로
원 모델과 같은 점수를 낸다.
"""
import os
import sys

import pandas as pd
import torch
from rdkit import Chem
from torch_geometric.data import Batch, Data

sys.path.insert(0, os.path.join(os.getcwd(), 'drugbank_test'))
import data_preprocessing as dp  # noqa: E402  (import 시 drugbank_test/drugbank/*.csv 를 읽음)
import models  # noqa: E402,F401  (torch.load 가 모델 클래스를 찾을 때 필요)

N_RELATIONS = 86
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

# 원 atom_features 의 원소 목록. 여기에 없으면 'Unknown' 으로 인코딩된다.
KNOWN_ATOM_SYMBOLS = {
    'C', 'N', 'O', 'S', 'F', 'Si', 'P', 'Cl', 'Br', 'Mg', 'Na', 'Ca', 'Fe', 'As', 'Al', 'I', 'B', 'V', 'K', 'Tl',
    'Yb', 'Sb', 'Sn', 'Ag', 'Pd', 'Co', 'Se', 'Ti', 'Zn', 'H', 'Li', 'Ge', 'Cu', 'Au', 'Ni', 'Cd', 'In',
    'Mn', 'Zr', 'Cr', 'Pt', 'Hg', 'Pb',
}

_train = pd.read_csv('drugbank_test/drugbank/fold0/train.csv')
TRAIN_DRUGS = set(_train['d1']) | set(_train['d2'])
DSN_DRUGS = set(dp.MOL_EDGE_LIST_FEAT_MTX)

MODELS = {
    name: torch.load('drugbank_test/%s_drugbank.pkl' % name, map_location=DEVICE).eval()
    for name in ('transductive', 'inductive')
}


class InputError(ValueError):
    """요청한 약물을 그래프로 만들 수 없음."""


def _drug_graph(drug):
    """drug: DrugBank ID 문자열 또는 {"smiles": ...}. (mol, edge_index, features, info) 반환."""
    if isinstance(drug, dict):
        smiles = str(drug.get('smiles', '')).strip()
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        if mol is None:
            raise InputError('SMILES를 해석할 수 없습니다: %r' % smiles)
        edge_index, feats = dp.get_mol_edge_list_and_feat_mtx(mol)
        is_new = True
    else:
        if drug not in DSN_DRUGS:
            raise InputError('DSN-DDI 데이터에 없는 약물입니다: %r' % drug)
        mol = dp.drug_to_mol_graph[drug]
        edge_index, feats = dp.MOL_EDGE_LIST_FEAT_MTX[drug]
        is_new = False
    if edge_index.numel() == 0:
        # 결합 없는 분자: 원 코드의 빈 간선은 1차원이라 배치 크기 1에서 PyG 가 처리하지 못함
        edge_index = torch.empty((2, 0), dtype=torch.long)
    unknown = sorted({a.GetSymbol() for a in mol.GetAtoms()} - KNOWN_ATOM_SYMBOLS)
    info = {
        'is_new': is_new,
        'in_train': (not is_new) and drug in TRAIN_DRUGS,
        'unknown_atoms': unknown,
    }
    return mol, edge_index, feats, info


def check_smiles(smiles):
    return Chem.MolFromSmiles(str(smiles).strip()) is not None


def score_pair(d1, d2, relations=None, model_name=None):
    """(d1, d2) 에 대해 각 관계의 확률(sigmoid)을 계산. model_name 이 없으면 학습셋 포함 여부로 고른다."""
    mol_h, ei_h, x_h, info_h = _drug_graph(d1)
    mol_t, ei_t, x_t, info_t = _drug_graph(d2)
    if model_name is None:
        model_name = 'transductive' if info_h['in_train'] and info_t['in_train'] else 'inductive'
    relations = list(range(N_RELATIONS)) if relations is None else list(relations)

    # 쌍 하나만 넣는다(배치 크기 1). 여러 쌍을 묶으면 이분 그래프 GATConv 의 self-loop 가
    # 배치 전체 원자 번호 기준으로 붙어 다른 쌍과 섞인다. 관계는 마지막 RESCAL 에서만 쓰이므로
    # rels 에 관계 목록을 넘기면 한 번의 forward 로 모든 관계 점수를 얻는다.
    h_data = Data(x=x_h.clone(), edge_index=ei_h)
    t_data = Data(x=x_t.clone(), edge_index=ei_t)
    b_data = dp.BipartiteData(dp.get_bipartite_graph(mol_h, mol_t), h_data.x, t_data.x)
    triple = (
        Batch.from_data_list([h_data]),
        Batch.from_data_list([t_data]),
        torch.LongTensor(relations).unsqueeze(0),
        Batch.from_data_list([b_data]),
    )
    triple = [x.to(device=DEVICE) for x in triple]
    with torch.no_grad():
        probs = torch.sigmoid(MODELS[model_name](triple)).cpu().tolist()
    return {
        'probs': dict(zip(relations, probs)),
        'model_used': model_name,
        'd1': info_h,
        'd2': info_t,
    }


def predict(d1, d2, top_k=3):
    res = score_pair(d1, d2)
    ranked = sorted(res.pop('probs').items(), key=lambda kv: kv[1], reverse=True)
    res['top'] = [{'relation': r, 'prob': p} for r, p in ranked[:top_k]]
    return res

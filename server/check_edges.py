"""작업 1.3 확인: 경계 입력 (서버 컨테이너 안에서 실행: python /opt/ddi-server/check_edges.py)."""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import predictor as P  # noqa: E402  (테스트할 약물을 고르는 데만 사용)


def post(d1, d2):
    req = urllib.request.Request('http://127.0.0.1:8765/predict', json.dumps({'d1': d1, 'd2': d2}).encode())
    try:
        return 200, json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


not_train = sorted(P.DSN_DRUGS - P.TRAIN_DRUGS)[0]
no_bond = sorted(d for d in P.DSN_DRUGS if P.dp.MOL_EDGE_LIST_FEAT_MTX[d][0].numel() == 0)[0]
by_size = sorted(P.DSN_DRUGS, key=lambda d: P.dp.drug_to_mol_graph[d].GetNumAtoms())
WARF = 'DB00682'
cases = [
    ('학습셋 밖 약물 %s' % not_train, not_train, WARF, lambda c, r: c == 200 and r['model_used'] == 'inductive' and not r['d1']['in_train']),
    ('유효한 SMILES(ibuprofen)', {'smiles': 'CC(C)Cc1ccc(cc1)C(C)C(=O)O'}, WARF, lambda c, r: c == 200 and r['model_used'] == 'inductive' and r['d1']['is_new']),
    ('잘못된 SMILES', {'smiles': 'Warfarn'}, WARF, lambda c, r: c == 400 and 'error' in r),
    ('목록 밖 원소(Ba)', {'smiles': 'CC(=O)O[Ba]OC(C)=O'}, WARF, lambda c, r: c == 200 and r['d1']['unknown_atoms'] == ['Ba']),
    ('결합 없는 약물 %s' % no_bond, no_bond, WARF, lambda c, r: c == 200 and len(r['top']) == 3),
    ('가장 큰 쌍 %s+%s' % (by_size[-1], by_size[-2]), by_size[-1], by_size[-2], lambda c, r: c == 200),
    ('DSN-DDI에 없는 ID', 'DB99999', WARF, lambda c, r: c == 400),
]
ok = True
for name, d1, d2, check in cases:
    code, res = post(d1, d2)
    passed = check(code, res)
    ok &= passed
    print('%-4s %s -> %s' % ('OK' if passed else 'FAIL', name, json.dumps(res, ensure_ascii=False)[:160]))

first = post('DB00641', 'DB01211')[1]['top']
same = all(post('DB00641', 'DB01211')[1]['top'] == first for _ in range(3) if post(by_size[-1], WARF))
print('%-4s 같은 쌍 반복 요청(다른 요청 사이사이)' % ('OK' if same else 'FAIL'))
ok &= same
print('ALL OK' if ok else 'SOME FAILED')

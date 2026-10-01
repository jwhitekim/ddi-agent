"""작업 1.1 확인: predictor 확률 == 원 DrugDataset.collate_fn 양성 샘플(배치 크기 1) 확률 (fold0 test 20쌍).

실행 (ddi-runtime 컨테이너, /opt/DSN-DDI 에서): python /srv/server/check_original.py
"""
import os
import sys

import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import predictor  # noqa: E402
from data_preprocessing import DrugDataset  # noqa: E402

df = pd.read_csv('drugbank_test/drugbank/fold0/test.csv').sample(20, random_state=0)
tups = [(h, t, r) for h, t, r in zip(df['d1'], df['d2'], df['type'])]
ds = DrugDataset(tups, disjoint_split=False, shuffle=False)

max_diff = 0.0
for h, t, r in tups:
    pos_tri, _ = ds.collate_fn([(h, t, r)])
    pos_tri = [x.to(device=predictor.DEVICE) for x in pos_tri]
    with torch.no_grad():
        orig = torch.sigmoid(predictor.MODELS['transductive'](pos_tri)).item()
    ours = predictor.score_pair(h, t, relations=[r], model_name='transductive')['probs'][r]
    full = predictor.score_pair(h, t, model_name='transductive')['probs'][r]  # 86개 관계를 한 번에 넘긴 값
    diff = max(abs(orig - ours), abs(orig - full))
    max_diff = max(max_diff, diff)
    print('%s %s r=%2d orig=%.6f single=%.6f all86=%.6f' % (h, t, r, orig, ours, full))

print('max |diff| = %.2e' % max_diff)
assert max_diff < 5e-5, 'mismatch'
print('OK')

"""작업 2.1~2.5 확인. 서버 컨테이너 네트워크에 붙인 python:3.11 에서 실행:
docker run --rm --network container:<서버> -v $PWD:/w -w /w python:3.11 python ddi_tests/check_ddi.py
"""
import csv
import itertools
import os
import tempfile

import ddi

ok = True


def check(name, cond, detail=''):
    global ok
    ok &= bool(cond)
    print('%-4s %s %s' % ('OK' if cond else 'FAIL', name, detail))


def raises(f, *a):
    try:
        f(*a)
        return None
    except (ValueError, RuntimeError) as e:
        return str(e)


# 2.1 resolve_drug
r = ddi.resolve_drug('Aspirin')
check('2.1 Aspirin', r['drugbank_id'] == 'DB00945' and r['name'] == 'Acetylsalicylic acid', r)
check('2.1 warfarin', ddi.resolve_drug('warfarin')['drugbank_id'] == 'DB00682')
check('2.1 DrugBank ID', ddi.resolve_drug('db00641')['name'] == 'Simvastatin')
check('2.1 없는 이름', raises(ddi.resolve_drug, 'Notadrug123'), raises(ddi.resolve_drug, 'Notadrug123'))
check('2.1 DSN-DDI에 없는 약물', raises(ddi.resolve_drug, 'Lepirudin'), raises(ddi.resolve_drug, 'Lepirudin'))
check('2.1 SMILES', ddi.resolve_drug('CC(C)Cc1ccc(cc1)C(C)C(=O)O')['is_new'])

# 2.2 explain
check('2.2 관계 5', ddi.explain(5, 'Warfarin', 'Acetylsalicylic acid') == 'Acetylsalicylic acid may increase the anticoagulant activities of Warfarin.')
check('2.2 관계 72', ddi.explain(72, 'Simvastatin', 'Clarithromycin') == 'The serum concentration of Simvastatin can be increased when it is combined with Clarithromycin.')
check('2.2 관계 3', ddi.explain(3, 'Carbamazepine', 'Simvastatin') == 'The metabolism of Simvastatin can be increased when combined with Carbamazepine.')
sents = [ddi.explain(t, 'AAA', 'BBB') for t in range(86)]
swapped = sum(s == ddi._RELATIONS[t + 1][0].replace('#Drug1', 'BBB').replace('#Drug2', 'AAA') for t, s in enumerate(sents))
check('2.2 86종 문장, 뒤집힌 관계 42개', len(sents) == 86 and swapped == 42, 'swapped=%d' % swapped)

# 2.3 predict / predict_many
p = ddi.predict('Warfarin', 'Aspirin')
check('2.3 Warfarin–Aspirin', p['top'][0]['relation'] == 5 and p['top'][0]['description'].startswith('Acetylsalicylic acid may increase')
      and p['model_used'] == 'transductive' and len(p['top']) == 3, [(t['relation'], round(t['prob'], 4)) for t in p['top']])
six = ['Warfarin', 'Aspirin', 'Simvastatin', 'Clarithromycin', 'Carbamazepine', 'Fluconazole']
pairs = list(itertools.combinations(six, 2))
many = ddi.predict_many(pairs)
rows = many.to_dict('records') if hasattr(many, 'to_dict') else many
check('2.3 6개 약물 15쌍', len(rows) == 15 and all(not r['error'] for r in rows), 'type=%s' % type(many).__name__)
filt = ddi.predict_many(pairs, relation=72)
frows = filt.to_dict('records') if hasattr(filt, 'to_dict') else filt
check('2.3 relation=72 필터', 0 < len(frows) < 15 and all(r['relation'] == 72 for r in frows), '%d쌍' % len(frows))
mixed = ddi.predict_many([('Warfarin', 'Aspirin'), ('Warfarin', 'Notadrug123')])
mrows = mixed.to_dict('records') if hasattr(mixed, 'to_dict') else mixed
check('2.3 실패한 쌍은 error로 남김', len(mrows) == 2 and mrows[1]['error'], mrows[1]['error'])
n = ddi.predict('CC(C)Cc1ccc(cc1)C(C)C(=O)O', 'Warfarin')
check('2.3 SMILES 신약 경고', n['model_used'] == 'inductive' and any('신뢰도' in w for w in n['warnings']), n['warnings'])
u = ddi.predict('CC(=O)O[Ba]OC(C)=O', 'Warfarin')
check('2.3 unknown 원자 경고', any('Unknown' in w for w in u['warnings']))

# 2.4 save_results
with tempfile.TemporaryDirectory() as d:
    path = ddi.save_results(many, os.path.join(d, 'out.csv'))
    with open(path) as f:
        rd = list(csv.reader(f))
    check('2.4 CSV 칼럼', rd[0] == ['drug_a', 'drug_b', 'relation', 'prob', 'model_used', 'description'] and len(rd) == 16, rd[1])
    path = ddi.save_results(p, os.path.join(d, 'one.csv'))
    with open(path) as f:
        rd = list(csv.reader(f))
    check('2.4 predict 결과는 상위 3행', len(rd) == 4 and rd[1][0] == 'DB00682')

# 2.5 공개 함수
public = sorted(n for n in dir(ddi) if not n.startswith('_') and callable(getattr(ddi, n)) and getattr(getattr(ddi, n), '__module__', '') == 'ddi')
check('2.5 공개 함수 5개', sorted(ddi.__all__) == public == sorted(['resolve_drug', 'predict', 'predict_many', 'explain', 'save_results']), public)

print('ALL OK' if ok else 'SOME FAILED')

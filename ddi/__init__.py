"""DDI skill: DSN-DDI 예측을 위한 함수 모음 (환경 ①에서 import).

    resolve_drug(x)                  약물 이름·동의어·DrugBank ID·SMILES -> 표준 약물 정보
    predict(a, b, top_k=3)           상위 관계, 관계별 확률, 방향이 반영된 문장, 경고
    predict_many(pairs, relation=None, top_k=3)
                                     여러 쌍을 한 번에 예측, relation(번호 또는 목록)으로 거름
    explain(rel, a, b)               DSN-DDI 관계 번호 -> 방향이 반영된 문장
    save_results(results, path)      채점용 CSV 저장 (drug_a, drug_b, relation, prob, model_used, description)

확률은 관계마다 따로 계산한 값(sigmoid)이라 86개의 합이 1이 아니다.
예측은 모델의 추정이며 기록된 사실이 아니다.
"""
import csv
import json
import os
import re
import urllib.error
import urllib.request

__all__ = ['resolve_drug', 'predict', 'predict_many', 'explain', 'save_results']

SERVER_URL = os.environ.get('DDI_SERVER_URL', 'http://127.0.0.1:8765')
CSV_COLUMNS = ['drug_a', 'drug_b', 'relation', 'prob', 'model_used', 'description']
N_RELATIONS = 86

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
_ID_RE = re.compile(r'^DB\d{5}$', re.IGNORECASE)


def _load():
    names, by_common, by_synonym = {}, {}, {}
    with open(os.path.join(_DATA, 'dbvocab.csv'), encoding='utf-8') as f:
        for row in csv.DictReader(f):
            dbid, common = row['DrugBank ID'], row['Common name'].strip()
            names[dbid] = common
            by_common.setdefault(common.lower(), set()).add(dbid)
            for syn in (row['Synonyms'] or '').split(' | '):
                if syn.strip():
                    by_synonym.setdefault(syn.strip().lower(), set()).add(dbid)
    with open(os.path.join(_DATA, 'dsn_drugs.txt')) as f:
        dsn = {line.strip() for line in f if line.strip()}
    relations = {}
    with open(os.path.join(_DATA, 'Interaction_information.csv'), encoding='utf-8') as f:
        for row in csv.DictReader(f):
            relations[int(row['Interaction type'])] = (row['Description'], int(row['Subject']))
    return names, by_common, by_synonym, dsn, relations


_NAMES, _BY_COMMON, _BY_SYNONYM, _DSN, _RELATIONS = _load()


def _post(path, body):
    req = urllib.request.Request(SERVER_URL + path, json.dumps(body).encode('utf-8'),
                                 {'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise ValueError(json.loads(e.read()).get('error', str(e)))
    except urllib.error.URLError as e:
        raise RuntimeError('DSN-DDI 예측 서버(%s)에 연결할 수 없습니다: %s' % (SERVER_URL, e.reason))


def resolve_drug(x):
    """약물 표기를 표준 약물로 바꾼다. 모르는 약물이면 ValueError.

    반환: {'drugbank_id', 'name', 'smiles', 'is_new', 'in_dsn'}
    """
    text = str(x).strip()
    if _ID_RE.match(text):
        dbid = text.upper()
        if dbid not in _DSN:
            raise ValueError('%s은(는) DSN-DDI 데이터에 없는 약물이라 예측할 수 없습니다.' % dbid)
        return {'drugbank_id': dbid, 'name': _NAMES.get(dbid, dbid), 'smiles': None, 'is_new': False, 'in_dsn': True}

    key = text.lower()
    matches = _BY_COMMON.get(key) or _BY_SYNONYM.get(key) or set()
    if matches:
        in_dsn = sorted(m for m in matches if m in _DSN)
        if not in_dsn:
            raise ValueError('%r(%s)은(는) DSN-DDI 데이터에 없는 약물이라 예측할 수 없습니다.'
                             % (text, ', '.join(sorted(matches))))
        if len(in_dsn) > 1:
            cands = ', '.join('%s (%s)' % (m, _NAMES[m]) for m in in_dsn)
            raise ValueError('%r에 해당하는 약물이 여러 개입니다: %s. DrugBank ID로 지정하세요.' % (text, cands))
        dbid = in_dsn[0]
        return {'drugbank_id': dbid, 'name': _NAMES[dbid], 'smiles': None, 'is_new': False, 'in_dsn': True}

    if _post('/check_smiles', {'smiles': text}).get('valid'):
        return {'drugbank_id': None, 'name': 'the query compound', 'smiles': text, 'is_new': True, 'in_dsn': False}
    raise ValueError('%r을(를) 약물 이름, DrugBank ID, SMILES 어느 것으로도 찾을 수 없습니다.' % text)


def _label(x):
    """explain 에 넣을 약물 이름. DrugBank ID 면 대표 이름으로 바꾼다."""
    text = str(x).strip()
    return _NAMES.get(text.upper(), text) if _ID_RE.match(text) else text


def explain(rel, a, b):
    """DSN-DDI 관계 번호 rel (0~85) 를 (a, b) 쌍의 문장으로 바꾼다.

    DSN-DDI 번호 t 는 설명 파일의 Interaction type == t + 1 행에 대응하고,
    그 행의 Subject 가 2 이면 #Drug1 에 b, #Drug2 에 a 가 들어간다 (86종 중 42종).
    """
    rel = int(rel)
    if not 0 <= rel < N_RELATIONS:
        raise ValueError('관계 번호는 0~85 사이여야 합니다: %d' % rel)
    template, subject = _RELATIONS[rel + 1]
    d1, d2 = (_label(b), _label(a)) if subject == 2 else (_label(a), _label(b))
    return template.replace('#Drug1', d1).replace('#Drug2', d2)


def _key(drug):
    return drug['drugbank_id'] or drug['smiles']


def _payload(drug):
    return drug['drugbank_id'] if drug['drugbank_id'] else {'smiles': drug['smiles']}


def predict(a, b, top_k=3):
    """두 약물의 상위 관계를 예측한다.

    반환: {'drug_a', 'drug_b', 'model_used', 'top': [{'relation', 'prob', 'description'}], 'warnings'}
    """
    da, db = resolve_drug(a), resolve_drug(b)
    res = _post('/predict', {'d1': _payload(da), 'd2': _payload(db), 'top_k': int(top_k)})
    warnings = []
    for drug, info in ((da, res['d1']), (db, res['d2'])):
        drug['in_train'] = info['in_train']
        if info['is_new']:
            warnings.append('%s은(는) 신약(SMILES 입력)이라 inductive 모델로 예측했습니다. 신뢰도가 낮을 수 있습니다.'
                            % drug['smiles'])
        elif not info['in_train']:
            warnings.append('%s(%s)은(는) 학습셋에 없는 약물이라 inductive 모델로 예측했습니다. 신뢰도가 낮을 수 있습니다.'
                            % (drug['name'], drug['drugbank_id']))
        if info['unknown_atoms']:
            warnings.append('%s에 모델이 모르는 원소(%s)가 있어 원자 특징이 Unknown으로 처리됐습니다. 예측을 신뢰하기 어렵습니다.'
                            % (drug['name'] if drug['drugbank_id'] else drug['smiles'], ', '.join(info['unknown_atoms'])))
    top = [{'relation': t['relation'], 'prob': t['prob'],
            'description': explain(t['relation'], da['name'], db['name'])} for t in res['top']]
    return {'drug_a': da, 'drug_b': db, 'model_used': res['model_used'], 'top': top, 'warnings': warnings}


def predict_many(pairs, relation=None, top_k=3):
    """여러 쌍을 예측해 쌍마다 한 행씩 돌려준다 (pandas 가 있으면 DataFrame).

    relation 에 관계 번호(하나 또는 목록)를 주면, 상위 top_k 안에 그 관계가 있는 쌍만 남기고
    그 행의 relation/prob/description 은 일치한 관계 중 확률이 가장 높은 것으로 채운다.
    식별이나 예측에 실패한 쌍은 error 칸에 이유를 적어 남긴다.
    """
    wanted = None if relation is None else {int(r) for r in (relation if isinstance(relation, (list, tuple, set)) else [relation])}
    rows = []
    for a, b in pairs:
        try:
            res = predict(a, b, top_k)
        except (ValueError, RuntimeError) as e:
            rows.append({'drug_a': str(a), 'drug_b': str(b), 'name_a': str(a), 'name_b': str(b),
                         'relation': None, 'prob': None, 'model_used': None, 'description': None,
                         'top_relations': None, 'warnings': '', 'error': str(e)})
            continue
        hits = [t for t in res['top'] if wanted is None or t['relation'] in wanted]
        if not hits:
            continue
        best = hits[0]
        rows.append({'drug_a': _key(res['drug_a']), 'drug_b': _key(res['drug_b']),
                     'name_a': res['drug_a']['name'], 'name_b': res['drug_b']['name'],
                     'relation': best['relation'], 'prob': best['prob'], 'model_used': res['model_used'],
                     'description': best['description'],
                     'top_relations': [(t['relation'], round(t['prob'], 4)) for t in res['top']],
                     'warnings': ' '.join(res['warnings']), 'error': ''})
    try:
        import pandas as pd
        return pd.DataFrame(rows)
    except ImportError:
        return rows


def _rows_for_csv(results):
    if isinstance(results, dict) and 'top' in results:  # predict() 결과: 상위 관계마다 한 행
        a, b = _key(results['drug_a']), _key(results['drug_b'])
        return [{'drug_a': a, 'drug_b': b, 'relation': t['relation'], 'prob': t['prob'],
                 'model_used': results['model_used'], 'description': t['description']} for t in results['top']]
    if hasattr(results, 'to_dict'):  # DataFrame
        results = results.to_dict('records')
    return [{c: r.get(c) for c in CSV_COLUMNS} for r in results]


def save_results(results, path):
    """predict / predict_many 결과(또는 같은 칼럼의 표)를 채점용 CSV로 저장하고 경로를 돌려준다."""
    rows = _rows_for_csv(results)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: ('' if r[c] is None or r[c] != r[c] else r[c]) for c in CSV_COLUMNS})
    return path

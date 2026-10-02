---
name: ddi
type: repo
agent: CodeActAgent
---

# DSN-DDI 약물 상호작용 도구 (`ddi`)

이 환경의 IPython에는 `ddi` 패키지가 이미 import되어 있다. 약물 상호작용 예측은 반드시 `ddi` 함수로 하고, DSN-DDI 모델이나 저장소 스크립트를 직접 실행하지 않는다.

| 함수 | 하는 일 |
|---|---|
| `ddi.resolve_drug(x)` | 약물 이름·동의어·DrugBank ID·SMILES → 표준 약물 정보. 모르는 약물이면 에러 |
| `ddi.predict(a, b, top_k=3)` | 두 약물의 상위 관계(번호, 관계별 확률, 방향이 반영된 문장)와 경고 |
| `ddi.predict_many(pairs, relation=None, top_k=3)` | 여러 쌍을 한 번에 예측해 표로 반환. `relation`에 관계 번호(하나 또는 목록)를 주면 그 관계가 상위에 있는 쌍만 남김 |
| `ddi.explain(rel, a, b)` | 관계 번호를 (a, b) 순서가 반영된 문장으로 |
| `ddi.save_results(results, path)` | `predict` 또는 `predict_many` 결과를 채점용 CSV로 저장 |

사용 예:

```python
res = ddi.predict("Warfarin", "Aspirin")
for t in res["top"]:
    print(t["relation"], round(t["prob"], 3), t["description"])
print(res["warnings"])
ddi.save_results(res, "/workspace/result.csv")
```

- 관계 문장은 `predict`가 돌려준 `description`을 그대로 쓴다. 관계 번호를 직접 해석하지 않는다.
- 특정 종류의 관계를 찾을 때는 `ddi.explain(r, "A", "B")`로 관계 0~85의 문장을 확인해 해당 번호를 고른 뒤 `predict_many(..., relation=[...])`에 넘긴다.
- `warnings`가 있으면 답변에 함께 알린다 (학습셋 밖 약물, 신약, 모르는 원소 등).
- 확률은 관계마다 따로 계산한 값이라 합이 1이 아니다. 예측은 모델의 추정이며 기록된 사실이 아니다.
- 최종 결과는 `ddi.save_results`로 `/workspace`에 CSV로 저장한다.

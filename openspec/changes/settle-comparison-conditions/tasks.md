# Tasks

## 1. 머리말

- [ ] 1.1 `ddi_agent_proposal.md` 제목을 v0.6으로 바꾸고 v0.6 변경 내역 한 줄(B·C 받는 것 명시, `lookup_known` 삭제, `description` 칼럼 추가, C′ 삭제)을 추가한다. 확인: `grep -n "v0.6" ddi_agent_proposal.md`로 제목과 변경 내역이 보인다

## 2. 시스템 구성 (2.3절)

- [ ] 2.1 DDI skill 표에서 `lookup_known` 행을 삭제한다. 확인: `grep -n "lookup_known" ddi_agent_proposal.md` 결과에 2.3절 표의 행이 없다

## 3. 비교 조건 (4장)

- [ ] 3.1 4장 표의 B 행을 "CodeActAgent 그대로 + 공통 재료"로 바꾸고, 조건별로 받는 것을 표로 추가한다. A는 환경 없음, B·C 공통은 환경 ①②·가중치 2개·압축 푼 데이터·SSI-DDI 설명 파일·환경 ② 위치 안내 한 줄, C에게만 예측 서버·`ddi` skill·micro agent 프롬프트. 확인: 표에 세 조건과 이 항목들이 모두 있다
- [ ] 3.2 B를 실행할 때는 `ddi` 패키지와 서버 코드를 컨테이너에 두지 않는다는 문장과 각 결정의 이유(design.md Decisions)를 한 줄씩 추가한다. 확인: 4장에 해당 문장이 있다
- [ ] 3.3 C′ ablation 줄을 "하지 않음 (실험 단순화, 한계 절에 언급)"으로 바꾼다. 확인: `grep -n "C′" ddi_agent_proposal.md`에 "❓ 여유 시"가 남아 있지 않다

## 4. 평가 (6장)

- [ ] 4.1 6.2절의 채점용 CSV 칼럼에 `description`(방향이 반영된 최종 문장)을 추가하고, 사람용 답변 항목에서 "② 기록된 상호작용"을 삭제한 뒤 번호를 다시 매긴다. 확인: `grep -n "description" ddi_agent_proposal.md`로 6.2절이 보이고 "기록된 상호작용"이 6.2절에 없다
- [ ] 4.2 6.4절의 `lookup_known` 관련 ⚠️ 문단을 "에이전트는 정답을 볼 수 없음 — `lookup_known` 제거"로 바꾸고, 해석 정확도 정의에 `description` 비교라는 점을 적는다. 확인: `grep -n "lookup_known" ddi_agent_proposal.md` 결과가 v0.6 변경 내역과 이 해결 문장뿐이다

## 5. 결정이 남은 것 (8장)

- [ ] 5.1 8장 표의 #2를 "✅ 해결 — `lookup_known` 제거"로, #4를 "✅ 하지 않음"으로 바꾼다. 확인: 8장 표에 ⚠️와 ❓가 #1, #3, #5에만 남아 있다

## 6. 전체 확인

- [ ] 6.1 문서 전체에서 B의 조건 설명이 서로 어긋나는 곳이 없는지 확인한다(1.5, 2.1, 2.2, 4장). 확인: `grep -n "generalist agent" ddi_agent_proposal.md`로 나오는 위치들을 읽어 보고 모순이 없다

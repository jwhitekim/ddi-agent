"""OpenHands 0.62.0 헤드리스 실행 진입점 (run_agent.py 가 `python -m openhands.core.main` 대신 실행).

Vercel AI Gateway 를 쓸 때 프롬프트 캐싱을 켠다. 캐싱은 비용·속도에만 영향을 준다.
- 0.62.0 은 모델 이름 목록(claude-sonnet-4* 까지)으로 캐싱 대상을 정해서 Sonnet 5.5 에 캐시 표시를 붙이지 않고,
  litellm 프록시가 아니면 extra_body 도 지운다.
- 게이트웨이의 OpenAI 호환 API 는 providerOptions.gateway.caching = "auto" 를 주면 캐시 표시를 직접 붙인다.
그래서 OpenHands 가 litellm 을 부르는 함수를 감싸, 게이트웨이로 가는 요청에만 이 옵션을 넣는다.
OpenHands 소스는 바꾸지 않는다(바꾸면 런타임 이미지가 다시 빌드됨).
"""
import runpy

import openhands.llm.llm as oh_llm

_litellm_completion = oh_llm.litellm_completion


def _completion_with_gateway_caching(*args, **kwargs):
    if 'ai-gateway.vercel.sh' in str(kwargs.get('base_url') or ''):
        body = dict(kwargs.get('extra_body') or {})
        body.setdefault('providerOptions', {}).setdefault('gateway', {})['caching'] = 'auto'
        kwargs['extra_body'] = body
    return _litellm_completion(*args, **kwargs)


oh_llm.litellm_completion = _completion_with_gateway_caching
runpy.run_module('openhands.core.main', run_name='__main__')

"""조건(B/C)과 질문 하나로 OpenHands 0.62.0 CodeActAgent 를 실행하고 결과를 모은다.

    .venv-openhands/bin/python agent/run_agent.py \
        --condition C --task "Warfarin이랑 Aspirin 상호작용 예측해줘" --out runs/smoke_C

API 키는 환경 변수나 프로젝트 루트의 .env 에서 읽는다 (기본 AI_GATEWAY_API_KEY).
임시로 Gemini 를 직접 쓸 때: --model gemini/gemini-3.5-flash --base-url "" --api-key-env GEMINI_API_KEY

출력 폴더: config.toml, task.txt, workspace/, trajectory.json, openhands.log, results/*.csv, run_info.json
"""
import argparse
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import jinja2
from dotenv import load_dotenv

AGENT_DIR = Path(__file__).resolve().parent
REPO = AGENT_DIR.parent
load_dotenv(REPO / '.env')
BASE_IMAGES = {'B': 'ddi-runtime', 'C': 'ddi-specialist'}
MAX_ITERATIONS = 10

def render_config(condition, out, args):
    template = jinja2.Template((AGENT_DIR / 'config.toml.j2').read_text())
    return template.render(
        trajectory_path=str(out / 'trajectory.json'),
        llm_model=args.model,
        llm_base_url=args.base_url,
        reasoning_effort=args.reasoning_effort,
        base_image=BASE_IMAGES[condition],
        workspace=str(out / 'workspace'),
        # B·C 공통 재료 (런타임 이미지를 다시 빌드하지 않도록 마운트로도 넣는다)
        vocab=str(REPO / 'ddi' / 'data' / 'dbvocab.csv'),
        # C 전용: 현재 ddi 패키지와 서버 코드를 읽기 전용으로 연결 (이미지에 굳어진 옛 코드 대신 사용,
        # 런타임 이미지를 다시 빌드하지 않음). 이미지의 IPython 시작 파일이 커널 시작 시 import ddi 를 하고,
        # ddi 가 import 될 때 예측 서버를 띄운다.
        aci_mounts=('%s:/opt/ddi-skill/ddi:ro,%s:/opt/ddi-server:ro' % (REPO / 'ddi', REPO / 'server'))
        if condition == 'C' else None,
    )


def prepare(condition, task, out, args):
    if out.exists():
        sys.exit('출력 폴더가 이미 있습니다: %s' % out)
    workspace = out / 'workspace'
    if condition == 'C':
        shutil.copytree(AGENT_DIR / 'c_workspace', workspace)
    else:
        workspace.mkdir(parents=True)
    (out / 'config.toml').write_text(render_config(condition, out, args))
    (out / 'task.txt').write_text(task + (AGENT_DIR / 'task_suffix.txt').read_text())


def summarize(out):
    """trajectory 와 OpenHands 로그에서 종료 상태, 상호작용 턴 수, 토큰 사용량을 뽑는다."""
    status = 'unknown'
    log = (out / 'openhands.log').read_text(errors='replace') if (out / 'openhands.log').exists() else ''
    states = re.findall(r'to AgentState\.([A-Z_]+)', log)
    if states:
        status = states[-1].lower()
    if 'Agent reached maximum iteration' in log:
        status = 'max_iterations'
    trajectory_path = out / 'trajectory.json'
    if not trajectory_path.exists():
        return {'status': status, 'turns': None, 'tokens': None}
    events = json.loads(trajectory_path.read_text())
    turns = sum(1 for e in events if e.get('source') == 'agent' and e.get('action')
                and e.get('action') not in ('message', 'system', 'recall', 'change_agent_state'))
    tokens = None
    for e in reversed(events):
        usage = (e.get('llm_metrics') or {}).get('accumulated_token_usage')
        if usage:
            tokens = {k: usage.get(k) for k in ('prompt_tokens', 'completion_tokens', 'cache_read_tokens', 'cache_write_tokens')}
            break
    return {'status': status, 'turns': turns, 'tokens': tokens}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--condition', choices=sorted(BASE_IMAGES), required=True)
    p.add_argument('--task', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--model', default='openai/anthropic/claude-sonnet-5.5')
    p.add_argument('--base-url', default='https://ai-gateway.vercel.sh/v1')
    p.add_argument('--reasoning-effort', default='low')
    p.add_argument('--api-key-env', default='AI_GATEWAY_API_KEY')
    args = p.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        sys.exit('%s 환경 변수(또는 .env)가 필요합니다' % args.api_key_env)
    out = Path(args.out).resolve()
    prepare(args.condition, args.task, out, args)

    cmd = [sys.executable, '-m', 'openhands.core.main', '--config-file', str(out / 'config.toml'),
           '-f', str(out / 'task.txt'), '-c', 'CodeActAgent', '-i', str(MAX_ITERATIONS)]
    env = dict(os.environ, LLM_API_KEY=api_key)
    start = time.time()
    with open(out / 'openhands.log', 'w') as log:
        code = subprocess.call(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.time() - start

    results = out / 'results'
    results.mkdir()
    for csv_path in (out / 'workspace').rglob('*.csv'):
        shutil.copy(csv_path, results / csv_path.name)

    info = {
        'condition': args.condition,
        'task': args.task,
        'openhands_version': importlib.metadata.version('openhands-ai'),
        'agent': 'CodeActAgent',
        'base_image': BASE_IMAGES[args.condition],
        'model': args.model,
        'max_iterations': MAX_ITERATIONS,
        'exit_code': code,
        'seconds': round(elapsed, 1),
        'result_csvs': sorted(x.name for x in results.iterdir()),
        **summarize(out),
    }
    (out / 'run_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2))
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

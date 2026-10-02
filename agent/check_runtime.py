"""LLM 없이 OpenHands 런타임만 띄워 조건별 환경을 점검한다 (스모크 테스트 사전 확인).

    .venv-openhands/bin/python agent/check_runtime.py --condition C --out runs/check_C

확인: 런타임 빌드, (C) IPython 시작 파일로 서버 기동과 ddi 자동 import, 환경 ② GPU. (헤드리스 실행과 같게 setup 스크립트는 부르지 않음)
"""
import argparse
import sys
import types
from pathlib import Path

from openhands.core.config import OpenHandsConfig
from openhands.core.config.utils import load_from_toml
from openhands.core.setup import create_runtime
from openhands.events.action import CmdRunAction, IPythonRunCellAction
from openhands.utils.async_utils import call_async_from_sync

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_agent  # noqa: E402

CHECKS = [
    ('ipython: ddi 자동 import', IPythonRunCellAction(
        "try:\n    print('ddi' , ddi.predict('Warfarin', 'Aspirin')['top'][0])\n"
        "except NameError as e:\n    print('NO_DDI', e)")),
    ('bash: 예측 서버', CmdRunAction('curl -s http://127.0.0.1:8765/health || echo NO_SERVER')),
    ('bash: 환경 ② GPU', CmdRunAction(
        '/opt/conda/envs/dsn/bin/python -c "import torch; print(\'cuda\', torch.cuda.is_available())"')),
    ('bash: 환경 ① 파이썬', CmdRunAction('which python; python --version')),
    ('bash: micro agent 파일', CmdRunAction('ls /workspace/.openhands/microagents 2>&1 | head -3')),
    ('bash: ddi 패키지 파일', CmdRunAction('ls /opt/ddi-skill /opt/ddi-server 2>&1 | head -4')),
    ('bash: 공통 재료(설명 파일, 약물 사전)', CmdRunAction(
        'wc -l /opt/DSN-DDI/Interaction_information.csv /opt/DSN-DDI/drugbank_vocabulary.csv; '
        'grep -m1 -i ",Warfarin," /opt/DSN-DDI/drugbank_vocabulary.csv | cut -c1-60')),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--condition', choices=['B', 'C'], required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    out = Path(args.out).resolve()
    fake = types.SimpleNamespace(model='openai/none', base_url='http://127.0.0.1:1', reasoning_effort='low')
    run_agent.prepare(args.condition, '(runtime check)', out, fake)

    config = OpenHandsConfig()
    load_from_toml(config, str(out / 'config.toml'))
    runtime = create_runtime(config, headless_mode=True)
    call_async_from_sync(runtime.connect)
    try:
        for name, action in CHECKS:
            action.set_hard_timeout(300)
            obs = runtime.run_action(action)
            print('== %s\n%s' % (name, str(getattr(obs, 'content', obs)).strip()[:400]), flush=True)
    finally:
        runtime.close()


if __name__ == '__main__':
    main()

"""DSN-DDI 예측 서버 (환경 ②). /opt/DSN-DDI 에서 실행:
    python /opt/ddi-server/app.py

GET  /health                         -> 모델 로드 상태
POST /predict      {"d1", "d2", "top_k"} -> 상위 관계와 확률 (d1/d2: DrugBank ID 또는 {"smiles": ...})
POST /check_smiles {"smiles"}        -> RDKit 으로 읽을 수 있는지
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import predictor  # noqa: E402

HOST, PORT = '127.0.0.1', int(os.environ.get('DDI_SERVER_PORT', '8765'))
_gpu_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            self._send(200, {'status': 'ok', 'models': sorted(predictor.MODELS), 'device': predictor.DEVICE})
        else:
            self._send(404, {'error': 'not found'})

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            req = json.loads(self.rfile.read(length) or b'{}')
        except ValueError:
            return self._send(400, {'error': '요청 본문이 JSON이 아닙니다'})
        try:
            if self.path == '/predict':
                with _gpu_lock:
                    res = predictor.predict(req['d1'], req['d2'], int(req.get('top_k', 3)))
                return self._send(200, res)
            if self.path == '/check_smiles':
                return self._send(200, {'valid': predictor.check_smiles(req['smiles'])})
            return self._send(404, {'error': 'not found'})
        except KeyError as e:
            return self._send(400, {'error': '필드가 없습니다: %s' % e})
        except predictor.InputError as e:
            return self._send(400, {'error': str(e)})

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    print('DSN-DDI server on %s:%d (%s)' % (HOST, PORT, predictor.DEVICE), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

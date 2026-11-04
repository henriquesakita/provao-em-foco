"""Servidor local temporário para receber arquivos do navegador."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "2023"
OUT.mkdir(parents=True, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        qs = parse_qs(urlparse(self.path).query)
        name = qs.get("name", ["arquivo.pdf"])[0]
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)
        target = OUT / name
        target.write_bytes(data)
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(str(len(data)).encode())

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()

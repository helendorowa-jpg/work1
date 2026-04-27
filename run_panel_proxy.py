"""
本地运行“海外内容运营 AI 面板” + CORS 代理（零依赖）。

用途：
- 解决浏览器直连云端大模型接口时的 CORS/Failed to fetch
- 同时把 index.html 作为静态页提供

使用：
  cd 到本目录后运行：
    python run_panel_proxy.py

然后浏览器打开：
  http://127.0.0.1:5173/index.html

页面“设置”里，把 API Base URL 改为：
  http://127.0.0.1:5173/v1

（此时浏览器只请求本机同源地址，不会触发 CORS；本脚本会把 /v1/chat/completions 转发到你真正的云端 Base URL。）

安全提示：
- 该代理只在本机监听 127.0.0.1，不对局域网开放
- 推荐做法：把 API Key 放在本机环境变量里（UPSTREAM_API_KEY），避免在浏览器里保存敏感信息
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError


HOST = "127.0.0.1"
PORT = 5173
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 你要转发到的云端 OpenAI 兼容 Base URL（可通过环境变量覆盖）
# 例如：讯飞 MaaS: https://maas-api.cn-huabei-1.xf-yun.com/v2
UPSTREAM_BASE_URL = os.environ.get("UPSTREAM_BASE_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2").rstrip("/")
UPSTREAM_API_KEY = os.environ.get("UPSTREAM_API_KEY", "").strip()


def _read_body(handler: BaseHTTPRequestHandler) -> bytes:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0:
        return b""
    return handler.rfile.read(length)


class Handler(BaseHTTPRequestHandler):
    server_version = "OpsPanelProxy/1.0"

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        # 静态文件：index.html / 其它同目录资源（目前就一个文件）
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(ROOT_DIR, path.lstrip("/")))
        if not file_path.startswith(ROOT_DIR):
            self.send_response(403)
            self._send_cors()
            self.end_headers()
            self.wfile.write(b"Forbidden")
            return

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_response(404)
            self._send_cors()
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except OSError:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(b"Read file error")
            return

        content_type = "application/octet-stream"
        if file_path.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        elif file_path.endswith(".js"):
            content_type = "text/javascript; charset=utf-8"
        elif file_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"

        self.send_response(200)
        self._send_cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        # 仅代理 OpenAI compatible chat completions
        # 页面配置为 base_url=http://127.0.0.1:5173/v1 后，请求会打到 /v1/chat/completions
        if self.path.split("?", 1)[0] != "/v1/chat/completions":
            self.send_response(404)
            self._send_cors()
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        upstream_url = f"{UPSTREAM_BASE_URL}/chat/completions"
        body = _read_body(self)

        # 认证优先级：
        # 1) 若设置了 UPSTREAM_API_KEY（推荐），则由代理注入 Authorization
        # 2) 否则透传浏览器传来的 Authorization（不推荐把 key 存在浏览器）
        auth = ""
        if UPSTREAM_API_KEY:
            auth = f"Bearer {UPSTREAM_API_KEY}"
        else:
            auth = self.headers.get("Authorization", "")
        headers = {
            "Content-Type": "application/json",
        }
        if auth:
            headers["Authorization"] = auth

        req = urllib.request.Request(upstream_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                status = resp.status
                resp_headers = resp.headers
        except HTTPError as e:
            status = e.code
            data = e.read() if hasattr(e, "read") else str(e).encode("utf-8", "ignore")
            resp_headers = getattr(e, "headers", {})
        except URLError as e:
            status = 502
            data = json.dumps({"error": {"message": f"Upstream URLError: {e}"}}).encode("utf-8")
            resp_headers = {}

        self.send_response(status)
        self._send_cors()
        # 尽量回传 upstream content-type
        ct = None
        try:
            ct = resp_headers.get("Content-Type")
        except Exception:
            ct = None
        self.send_header("Content-Type", ct or "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        # 安静一点；需要可打开
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def main():
    os.chdir(ROOT_DIR)
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"Ops panel proxy running at http://{HOST}:{PORT}/index.html")
    print(f"Upstream base url: {UPSTREAM_BASE_URL}")
    if UPSTREAM_API_KEY:
        print("Upstream auth: using UPSTREAM_API_KEY from env (recommended)")
    else:
        print("Upstream auth: pass-through from browser Authorization header")
    print("Set page API Base URL to: http://127.0.0.1:5173/v1")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()


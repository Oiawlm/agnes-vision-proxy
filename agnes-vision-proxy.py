#!/usr/bin/env python3
"""
Hermes → Agnes 2.0 Flash 视觉代理
===================================
自动把 Hermes 发出的 base64 图片上传到 0x0.st 换公网 URL，
再转发给 Agnes API（Agnes 只吃公网 URL，不吃 base64）。

用法:
  1. 设置环境变量: set AGNES_API_KEY=sk-xxx
  2. 启动代理:     python D:\App\agnes-vision-proxy.py
  3. 配置 Hermes:  auxiliary.vision.base_url = http://localhost:8899/v1

0x0.st 免费图床，512MB 限制，文件保留 30 天+，无需注册。
"""

import json
import base64
import tempfile
import subprocess
import sys
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

AGNES_API = "https://apihub.agnes-ai.com/v1"
UPLOAD_URL = "https://0x0.st"
PORT = 8899


def get_agnes_key():
    """从环境变量或 Hermes .env 文件读取 Agnes API Key"""
    key = os.environ.get("AGNES_API_KEY", "")
    if key:
        return key

    # 回退：从 Hermes .env 文件读取
    env_paths = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", ".env"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "hermes", ".env"),
    ]
    for env_path in env_paths:
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("AGNES_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        if key:
                            return key
        except (FileNotFoundError, PermissionError):
            continue

    print("[proxy] 错误: 请设置环境变量 AGNES_API_KEY 或写入 Hermes .env", file=sys.stderr)
    sys.exit(1)


def upload_to_0x0st(filepath):
    """上传图片到 0x0.st，返回公网 URL"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "15", "--max-time", "30",
             "-F", f"file=@{filepath}", UPLOAD_URL],
            capture_output=True, text=True, timeout=35
        )
        url = result.stdout.strip()
        if url.startswith("http"):
            return url
        print(f"[proxy] 0x0.st 返回异常: {result.stdout[:200]}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("[proxy] 0x0.st 上传超时", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[proxy] 上传异常: {e}", file=sys.stderr)
        return None


def convert_base64_images(messages):
    """扫描 messages 里所有 base64 图片，上传并替换为公网 URL"""
    count = 0
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if part.get("type") != "image_url":
                continue
            url = part.get("image_url", {}).get("url", "")
            if not url.startswith("data:"):
                continue

            # 解析 data URL: data:image/png;base64,xxxxx
            match = re.match(r"data:([^;]+);base64,(.+)", url, re.DOTALL)
            if not match:
                continue

            mime_type = match.group(1)
            b64_data = match.group(2)
            ext = mime_type.split("/")[-1] if "/" in mime_type else "png"
            size_kb = len(b64_data) // 1024

            print(f"[proxy] 发现 base64 图片 ({size_kb}KB, {mime_type})", file=sys.stderr)

            # 解码存临时文件
            tmp_path = None
            try:
                raw = base64.b64decode(b64_data)
                with tempfile.NamedTemporaryFile(
                    suffix=f".{ext}", delete=False
                ) as f:
                    f.write(raw)
                    tmp_path = f.name

                # 上传
                public_url = upload_to_0x0st(tmp_path)
                if public_url:
                    part["image_url"]["url"] = public_url
                    count += 1
                    print(f"[proxy] ✓ {public_url}", file=sys.stderr)
                else:
                    print("[proxy] ✗ 上传失败，base64 保留不动", file=sys.stderr)
            except Exception as e:
                print(f"[proxy] 处理图片出错: {e}", file=sys.stderr)
            finally:
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

    return count


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器：拦截 → 转换 → 转发"""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # 转换 base64 图片
        messages = data.get("messages", [])
        n = convert_base64_images(messages)

        # 转发到 Agnes
        modified_body = json.dumps(data).encode("utf-8")
        req = Request(
            f"{AGNES_API}/chat/completions",
            data=modified_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AGNES_KEY}",
            },
        )

        try:
            with urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp.read())
        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"[proxy] Agnes 返回 {e.code}: {err_body[:300]}", file=sys.stderr)
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body.encode())
        except URLError as e:
            print(f"[proxy] 无法连接 Agnes: {e}", file=sys.stderr)
            self.send_error(502, f"上游不可达: {e}")

    def do_GET(self):
        if self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "object": "list",
                        "data": [
                            {
                                "id": "agnes-2.0-flash",
                                "object": "model",
                                "owned_by": "agnes",
                            }
                        ],
                    }
                ).encode()
            )
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        """精简日志输出"""
        print(f"[proxy] {args[0]}", file=sys.stderr)


def main():
    global AGNES_KEY
    AGNES_KEY = get_agnes_key()

    print(f"[proxy] 启动 → http://localhost:{PORT}", file=sys.stderr)
    print(f"[proxy] 上游 → {AGNES_API}", file=sys.stderr)
    print(f"[proxy] 图床 → {UPLOAD_URL}", file=sys.stderr)
    print(f"[proxy] 模型 → agnes-2.0-flash", file=sys.stderr)
    print("[proxy] 等待请求...", file=sys.stderr)

    server = HTTPServer(("127.0.0.1", PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[proxy] 已停止", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()

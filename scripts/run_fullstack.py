"""Full-stack dev launcher.

1. 启动后端（FastAPI）
2. 启动前端（Vite dev）
3. 自动在默认浏览器打开前端地址

用法：
    python scripts/run_fullstack.py

依赖：
    – Windows: 需已激活 venv 并在 PATH 中找到 npm
    – Linux/macOS 同理
"""

from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def start_backend() -> subprocess.Popen[str]:
    """启动 FastAPI 后端（非阻塞）。"""

    cmd = [sys.executable, str(ROOT / "scripts" / "run_backend.py")]
    return subprocess.Popen(cmd, cwd=ROOT)


# ------------------------------ FRONTEND ------------------------------
def start_frontend() -> subprocess.Popen[str] | None:
    """启动前端。

    1. 若 frontend/package.json 存在 → 认为是 Vite/React 项目，执行 `npm run dev`。
    2. 否则视为纯静态文件，直接用 python 内置 http.server 提供。
    """

    pkg = ROOT / "frontend" / "package.json"
    if pkg.exists():
        npm_exe = "npm.cmd" if sys.platform.startswith("win") else "npm"
        cmd = [npm_exe, "run", "dev", "--prefix", "frontend"]
        return subprocess.Popen(cmd, cwd=ROOT)

    # 静态目录：使用 python -m http.server 5173
    port = 5173
    cmd = [sys.executable, "-m", "http.server", str(port), "--directory", "frontend"]
    return subprocess.Popen(cmd, cwd=ROOT)


def main() -> None:  # noqa: D401
    print("[run_fullstack] 启动后端 …")
    backend_proc = start_backend()

    # 简单等待后端端口就绪；可根据需要调整时间或添加端口探测
    time.sleep(3)

    print("[run_fullstack] 启动前端 …")
    front_proc = start_frontend()

    time.sleep(2)
    print("[run_fullstack] 打开浏览器 http://localhost:5173 …")
    webbrowser.open("http://localhost:5173/index.html")

    try:
        if front_proc:
            front_proc.wait()
    finally:
        print("[run_fullstack] 关闭后端 …")
        backend_proc.terminate()
        backend_proc.wait(timeout=5)


if __name__ == "__main__":
    main() 
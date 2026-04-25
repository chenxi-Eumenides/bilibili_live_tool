"""入口重定向 — 请使用 python -m src 启动

TUI 入口已迁移至 src/tui/app.py
CLI 入口已迁移至 src/cli/main.py
"""

if __name__ == "__main__":
    from src.tui import run_tui
    run_tui()

"""TUI 用户层 — 入口"""
from .app import run_tui

FLAGS = frozenset({"--tui"})

def help_lines():
    return [
        "TUI 模式:",
        "  --tui                          启动 TUI",
    ]


def run():
    run_tui()

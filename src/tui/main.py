"""TUI 用户层 — 入口"""

FLAGS = frozenset({"--tui"})


def help_lines():
    return [
        "TUI 模式:",
        "  --tui                          启动 TUI",
    ]


def run():
    from .app import run_tui
    run_tui()

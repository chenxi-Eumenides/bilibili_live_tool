"""工具函数库."""

from os import environ


MODERN_ENV_VARS = [
    "WT_SESSION",
    "TERM_PROGRAM",
    "TERMINAL_EMULATOR",
    "KONSOLE_VERSION",
    "ALACRITTY_LOG",
    "KITTY_WINDOW_ID",
    "VTE_VERSION",
    "XTERM_VERSION",
    "WEZTERM_EXECUTABLE",
    "FOOT_META_FILE",
    "GHOSTTY_RESOURCES_DIR",
]

MODERN_TERM_NAMES = frozenset({
    "xterm-256color",
    "xterm-kitty",
    "alacritty",
    "tmux-256color",
    "wezterm",
})


def is_modern_terminal() -> bool:
    """判断终端是否支持半块字符.

    仅识别已知的现代终端 (Windows Terminal, iTerm2, Kitty 等),
    无法识别的默认走兼容模式 (`` + 空格).
    """
    if any(environ.get(v) for v in MODERN_ENV_VARS):
        return True
    return environ.get("TERM", "") in MODERN_TERM_NAMES

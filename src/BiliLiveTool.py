"""总入口"""

import sys


def _print_help():
    from .cli import cli_help
    print("B站直播管理工具")
    print("  --help          帮助信息")
    print("  --set-default MODE  设置默认启动模式 (tui|cli|help)")
    cli_help()


def _handle_set_default():
    idx = sys.argv.index("--set-default")
    mode = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "help"
    from .utils.config import CONFIG, CONFIG_FILE
    config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
    config.default_mode = mode
    config.save_config()
    print(f"默认启动模式已设为: {mode}")


def _dispatch():
    from .cli import CLI_FLAGS, run_cli
    from .tui import TUI_FLAGS, run_tui

    given = set(sys.argv[1:]) & (CLI_FLAGS | TUI_FLAGS)

    if given & CLI_FLAGS:
        run_cli()
    elif given & TUI_FLAGS:
        run_tui()
    else:
        _default_mode()


def _default_mode():
    from .utils.config import CONFIG, CONFIG_FILE
    config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
    mode = config.default_mode or "help"

    if mode == "tui":
        sys.argv.append("--tui")
        from .tui import run_tui
        run_tui()
    elif mode == "cli":
        sys.argv.append("--cli")
        from .cli import run_cli
        run_cli()
    else:
        _print_help()


def main():
    if "--help" in sys.argv:
        _print_help()
    elif "--set-default" in sys.argv:
        _handle_set_default()
    else:
        _dispatch()


if __name__ == "__main__":
    main()

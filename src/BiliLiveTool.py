"""总入口

处理 --help / --set-default（不加载 cli/tui），
其余参数按 cli/tui 各自导出的 flag 集匹配分发，
无匹配时使用 config.json 中的 default_mode。
"""

import sys


def main():
    if "--help" in sys.argv:
        print("B站直播管理工具\n")
        print("    --help          帮助信息")
        print("    --set-default MODE  设置默认启动模式 (tui|cli|help)")
        print()
        print("  CLI 模式:")
        from .cli import cli_help
        cli_help()
        return

    if "--set-default" in sys.argv:
        idx = sys.argv.index("--set-default")
        mode = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "help"
        from .utils.config import CONFIG, CONFIG_FILE
        config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
        config.default_mode = mode
        config.save_config()
        print(f"默认启动模式已设为: {mode}")
        return

    from .cli import CLI_FLAGS, run_cli
    from .tui import TUI_FLAGS, run_tui

    given = set(sys.argv[1:]) & (CLI_FLAGS | TUI_FLAGS)

    if given & CLI_FLAGS:
        run_cli()
    elif given & TUI_FLAGS:
        run_tui()
    else:
        from .utils.config import CONFIG, CONFIG_FILE
        config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
        mode = config.default_mode or "help"
        if mode == "tui":
            sys.argv.append("--tui")
            run_tui()
        elif mode == "cli":
            sys.argv.append("--cli")
            run_cli()
        else:
            print("B站直播管理工具\n")
            print("    --help          帮助信息")
            print("    --set-default MODE  设置默认启动模式 (tui|cli|help)")
            print()
            print("  CLI 模式:")
            from .cli import cli_help
            cli_help()


if __name__ == "__main__":
    main()

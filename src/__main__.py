"""入口分发

__main__.py 处理 --help / --set-default（不加载 cli/tui），
其余参数分发给 cli 或 tui 入口。
"""

import sys


def main():
    if "--help" in sys.argv:
        print("B站直播管理工具\n")
        print("  模式选择 (__main__.py 处理):")
        print("    --help          帮助信息")
        print("    --set-default MODE  设置默认启动模式 (tui|cli|help)")
        print()
        print("  CLI 模式 (默认):")
        from src.cli.main import cli_help
        cli_help()
        return

    if "--set-default" in sys.argv:
        idx = sys.argv.index("--set-default")
        mode = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "help"
        from src.utils.config import CONFIG, CONFIG_FILE
        config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
        config.default_mode = mode
        config.save_config()
        print(f"默认启动模式已设为: {mode}")
        return

    if "--tui" in sys.argv:
        from src.tui import run_tui
        run_tui()
    else:
        from src.cli.main import main as run_cli
        run_cli()


if __name__ == "__main__":
    main()

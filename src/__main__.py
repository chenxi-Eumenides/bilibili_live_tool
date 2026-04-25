"""B站直播管理工具 入口分发

用法:
  python -m src --help
  python -m src --login
  python -m src --live start
  python -m src --tui
"""

import sys


def main():
    if "--tui" in sys.argv:
        from src.tui import run_tui
        run_tui()
    else:
        from src.cli.main import main as run_cli
        run_cli()


if __name__ == "__main__":
    main()

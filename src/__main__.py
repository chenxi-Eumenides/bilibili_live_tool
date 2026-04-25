"""B站直播管理工具 入口分发

根据命令行参数选择运行模式:
  - 无参数: 启动 TUI (Textual 图形界面)
  - 有参数: 启动 CLI (命令行模式)

用法:
  python -m src              # 启动 TUI
  python -m src login        # CLI: 扫码登录
  python -m src live start   # CLI: 开播
  python -m src danmaku      # CLI: 弹幕监听
"""

import sys


def main():
    if len(sys.argv) > 1:
        from src.cli import run_cli
        run_cli()
    else:
        from src.tui import run_tui
        run_tui()


if __name__ == "__main__":
    main()

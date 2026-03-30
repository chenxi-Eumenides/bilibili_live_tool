"""TUI应用入口

命令行入口点，启动Textual应用。
"""

import logging
from pathlib import Path

from .ui.app import BiliLiveApp


def setup_logging():
    """配置日志"""
    # 配置日志只写入文件，不输出到控制台
    log_file = Path("bili_live_tool.log")

    # 启动时清理已有日志文件
    if log_file.exists():
        try:
            log_file.unlink()
        except Exception:
            pass  # 清理失败不影响启动

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.FileHandler(log_file, encoding="utf-8")],
    )


def main():
    """应用入口"""
    setup_logging()

    app = BiliLiveApp()
    app.run()


if __name__ == "__main__":
    main()

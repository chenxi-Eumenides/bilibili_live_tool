"""CLI 用户层

通过命令行参数调用 logic 层，返回结果到 stdout。
"""

from .main import main as run_cli

__all__ = ["run_cli"]

"""逻辑层入口

提供 Session 状态中心及认证、直播、弹幕编排的公共 API。
用户层（cli/tui）只 import 本层，不直接 import utils。
"""

from .session import Session

__all__ = ["Session"]

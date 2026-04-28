"""逻辑层入口

提供 Session 状态中心及认证、直播、弹幕编排的公共 API。
用户层（cli/tui）只 import 本层，不直接 import utils。
"""

from .session import Session
from .auth import (
    auth_get_qr,
    auth_poll_qr,
    auth_update_safety,
    auth_validate_login,
    auth_logout,
)
from .live import (
    live_init,
    live_start,
    live_stop,
    live_update_room,
    live_refresh_room_data,
)
from .danmaku import danmaku_start, danmaku_stop, _listen_loop
from ..utils.constant import BiliCode, SessionEvent

__all__ = [
    "Session",
    "SessionEvent",
    "BiliCode",
    "auth_get_qr",
    "auth_poll_qr",
    "auth_update_safety",
    "auth_validate_login",
    "auth_logout",
    "live_init",
    "live_start",
    "live_stop",
    "live_update_room",
    "live_refresh_room_data",
    "danmaku_start",
    "danmaku_stop",
    "_listen_loop",
]

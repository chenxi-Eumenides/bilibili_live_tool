"""逻辑层入口

提供 Session 状态中心及认证、直播、弹幕编排的公共 API。
用户层（cli/tui）只 import 本层，不直接 import utils。
"""

from .session import Session
from .auth import (
    auth_generate_qrcode,
    auth_poll_login,
    auth_validate_login,
    auth_logout,
)
from .live import (
    live_start,
    live_stop,
    live_update_room,
    live_refresh_room_info,
    live_get_room_info_cache,
    live_get_area_list,
)
from .danmaku import danmaku_start, danmaku_stop, _listen_loop
from ..utils.constant import BiliCode, SessionEvent

__all__ = [
    "Session",
    "SessionEvent",
    "BiliCode",
    "auth_generate_qrcode",
    "auth_poll_login",
    "auth_validate_login",
    "auth_logout",
    "live_start",
    "live_stop",
    "live_update_room",
    "live_refresh_room_info",
    "live_get_room_info",
    "live_get_area_list",
    "danmaku_start",
    "danmaku_stop",
    "_listen_loop",
]

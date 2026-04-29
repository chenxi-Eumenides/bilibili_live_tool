"""常量定义"""

from dataclasses import dataclass
from pathlib import Path
from struct import Struct

# 版本信息
VERSION = (0, 5, 0)
VERSION_STR = ".".join(map(str, VERSION))

# 文件、路径
BASE_DIR = Path.cwd()
CONFIG_FILE = Path("config.json")
# 所需常量
TITLE_MAX_CHAR: int = 40
# WEBSOCKET_HEADER_STRUCT = Struct(">I I I I I I")
WEBSOCKET_HEADER_STRUCT = Struct(">I2H2I")
BILI_TICKET_KEY = "XgwSnGZ1p"


# B站API
# @dataclass
class ApiData:
    """B站API所需默认数据"""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
    HEADERS: dict[str, str] = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://link.bilibili.com",
        "referer": "https://link.bilibili.com/p/center/index",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Not=A?Brand";v="8", "Chromium";v="137"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": USER_AGENT,
    }
    APP_KEY: str = "aae92bc66f3edfab"
    APP_SECRET: str = "af125a0d5279fd576c1b4418a3e8276d"
    LIVEHIME_BUILD: str = "10082"
    LIVEHIME_VERSION: str = "7.40.0.10082"
    TICKET_KEY_ID: str = "ec02"
    TICKET_KEY: str = "XgwSnGZ1p"
    PLATFORM: str = "pc_link"


@dataclass
class ApiUrl:
    """B站API路径"""

    START_LIVE: str = "https://api.live.bilibili.com/room/v1/Room/startLive"
    STOP_LIVE: str = "https://api.live.bilibili.com/room/v1/Room/stopLive"
    GENERATE_QR: str = (
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    )
    GET_QR_RES: str = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    FACE_AUTH: str = "https://api.live.bilibili.com/xlive/app-blink/v1/preLive/IsUserIdentifiedByFaceAuth"
    GET_ROOM_ID: str = "https://api.live.bilibili.com/room/v2/Room/room_id_by_uid"
    GET_USER_STATUS: str = "https://api.bilibili.com/x/web-interface/nav/stat"
    GET_AREA_LIST: str = "https://api.live.bilibili.com/room/v1/Area/getList"
    GET_ROOM_DATA: str = "https://api.live.bilibili.com/room/v1/Room/get_info"
    UPDATE_ROOM: str = "https://api.live.bilibili.com/room/v1/Room/update"
    GET_LIVE_VERSION: str = "https://api.live.bilibili.com/xlive/app-blink/v1/liveVersionInfo/getHomePageLiveVersion"
    GET_WBI_KEY: str = "https://api.bilibili.com/x/web-interface/nav"
    GET_DANMAKU_INFO: str = (
        "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo"
    )
    SEND_DANMAKU: str = "https://api.live.bilibili.com/msg/send"
    GET_BILI_TICKET: str = (
        "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
    )
    SET_LIVE_TIMESHIFT: str = "https://api.live.bilibili.com/xlive/app-blink/v1/upStreamConfig/SetAnchorSelfStreamTimeShift"


class SessionEvent:
    """Session 事件名称常量

    逻辑层通过 session._emit(SessionEvent.XXX) 触发，
    用户层通过 session.on(SessionEvent.XXX, callback) 订阅。
    """

    AUTH_QR_READY = "auth:qr_ready"
    AUTH_QR_FAIL = "auth:qr_fail"
    AUTH_QR_WAITING = "auth:qr_waiting"
    AUTH_QR_SCANNED = "auth:qr_scanned"
    AUTH_LOGIN_SUCCESS = "auth:login_success"
    AUTH_LOGIN_FAILED = "auth:login_failed"
    AUTH_LOGOUT = "auth:logout"
    AUTH_UPDATE_SAFETY = "auth:update_safety"

    LIVE_STATE_CHANGED = "live:state_changed"
    LIVE_INFO_UPDATED = "live:info_updated"
    LIVE_INFO_UPDATED_FAIL = "live:info_updated_fail"
    LIVE_AREA_UPDATED = "live:area_updated"
    LIVE_AREA_UPDATED_FAIL = "live:area_updated_fail"
    LIVE_FACE_AUTH_REQUIRED = "live:face_auth_required"
    LIVE_START_FAIL = "live:start_fail"
    LIVE_STOP_FAIL = "live:stop_fail"

    DANMAKU_RECEIVED = "danmaku:received"
    DANMAKU_STOPPED = "danmaku:stopped"

    ERROR = "error"
    EXCEPTION = "exception"


class BiliCode:
    """B站 API 常用状态码常量

    码值为 abs 后的正整数，与 error.FAIL_BILI_CODE 的 key 一一对应。
    """

    LOGIN_QR_WAITING = 86101
    LOGIN_QR_SCANNED = 86090
    LOGIN_QR_EXPIRED = 86038
    LOGIN_QR_INVALID = 86039

    FACE_AUTH_REQUIRED = 60024
    FACE_AUTH_VERIFY = 60043


class Tuning:
    """运行时调优参数（延迟 / 超时 / 间隔）"""

    API_TIMEOUT = 10
    POLL_INTERVAL = 2
    LOGIN_POLL_TIMEOUT = 180
    DANMAKU_HEARTBEAT = 30
    COOLDOWN_MIN = 0.3
    COOLDOWN_MAX = 1.0


class DanmakuColors:
    """弹幕颜色配置 - 所有颜色统一管理"""

    DEFAULT: str = "#FFFFFF"  # 默认颜色 - 白色

    # ===== 常规类型颜色 =====
    CONTENT: str = "#FFFFFF"  # 弹幕内容 - 白色
    TIMESTAMP: str = "#999999"  # 时间戳 - 灰色

    # ===== 通知类颜色（全部内容都显示此颜色，不含时间戳） =====
    NOTICE_IMPORTANT: str = "#CC0000"  # 重要通知 - 深红色
    NOTICE_SYSTEM: str = "#FF6B6B"  # 系统通知 - 浅红色
    NOTICE_NORMAL: str = "#979797"  # 普通通知 - 浅灰色（欢迎信息等）

    # ===== 用户类颜色（仅类型和用户名显示此颜色） =====
    USER_NORMAL: str = "#FFFFFF"  # 普通用户 - 白色
    USER_FAN: str = "#FFB6C1"  # 粉丝用户 - 浅粉色
    USER_JIANZHANG: str = "#66CCFF"  # 舰长用户 - 浅蓝色
    USER_TIDU: str = "#0066CC"  # 提督用户 - 深蓝色
    USER_ZONGDU: str = "#FFD700"  # 总督用户 - 金色
    USER_ADMIN: str = "#00CC00"  # 房管用户 - 绿色

    # ===== 礼物类颜色（全部内容都显示此颜色，不含时间戳） =====
    GIFT_JIANZHANG: str = "#66CCFF"  # 舰长礼物 - 浅蓝色
    GIFT_IMPORTANT: str = "#CC0000"  # 重要礼物 - 深红色
    GIFT_DENGPAI: str = "#FFB6C1"  # 灯牌礼物 - 浅粉色
    GIFT_NORMAL: str = "#AAAAAA"  # 普通礼物 - 浅灰色


QR_DISPLAY_CHARS = {
    (False, False): " ",
    (True, False): "▀",
    (False, True): "▄",
    (True, True): "█",
}


class KeyBindings:
    """全局快捷键绑定"""

    QUIT = "q,escape"  # 退出
    # 以下不支持
    TOGGLE_LIVE = "space"  # 开播/下播切换
    EDIT_TITLE = "t"  # 修改标题
    EDIT_AREA = "a"  # 修改分区
    REFRESH = "r"  # 刷新状态
    NEXT_FOCUS = "tab"  # 切换焦点
    COPY_STREAM = "c"  # 复制推流码
    COPY_ALL = "shift+c"  # 复制全部信息
    TOGGLE_LOG = "l"  # 展开/折叠日志


# 解码加密数据
WBI_KEY_INDEX_TABLE = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
]
MIXIN_KEY_ENC_TABLE: list[int] = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]

"""TUI常量定义

使用标准库的enum和pathlib。
"""

from enum import Enum, auto
from pathlib import Path

# ===== 版本信息 =====
VERSION = (0, 4, 2)
VERSION_STR = ".".join(map(str, VERSION))

# ===== 基础路径 =====
BASE_DIR = Path.cwd()

# ===== 文件路径 =====
# 使用工作目录下的配置文件
CONFIG_FILE = Path("config.json")
README_FILE = Path("使用说明.txt")
QR_IMG = Path("qr.jpg")
QR_FACE_IMG = Path("qr_face.jpg")

# ===== B站API常量 =====
APP_KEY: str = "aae92bc66f3edfab"
APP_SECRET: str = "af125a0d5279fd576c1b4418a3e8276d"
LIVEHIME_BUILD: str = "10082"
LIVEHIME_VERSION: str = "7.40.0.10082"

# ===== 导出所有常量 =====
__all__ = [
    "VERSION",
    "VERSION_STR",
    "BASE_DIR",
    "CONFIG_FILE",
    "README_FILE",
    "QR_IMG",
    "QR_FACE_IMG",
    "APP_KEY",
    "APP_SECRET",
    "LIVEHIME_BUILD",
    "LIVEHIME_VERSION",
    "TITLE_MAX_CHAR",
    "AREA_OUTPUT_LINE_NUM",
    "ApiEndpoints",
    # 枚举
    "AppState",
    "LiveStatus",
    "KeyBindings",
    "Messages",
    "Styles",
]


# ===== 配置限制 =====
TITLE_MAX_CHAR: int = 40
AREA_OUTPUT_LINE_NUM: int = 4

# ===== 配置文件版本 =====
CONFIG_DEFAULT_VERSION: int = 2  # 默认保存的配置版本

# ===== API端点 =====
class ApiEndpoints:
    """B站API端点"""

    GET_ROOM_ID: str = "https://api.live.bilibili.com/room/v2/Room/room_id_by_uid"
    GET_QR_RES: str = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    GENERATE_QR: str = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    GET_AREA_LIST: str = "https://api.live.bilibili.com/room/v1/Area/getList"
    GET_ROOM_STATUS: str = "https://api.live.bilibili.com/room/v1/Room/get_info"
    UPDATE_ROOM: str = "https://api.live.bilibili.com/room/v1/Room/update"
    GET_USER_STATUS: str = "https://api.bilibili.com/x/web-interface/nav/stat"
    CHECK_FACE: str = "https://api.live.bilibili.com/xlive/app-blink/v1/preLive/IsUserIdentifiedByFaceAuth"
    START_LIVE: str = "https://api.live.bilibili.com/room/v1/Room/startLive"
    STOP_LIVE: str = "https://api.live.bilibili.com/room/v1/Room/stopLive"
    GET_LIVE_VERSION: str = "https://api.live.bilibili.com/xlive/app-blink/v1/liveVersionInfo/getHomePageLiveVersion"
    SET_LIVE_TIMESHIFT: str = "https://api.live.bilibili.com/xlive/app-blink/v1/upStreamConfig/SetAnchorSelfStreamTimeShift"

# ===== 应用状态枚举 =====
class AppState(Enum):
    """应用全局状态 - 3种"""

    UNAUTH = auto()  # 未登录
    IDLE = auto()  # 已登录，未开播
    LIVE = auto()  # 直播中


# ===== 直播状态枚举 =====
class LiveStatus(Enum):
    """直播间状态"""

    OFFLINE = 0  # 未开播
    LIVE = 1  # 直播中
    REPLAY = 2  # 轮播中


# ===== 快捷键定义 =====
class KeyBindings:
    """全局快捷键绑定"""

    TOGGLE_LIVE = "space"  # 开播/下播切换
    EDIT_TITLE = "t"  # 修改标题
    EDIT_AREA = "a"  # 修改分区
    REFRESH = "r"  # 刷新状态
    QUIT = "q,escape"  # 退出
    NEXT_FOCUS = "tab"  # 切换焦点
    COPY_STREAM = "c"  # 复制推流码
    COPY_ALL = "shift+c"  # 复制全部信息
    TOGGLE_LOG = "l"  # 展开/折叠日志


# ===== 消息常量 =====
class Messages:
    """提示消息"""

    LOGIN_SUCCESS = "[OK] 登录成功"
    LOGIN_FAILED = "[ERR] 登录失败: {error}"
    LIVE_STARTED = "[OK] 开播成功"
    LIVE_STOPPED = "[OK] 下播成功"
    TITLE_UPDATED = "[OK] 标题已更新"
    AREA_UPDATED = "[OK] 分区已更新"
    STREAM_COPIED = "[OK] 推流码已复制"
    STREAM_ERROR = "[ERR] 获取推流码失败: {error}"
    CONFIG_SAVED = "[OK] 配置已保存"
    CONFIG_LOADED = "[OK] 配置已加载"
    NETWORK_ERROR = "[ERR] 网络错误: {error}"
    UNKNOWN_ERROR = "[ERR] 未知错误: {error}"
    NOT_LOGGED_IN = "未登录，请先登录"
    MISSING_INFO = "请填写完整信息"


# ===== 样式常量 =====
class Styles:
    """UI样式常量 - 深色主题"""

    ACCENT_COLOR = "#06b6d4"      # 青色强调色
    SUCCESS_COLOR = "#22c55e"     # 成功绿
    WARNING_COLOR = "#f59e0b"     # 警告黄
    ERROR_COLOR = "#ef4444"       # 错误红
    TEXT_PRIMARY = "#ffffff"      # 主文字 - 纯白
    TEXT_SECONDARY = "#a1a1aa"    # 次文字 - 淡灰
    TEXT_MUTED = "#71717a"        # 辅助文字 - 中灰
    BG_PRIMARY = "#09090b"        # 最深背景 - 近黑
    BG_SECONDARY = "#18181b"      # 二级背景 - 深灰
    BG_TERTIARY = "#27272a"       # 三级背景 - 中深灰
    BORDER_COLOR = "#3f3f46"      # 边框颜色

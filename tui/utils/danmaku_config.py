"""弹幕配置模块

统一管理弹幕类型、颜色等配置。
"""

from enum import Enum, auto
from dataclasses import dataclass


class DanmakuCategory(Enum):
    """弹幕分类"""
    REGULAR = auto()    # 常规
    NOTICE = auto()     # 通知类
    USER = auto()       # 用户类


class DanmakuType(Enum):
    """弹幕类型"""
    # 常规类型
    CONTENT = auto()     # 弹幕内容
    TIMESTAMP = auto()   # 时间戳
    
    # 通知类
    NOTICE_IMPORTANT = auto()  # 重要通知
    NOTICE_SYSTEM = auto()     # 系统通知
    NOTICE_NORMAL = auto()     # 普通通知（欢迎信息等）
    
    # 用户类
    USER_NORMAL = auto()   # 普通用户
    USER_FAN = auto()      # 粉丝用户
    USER_JIANZHANG = auto()  # 舰长用户
    USER_TIDU = auto()     # 提督用户
    USER_ZONGDU = auto()   # 总督用户
    USER_ADMIN = auto()    # 房管用户


@dataclass(frozen=True)
class DanmakuColors:
    """弹幕颜色配置 - 所有颜色统一管理"""
    
    # ===== 常规类型颜色 =====
    CONTENT: str = "#FFFFFF"           # 弹幕内容 - 白色
    TIMESTAMP: str = "#999999"         # 时间戳 - 灰色
    
    # ===== 通知类颜色（全部内容都显示此颜色，不含时间戳） =====
    NOTICE_IMPORTANT: str = "#CC0000"  # 重要通知 - 深红色
    NOTICE_SYSTEM: str = "#FF6B6B"     # 系统通知 - 浅红色
    NOTICE_NORMAL: str = "#AAAAAA"     # 普通通知 - 浅灰色（欢迎信息等）
    
    # ===== 用户类颜色（仅类型和用户名显示此颜色） =====
    USER_NORMAL: str = "#E5E5E5"       # 普通用户 - 浅灰白
    USER_FAN: str = "#FFB6C1"          # 粉丝用户 - 浅粉色
    USER_JIANZHANG: str = "#66CCFF"    # 舰长用户 - 浅蓝色
    USER_TIDU: str = "#0066CC"         # 提督用户 - 深蓝色
    USER_ZONGDU: str = "#FFD700"       # 总督用户 - 金色
    USER_ADMIN: str = "#00CC00"        # 房管用户 - 绿色


# 全局颜色配置实例
DANMAKU_COLORS = DanmakuColors()


# 弹幕类型到分类的映射
TYPE_CATEGORY_MAP: dict[DanmakuType, DanmakuCategory] = {
    # 常规
    DanmakuType.CONTENT: DanmakuCategory.REGULAR,
    DanmakuType.TIMESTAMP: DanmakuCategory.REGULAR,
    
    # 通知类
    DanmakuType.NOTICE_IMPORTANT: DanmakuCategory.NOTICE,
    DanmakuType.NOTICE_SYSTEM: DanmakuCategory.NOTICE,
    DanmakuType.NOTICE_NORMAL: DanmakuCategory.NOTICE,
    
    # 用户类
    DanmakuType.USER_NORMAL: DanmakuCategory.USER,
    DanmakuType.USER_FAN: DanmakuCategory.USER,
    DanmakuType.USER_JIANZHANG: DanmakuCategory.USER,
    DanmakuType.USER_TIDU: DanmakuCategory.USER,
    DanmakuType.USER_ZONGDU: DanmakuCategory.USER,
    DanmakuType.USER_ADMIN: DanmakuCategory.USER,
}


# 弹幕类型到颜色的映射
TYPE_COLOR_MAP: dict[DanmakuType, str] = {
    # 常规
    DanmakuType.CONTENT: DANMAKU_COLORS.CONTENT,
    DanmakuType.TIMESTAMP: DANMAKU_COLORS.TIMESTAMP,
    
    # 通知类
    DanmakuType.NOTICE_IMPORTANT: DANMAKU_COLORS.NOTICE_IMPORTANT,
    DanmakuType.NOTICE_SYSTEM: DANMAKU_COLORS.NOTICE_SYSTEM,
    DanmakuType.NOTICE_NORMAL: DANMAKU_COLORS.NOTICE_NORMAL,
    
    # 用户类
    DanmakuType.USER_NORMAL: DANMAKU_COLORS.USER_NORMAL,
    DanmakuType.USER_FAN: DANMAKU_COLORS.USER_FAN,
    DanmakuType.USER_JIANZHANG: DANMAKU_COLORS.USER_JIANZHANG,
    DanmakuType.USER_TIDU: DANMAKU_COLORS.USER_TIDU,
    DanmakuType.USER_ZONGDU: DANMAKU_COLORS.USER_ZONGDU,
    DanmakuType.USER_ADMIN: DANMAKU_COLORS.USER_ADMIN,
}


# 头衔文本到弹幕类型的映射
BADGE_TYPE_MAP: dict[str, DanmakuType] = {
    "": DanmakuType.USER_NORMAL,
    "粉丝": DanmakuType.USER_FAN,
    "舰长": DanmakuType.USER_JIANZHANG,
    "提督": DanmakuType.USER_TIDU,
    "总督": DanmakuType.USER_ZONGDU,
}


# 通知类型映射
NOTICE_TYPE_MAP: dict[str, DanmakuType] = {
    "important": DanmakuType.NOTICE_IMPORTANT,
    "system": DanmakuType.NOTICE_SYSTEM,
    "normal": DanmakuType.NOTICE_NORMAL,
}



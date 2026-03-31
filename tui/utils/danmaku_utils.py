"""弹幕工具函数模块

提供弹幕相关的工具函数，如颜色获取、分类判断等。
"""

from .danmaku_config import (
    DanmakuType,
    DanmakuCategory,
    DANMAKU_COLORS,
    TYPE_COLOR_MAP,
    TYPE_CATEGORY_MAP,
    BADGE_TYPE_MAP,
    NOTICE_TYPE_MAP,
)


__all__ = (
    'get_danmaku_color',
    'get_danmaku_category',
    'get_badge_type',
    'get_notice_type',
    'format_timestamp',
)


def get_danmaku_color(danmaku_type: DanmakuType) -> str:
    """获取弹幕类型对应的颜色
    
    Args:
        danmaku_type: 弹幕类型
        
    Returns:
        str: 颜色值（十六进制）
    """
    return TYPE_COLOR_MAP.get(danmaku_type, DANMAKU_COLORS.CONTENT)


def get_danmaku_category(danmaku_type: DanmakuType) -> DanmakuCategory:
    """获取弹幕类型的分类
    
    Args:
        danmaku_type: 弹幕类型
        
    Returns:
        DanmakuCategory: 弹幕分类
    """
    return TYPE_CATEGORY_MAP.get(danmaku_type, DanmakuCategory.REGULAR)


def get_badge_type(badge_text: str) -> DanmakuType:
    """根据头衔文本获取弹幕类型
    
    Args:
        badge_text: 头衔文本
        
    Returns:
        DanmakuType: 弹幕类型
    """
    return BADGE_TYPE_MAP.get(badge_text, DanmakuType.USER_NORMAL)


def get_notice_type(notice_level: str) -> DanmakuType:
    """根据通知级别获取弹幕类型
    
    Args:
        notice_level: 通知级别 ("important", "system", "normal")
        
    Returns:
        DanmakuType: 弹幕类型
    """
    return NOTICE_TYPE_MAP.get(notice_level, DanmakuType.NOTICE_NORMAL)


def format_timestamp(hour: int, minute: int, second: int) -> str:
    """格式化时间戳
    
    Args:
        hour: 小时
        minute: 分钟
        second: 秒
        
    Returns:
        str: HH:MM:SS 格式的时间字符串
    """
    return f"{hour:02d}:{minute:02d}:{second:02d}"
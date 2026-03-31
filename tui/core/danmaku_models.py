"""弹幕数据模型

参考blivedm.models.web的实现，定义弹幕相关的数据模型。
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ..utils.danmaku_config import DanmakuType

__all__ = (
    'DanmakuMessage',
    'HeartbeatMessage',
    'GiftMessage',
)


@dataclass
class DanmakuMessage:
    """弹幕消息
    
    解析B站弹幕协议中的DANMU_MSG命令。
    """
    
    # 弹幕基础信息 (info[0])
    mode: int = 0
    """弹幕显示模式（滚动、顶部、底部）"""
    font_size: int = 0
    """字体尺寸"""
    color: int = 0
    """颜色"""
    timestamp: int = 0
    """时间戳（毫秒）"""
    rnd: int = 0
    """随机数/弹幕ID"""
    
    # 弹幕内容 (info[1])
    msg: str = ''
    """弹幕内容"""
    
    # 用户信息 (info[2])
    uid: int = 0
    """用户ID"""
    uname: str = ''
    """用户名"""
    face: str = ''
    """用户头像URL"""
    admin: int = 0
    """是否房管"""
    vip: int = 0
    """是否月费老爷"""
    svip: int = 0
    """是否年费老爷"""
    
    # 勋章信息 (info[3])
    medal_level: int = 0
    """勋章等级"""
    medal_name: str = ''
    """勋章名"""
    medal_room_id: int = 0
    """勋章房间ID"""
    
    # 用户等级 (info[4])
    user_level: int = 0
    """用户等级"""
    
    # 头衔 (info[5])
    title: str = ''
    """头衔"""
    
    # 舰队类型 (info[7])
    privilege_type: int = 0
    """舰队类型，0非舰队，1总督，2提督，3舰长"""
    
    is_mirror: bool = False
    """是否跨房弹幕"""
    
    @classmethod
    def from_command(cls, info: list, is_mirror: bool = False) -> 'DanmakuMessage':
        """从B站弹幕协议解析
        
        Args:
            info: B站弹幕消息的info字段
            is_mirror: 是否为跨房弹幕
            
        Returns:
            DanmakuMessage实例
        """
        # 基础信息
        mode_info = info[0]
        mode = mode_info[1] if len(mode_info) > 1 else 0
        font_size = mode_info[2] if len(mode_info) > 2 else 0
        color = mode_info[3] if len(mode_info) > 3 else 0
        timestamp = mode_info[4] if len(mode_info) > 4 else 0
        rnd = mode_info[5] if len(mode_info) > 5 else 0
        
        # 尝试获取头像
        face = ''
        try:
            if len(mode_info) > 15 and mode_info[15]:
                face = mode_info[15]['user']['base']['face']
        except (TypeError, KeyError, IndexError):
            pass
        
        # 弹幕内容
        msg = info[1] if len(info) > 1 else ''
        
        # 用户信息
        user_info = info[2] if len(info) > 2 else []
        uid = user_info[0] if len(user_info) > 0 else 0
        uname = user_info[1] if len(user_info) > 1 else ''
        admin = user_info[2] if len(user_info) > 2 else 0
        vip = user_info[3] if len(user_info) > 3 else 0
        svip = user_info[4] if len(user_info) > 4 else 0
        
        # 勋章信息
        medal_level = 0
        medal_name = ''
        medal_room_id = 0
        if len(info) > 3 and len(info[3]) > 0:
            medal_info = info[3]
            medal_level = medal_info[0] if len(medal_info) > 0 else 0
            medal_name = medal_info[1] if len(medal_info) > 1 else ''
            medal_room_id = medal_info[3] if len(medal_info) > 3 else 0
        
        # 用户等级
        user_level = 0
        if len(info) > 4 and len(info[4]) > 0:
            user_level = info[4][0]
        
        # 头衔
        title = ''
        if len(info) > 5 and len(info[5]) > 1:
            title = info[5][1]
        
        # 舰队类型
        privilege_type = info[7] if len(info) > 7 else 0
        
        return cls(
            mode=mode,
            font_size=font_size,
            color=color,
            timestamp=timestamp,
            rnd=rnd,
            msg=msg,
            uid=uid,
            uname=uname,
            face=face,
            admin=admin,
            vip=vip,
            svip=svip,
            medal_level=medal_level,
            medal_name=medal_name,
            medal_room_id=medal_room_id,
            user_level=user_level,
            title=title,
            privilege_type=privilege_type,
            is_mirror=is_mirror,
        )
    
    @property
    def badge_text(self) -> str:
        """获取用户徽章文本"""
        if self.admin:
            return "房管"
        if self.privilege_type == 1:
            return "总督"
        if self.privilege_type == 2:
            return "提督"
        if self.privilege_type == 3:
            return "舰长"
        if self.medal_name:
            return self.medal_name
        return ""
    
    @property
    def danmaku_type(self) -> DanmakuType:
        """获取对应的DanmakuType"""
        if self.admin:
            return DanmakuType.USER_NORMAL
        if self.privilege_type == 1:
            return DanmakuType.USER_ZONGDU
        if self.privilege_type == 2:
            return DanmakuType.USER_TIDU
        if self.privilege_type == 3:
            return DanmakuType.USER_JIANZHANG
        if self.medal_name:
            return DanmakuType.USER_FAN
        return DanmakuType.USER_NORMAL
    
    def to_timestamp_str(self) -> str:
        """将时间戳转换为字符串"""
        dt = datetime.fromtimestamp(self.timestamp / 1000)
        return dt.strftime("%H:%M:%S")


@dataclass
class HeartbeatMessage:
    """心跳消息"""
    
    popularity: int = 0
    """人气值"""
    
    @classmethod
    def from_command(cls, data: dict) -> 'HeartbeatMessage':
        """从命令数据解析"""
        return cls(
            popularity=data.get('popularity', 0),
        )


@dataclass
class GiftMessage:
    """礼物消息"""
    
    gift_name: str = ''
    """礼物名称"""
    gift_id: int = 0
    """礼物ID"""
    num: int = 0
    """礼物数量"""
    uname: str = ''
    """用户名"""
    uid: int = 0
    """用户ID"""
    face: str = ''
    """用户头像"""
    
    @classmethod
    def from_command(cls, data: dict) -> 'GiftMessage':
        """从命令数据解析"""
        return cls(
            gift_name=data.get('giftName', ''),
            gift_id=data.get('giftId', 0),
            num=data.get('num', 0),
            uname=data.get('uname', ''),
            uid=data.get('uid', 0),
            face=data.get('face', ''),
        )

"""数据结构定义"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum, auto
from pprint import pformat
from types import SimpleNamespace
from typing import Any, Optional

from requests import Response

from .constant import DanmakuColors


class AppState(Enum):
    """全局用户状态"""

    UNAUTH = auto()
    IDLE = auto()
    LIVE = auto()
    REPLAY = auto()


class ApiType(Enum):
    POST = auto()
    GET = auto()


@dataclass(frozen=True)
class ApiResult:
    """
    VALUE:
        MSG: 请求提示信息
        DATA: 请求返回数据
        COOKIE: 请求cookies
        RAW_RESPONSE: 原始响应
    """

    msg: Optional[str] = None
    data: Optional[dict] = None
    cookies: Optional[dict] = None
    raw_response: Optional[Response] = None

    def __repr__(self):
        lines = [
            f"MSG : {self.msg}",
            f"DATA : {pformat(self.data, indent=2)}",
            f"COOKIES : {self.cookies}",
        ]
        return "\n".join(lines)

    @classmethod
    def from_response(cls, response: Response):
        cookies: dict[str, str] = response.cookies.get_dict()
        json = response.json()
        msg = json.get("msg") or json.get("message")

        return cls(
            msg=msg,
            data=json.get("data"),
            cookies=cookies,
            raw_response=response,
        )


class FuncType(Enum):
    SUCCESS = auto()
    FAIL = auto()
    ERROR = auto()


@dataclass(frozen=True)
class FuncResult:
    """
    VALUE:
        TYPE: 状态
        RESULT: 结果
    """

    type: FuncType = FuncType.FAIL
    result: Any = None


class LiveSubArea(SimpleNamespace):
    name: str
    id: int


class LiveArea(SimpleNamespace):
    name: str
    id: int
    list: list[LiveSubArea]


@dataclass
class LiveAreaList:
    """直播分区列表对象"""

    _data: list[LiveArea]

    def __getitem__(self, index) -> LiveArea:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    @classmethod
    def from_api_data(cls, data):

        results: list[LiveArea] = []
        for root in data:
            part_results: list[LiveSubArea] = []
            for part in root.get("list"):
                part_result: LiveSubArea = LiveSubArea(
                    name=part.get("name"),
                    id=int(part.get("id")),
                )
                part_results.append(part_result)
            result: LiveArea = LiveArea(
                name=root.get("name"),
                id=int(root.get("id")),
                list=part_results,
            )
            results.append(result)
        return cls(_data=results)


class WebSocketOperation(IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_MSG = 4
    SEND_MSG_REPLY = 5
    DISCONNECT_REPLY = 6
    AUTH = 7
    AUTH_REPLY = 8
    RAW = 9


class WebSocketProtoVer(IntEnum):
    NORMAL = 0
    DEFLATE = 1
    BROTLI = 3


class MessageType(Enum):
    DANMAKU = auto()
    GIFT = auto()
    NOTICE = auto()
    OTHER = auto()


class UserDanmakuType(Enum):
    # 用户弹幕
    NORMAL = auto()  # 普通用户
    FAN = auto()  # 粉丝用户
    JIANZHANG = auto()  # 舰长用户
    TIDU = auto()  # 提督用户
    ZONGDU = auto()  # 总督用户
    ADMIN = auto()  # 房管用户


class GiftDanmakuType(Enum):
    # 礼物弹幕
    NORMAL = auto()  # 普通礼物
    DENGPAI = auto()  # 灯牌礼物
    IMPORTANT = auto()  # 重要礼物
    JIANZHANG = auto()  # 舰长礼物


class NoticeDanmakuType(Enum):
    # 通知弹幕
    NORMAL = auto()  # 普通通知
    IMPORTANT = auto()  # 重要通知
    SYSTEM = auto()  # 系统通知


@dataclass
class WebSocketMessage:
    message_type: MessageType
    """消息类型"""
    timestamp: int = 0
    """时间戳（毫秒）"""

    @property
    def datetime(self) -> datetime:
        """获取时间戳字符串"""
        if self.timestamp == 0:
            raise NotImplementedError
        return datetime.fromtimestamp(self.timestamp / 1000)

    @property
    def timestamp_str(self) -> str:
        """获取时间戳字符串"""
        return self.datetime.strftime("%H:%M:%S")

    def __repr__(self) -> str:
        raise NotImplementedError

    @property
    def type(self):
        raise NotImplementedError


@dataclass
class DanmakuMessage(WebSocketMessage):
    """弹幕消息

    解析B站弹幕协议中的DANMU_MSG命令。
    """

    # 弹幕基础信息 (info[0])
    mode: int = 0
    """弹幕显示模式（滚动、顶部、底部）"""
    font_size: int = 0
    """字体尺寸"""
    font_color: int = 0
    """颜色"""
    rnd: int = 0
    """随机数/弹幕ID"""

    # 弹幕内容 (info[1])
    msg: str = ""
    """弹幕内容"""

    # 用户信息 (info[2])
    uid: int = 0
    """用户ID"""
    uname: str = ""
    """用户名"""
    face: str = ""
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
    medal_name: str = ""
    """勋章名"""
    medal_room_id: int = 0
    """勋章房间ID"""

    # 用户等级 (info[4])
    user_level: int = 0
    """用户等级"""

    # 头衔 (info[5])
    title: str = ""
    """头衔"""

    # 舰队类型 (info[7])
    privilege_type: int = 0
    """舰队类型，0非舰队，1总督，2提督，3舰长"""

    is_mirror: bool = False
    """是否跨房弹幕"""

    live_room_id: int = -1
    """直播间ID"""

    @classmethod
    def from_info(cls, info: list, is_mirror: bool = False) -> "DanmakuMessage":
        """从B站弹幕协议解析

        Args:
            info: B站弹幕消息的info字段
            is_mirror: 是否为跨房弹幕
        Return:
            DanmakuMessage实例
        """
        # 基础信息
        mode_info = info[0]
        mode = mode_info[1] if len(mode_info) > 1 else 0
        font_size = mode_info[2] if len(mode_info) > 2 else 0
        font_color = mode_info[3] if len(mode_info) > 3 else 0
        timestamp = mode_info[4] if len(mode_info) > 4 else 0
        rnd = mode_info[5] if len(mode_info) > 5 else 0

        # 尝试获取头像
        face = ""
        try:
            if len(mode_info) > 15 and mode_info[15]:
                face = mode_info[15]["user"]["base"]["face"]
        except (TypeError, KeyError, IndexError):
            pass

        # 弹幕内容
        msg = info[1] if len(info) > 1 else ""

        # 用户信息
        user_info = info[2] if len(info) > 2 else []
        uid = user_info[0] if len(user_info) > 0 else 0
        uname = user_info[1] if len(user_info) > 1 else ""
        admin = user_info[2] if len(user_info) > 2 else 0
        vip = user_info[3] if len(user_info) > 3 else 0
        svip = user_info[4] if len(user_info) > 4 else 0

        # 勋章信息
        medal_level = 0
        medal_name = ""
        medal_room_id = 0
        if len(info) > 3 and len(info[3]) > 0:
            medal_info = info[3]
            medal_level = medal_info[0] if len(medal_info) > 0 else 0
            medal_name = medal_info[1] if len(medal_info) > 1 else ""
            medal_room_id = medal_info[3] if len(medal_info) > 3 else 0

        # 用户等级
        user_level = 0
        if len(info) > 4 and len(info[4]) > 0:
            user_level = info[4][0]

        # 头衔
        title = ""
        if len(info) > 5 and len(info[5]) > 1:
            title = info[5][1]

        # 舰队类型
        privilege_type = info[7] if len(info) > 7 else 0

        return cls(
            message_type=MessageType.DANMAKU,
            mode=mode,
            font_size=font_size,
            font_color=font_color,
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

    def __repr__(self) -> str:
        return "\n".join(
            [
                f"用户:{self.uname} {self.uid} lv{self.user_level}",
                f"勋章:{self.medal_name} lv{self.medal_level} room{self.medal_room_id}",
                f"身份:{self.privilege_type} {self.admin}",
                f"vip:{self.vip} svip:{self.svip} 头衔:{self.title}",
                f"内容:{self.msg}",
                f"样式:mode:{self.mode} size:{self.font_size} color:{self.font_color} rnd:{self.rnd}",
            ]
        )

    @property
    def type(self) -> UserDanmakuType:
        """获取对应的DanmakuType

        如果live_room_id未设置，则不会返回粉丝类型
        """

        if self.admin:
            return UserDanmakuType.ADMIN
        if self.privilege_type == 1:
            return UserDanmakuType.ZONGDU
        if self.privilege_type == 2:
            return UserDanmakuType.TIDU
        if self.privilege_type == 3:
            return UserDanmakuType.JIANZHANG
        if self.medal_room_id == self.live_room_id:
            return UserDanmakuType.FAN
        return UserDanmakuType.NORMAL

    @property
    def color(self) -> str:
        """获取对应的颜色"""
        return {
            UserDanmakuType.NORMAL: DanmakuColors.USER_NORMAL,
            UserDanmakuType.FAN: DanmakuColors.USER_FAN,
            UserDanmakuType.JIANZHANG: DanmakuColors.USER_JIANZHANG,
            UserDanmakuType.TIDU: DanmakuColors.USER_TIDU,
            UserDanmakuType.ZONGDU: DanmakuColors.USER_ZONGDU,
            UserDanmakuType.ADMIN: DanmakuColors.USER_ADMIN,
        }.get(self.type, DanmakuColors.DEFAULT)

    @property
    def badge_text(self) -> str:
        """获取前缀文本"""
        if text := {
            UserDanmakuType.ADMIN: "房管",
            UserDanmakuType.ZONGDU: "总督",
            UserDanmakuType.TIDU: "提督",
            UserDanmakuType.JIANZHANG: "舰长",
            UserDanmakuType.FAN: self.medal_name,
        }.get(self.type):
            return f"{text}{self.medal_level}"
        else:
            return ""

    def format_rich(self) -> str:
        """格式化为富文本显示"""
        parts = []

        # 时间戳
        parts.append(
            f"[{DanmakuColors.TIMESTAMP}]{self.timestamp_str}[/{DanmakuColors.TIMESTAMP}]"
        )
        # 弹幕前缀
        if self.type != UserDanmakuType.NORMAL:
            parts.append(f"[{self.color}][{self.badge_text}][/{self.color}]")
        # 用户名
        parts.append(f"[{self.color}]{self.uname}:[/{self.color}]")
        # 弹幕内容
        parts.append(f"[{DanmakuColors.CONTENT}]{self.msg}[/{DanmakuColors.CONTENT}]")
        return " ".join(parts)


@dataclass
class GiftMessage(WebSocketMessage):
    def __repr__(self) -> str:
        raise NotImplementedError

    @property
    def type(self) -> GiftDanmakuType:
        """获取对应的GiftDanmakuType"""
        raise NotImplementedError

    @property
    def color(self) -> str:
        """获取对应的颜色"""
        return {
            GiftDanmakuType.NORMAL: DanmakuColors.GIFT_NORMAL,
            GiftDanmakuType.DENGPAI: DanmakuColors.GIFT_DENGPAI,
            GiftDanmakuType.JIANZHANG: DanmakuColors.GIFT_JIANZHANG,
            GiftDanmakuType.IMPORTANT: DanmakuColors.GIFT_IMPORTANT,
        }.get(self.type, DanmakuColors.DEFAULT)

    @property
    def badge_text(self) -> str:
        """获取前缀文本"""
        if text := {
            GiftDanmakuType.NORMAL: "礼物",
            GiftDanmakuType.DENGPAI: "粉丝灯牌",
            GiftDanmakuType.JIANZHANG: "大航海礼物",
            GiftDanmakuType.IMPORTANT: "贵重礼物",
        }.get(self.type):
            return f"{text}"
        else:
            return "礼物"

    def format_rich(self) -> str:
        """格式化为富文本显示"""
        raise NotImplementedError


@dataclass
class NoticeMessage(WebSocketMessage):
    def __repr__(self) -> str:
        raise NotImplementedError

    @property
    def type(self) -> NoticeDanmakuType:
        """获取对应的NoticeDanmakuType"""
        raise NotImplementedError

    @property
    def color(self) -> str:
        """获取对应的颜色"""
        return {
            NoticeDanmakuType.NORMAL: DanmakuColors.NOTICE_NORMAL,
            NoticeDanmakuType.IMPORTANT: DanmakuColors.NOTICE_IMPORTANT,
            NoticeDanmakuType.SYSTEM: DanmakuColors.NOTICE_SYSTEM,
        }.get(self.type, DanmakuColors.DEFAULT)

    @property
    def badge_text(self) -> str:
        """获取前缀文本"""
        if text := {
            NoticeDanmakuType.NORMAL: "提示",
            NoticeDanmakuType.SYSTEM: "系统提示",
            NoticeDanmakuType.IMPORTANT: "贵重礼物",
        }.get(self.type):
            return f"{text}"
        else:
            return "礼物"

    def format_rich(self) -> str:
        """格式化为富文本显示"""
        raise NotImplementedError


@dataclass
class OtherMessage(WebSocketMessage):
    pass


@dataclass
class STATUS:
    is_live: bool = False
    area_id: int = 0
    parent_area_id: int = 0
    title: str = ""
    attention: int = 0
    description: str = ""
    live_time: str = ""
    online: int = 0

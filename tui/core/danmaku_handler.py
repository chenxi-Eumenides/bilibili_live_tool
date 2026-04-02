"""弹幕消息处理器

参考blivedm.handlers的实现，提供消息处理接口和基础实现。
"""

from logging import getLogger
from typing import Optional, TYPE_CHECKING

from .danmaku_models import GiftMessage, DanmakuMessage, HeartbeatMessage

if TYPE_CHECKING:
    from .danmaku_fetcher import DanmakuClient

logger = getLogger(__name__)

__all__ = (
    "HandlerInterface",
    "BaseHandler",
)


class HandlerInterface:
    """直播消息处理器接口"""

    def handle(self, client: "DanmakuClient", command: dict):
        """处理消息

        Args:
            client: 弹幕客户端
            command: 命令数据
        """
        raise NotImplementedError

    def on_client_stopped(
        self, client: "DanmakuClient", exception: Optional[Exception]
    ):
        """当客户端停止时调用

        Args:
            client: 弹幕客户端
            exception: 异常信息，正常停止为None
        """
        pass


class BaseHandler(HandlerInterface):
    """基础消息处理器实现

    带消息分发和消息类型转换，继承并重写_on_xxx方法即可实现自定义处理器。
    """

    # 已知但不需要处理的命令（避免重复日志）
    _logged_unknown_cmds = {
        "SUPER_CHAT_MESSAGE_JPN",  # SC弹幕
        "ENTRY_EFFECT",  # 入场信息
        "NOTICE_MSG",  # 全站消息: 全站总督、全区道具抽奖广播
        "COMBO_SEND",
        "HOT_RANK_CHANGED",
        "HOT_RANK_CHANGED_V2",
        "LIVE",
        "LIVE_INTERACTIVE_GAME",
        "ONLINE_RANK_COUNT",
        "ONLINE_RANK_TOP3",
        "ONLINE_RANK_V2",
        "PK_BATTLE_END",
        "PK_BATTLE_FINAL_PROCESS",
        "PK_BATTLE_PROCESS",
        "PK_BATTLE_PROCESS_NEW",
        "PK_BATTLE_SETTLE",
        "PK_BATTLE_SETTLE_USER",
        "PK_BATTLE_SETTLE_V2",
        "PREPARING",
        "ROOM_REAL_TIME_MESSAGE_UPDATE",
        "STOP_LIVE_ROOM_LIST",
        "USER_TOAST_MSG",
        "WIDGET_BANNER",
        "MESSAGEBOX_USER_MEDAL_CHANGE",
        "WATCHED_CHANGE",
        "DM_INTERACTION",
        "INTERACT_WORD_V2",
        "LIKE_INFO_V3_UPDATE",
        "ONLINE_RANK_V3",
        "LIKE_INFO_V3_CLICK",
        "POPULAR_RANK_CHANGED",
        "RANK_CHANGED_V2",
        "ROOM_CHANGE",
        "CHG_RANK_REFRESH",
        "POPULARITY_RANK_TAB_CHG",
    }

    # 命令到处理方法的映射
    _CMD_CALLBACK_DICT = {
        # 收到心跳包（blivedm自造的消息）
        "_HEARTBEAT": "_on_heartbeat_callback",
        # 弹幕
        "DANMU_MSG": "_on_danmaku_callback",
        "DANMU_MSG_MIRROR": "_on_danmaku_mirror_callback",
        # 礼物
        "SEND_GIFT": "_on_gift_callback",
        # 入场信息
        "ENTRY_EFFECT": "_on_entry_effect_callback",
        # 全站消息
        "NOTICE_MSG": "_on_notice_msg_callback",
        # 测试
        "SUPER_CHAT_MESSAGE_JPN": "_on_test_callback",
    }

    def handle(self, client: "DanmakuClient", command: dict):
        """处理消息"""
        cmd = command.get("cmd", "")

        # 处理带参数的命令（B站弹幕协议升级后的格式）
        pos = cmd.find(":")
        if pos != -1:
            cmd = cmd[:pos]

        # 查找并调用对应的处理方法
        if cmd not in self._CMD_CALLBACK_DICT:
            # 只有第一次遇到未知cmd时打日志
            if cmd not in self._logged_unknown_cmds:
                logger.debug("room=%s unknown cmd=%s", client.room_id, cmd)
                self._logged_unknown_cmds.add(cmd)
            return

        callback_name = self._CMD_CALLBACK_DICT[cmd]
        callback = getattr(self, callback_name, None)
        if callback:
            callback(client, command)

    # ===== 回调方法 =====

    def _on_heartbeat_callback(self, client: "DanmakuClient", command: dict):
        """心跳回调"""
        message = HeartbeatMessage.from_command(command.get("data", {}))
        self._on_heartbeat(client, message)

    def _on_danmaku_callback(self, client: "DanmakuClient", command: dict):
        """弹幕回调"""
        message = DanmakuMessage.as_danmaku(command.get("info", []), is_mirror=False)
        self._on_danmaku(client, message)

    def _on_danmaku_mirror_callback(self, client: "DanmakuClient", command: dict):
        """跨房弹幕回调"""
        message = DanmakuMessage.as_danmaku(command.get("info", []), is_mirror=True)
        self._on_danmaku(client, message)

    def _on_gift_callback(self, client: "DanmakuClient", command: dict):
        """礼物回调"""
        message = GiftMessage.as_gift(command.get("data", {}))
        self._on_gift(client, message)

    def _on_entry_effect_callback(self, client: "DanmakuClient", data: dict):
        """入场信息回调"""
        self._on_entry_effect(client, data)

    def _on_notice_msg_callback(self, client: "DanmakuClient", data: dict):
        """全站消息回调"""
        self._on_notice_msg(client, data)

    def _on_test_callback(self, client: "DanmakuClient", command: dict):
        self._on_test(client, command)

    # ===== 可重写的方法 =====

    def _on_heartbeat(self, client: "DanmakuClient", message: HeartbeatMessage):
        """收到心跳包

        Args:
            client: 弹幕客户端
            message: 心跳消息
        """
        pass

    def _on_danmaku(self, client: "DanmakuClient", message: DanmakuMessage):
        """收到弹幕

        Args:
            client: 弹幕客户端
            message: 弹幕消息
        """
        pass

    def _on_gift(self, client: "DanmakuClient", message: GiftMessage):
        """收到礼物

        Args:
            client: 弹幕客户端
            message: 礼物消息
        """
        pass

    def _on_entry_effect(self, client: "DanmakuClient", data: dict):
        """入场信息

        Args:
            client: 弹幕客户端
            data: 入场信息数据
        """
        pass

    def _on_notice_msg(self, client: "DanmakuClient", data: dict):
        """全站消息

        Args:
            client: 弹幕客户端
            data: 全站消息数据
        """
        pass

    def _on_test(self, client: "DanmakuClient", command: dict):
        """测试信息

        Args:
            client: 弹幕客户端
            data: 入场信息数据
        """
        pass


class UIPanelHandler(BaseHandler):
    """UI面板处理器

    将弹幕消息转发到UI面板的处理器。
    """

    def __init__(self, panel):
        """
        Args:
            panel: DanmakuPanel实例
        """
        self._panel = panel

    def _on_danmaku(self, client: "DanmakuClient", message: DanmakuMessage):
        """收到弹幕，转发到面板"""
        if self._panel and hasattr(self._panel, "on_danmaku"):
            self._panel.on_danmaku(client.room_id, message)

    def _on_gift(self, client: "DanmakuClient", message: GiftMessage):
        """收到礼物，转发到面板"""
        if self._panel and hasattr(self._panel, "on_gift"):
            self._panel.on_gift(client.room_id, message)

    def on_client_stopped(
        self, client: "DanmakuClient", exception: Optional[Exception]
    ):
        """客户端停止"""
        if self._panel:
            if exception:
                if hasattr(self._panel, "on_error"):
                    self._panel.on_error(client.room_id, exception)
            else:
                if hasattr(self._panel, "on_disconnect"):
                    self._panel.on_disconnect(client.room_id)

    def _on_notice_msg(self, client: "DanmakuClient", data: dict):
        logger.debug(data.get("msg_common"))

    def _on_test(self, client: "DanmakuClient", command: dict):
        from json import dumps

        logger.debug(dumps(command, indent=4, ensure_ascii=False))

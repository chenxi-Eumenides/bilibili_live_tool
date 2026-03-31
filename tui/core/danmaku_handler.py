"""弹幕消息处理器

参考blivedm.handlers的实现，提供消息处理接口和基础实现。
"""

import logging
from typing import Optional, TYPE_CHECKING

from . import danmaku_models

if TYPE_CHECKING:
    from .danmaku_fetcher import DanmakuClient

logger = logging.getLogger(__name__)

__all__ = (
    'HandlerInterface',
    'BaseHandler',
)


class HandlerInterface:
    """直播消息处理器接口"""
    
    def handle(self, client: 'DanmakuClient', command: dict):
        """处理消息
        
        Args:
            client: 弹幕客户端
            command: 命令数据
        """
        raise NotImplementedError
    
    def on_client_stopped(self, client: 'DanmakuClient', exception: Optional[Exception]):
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
        'COMBO_SEND',
        'ENTRY_EFFECT',
        'HOT_RANK_CHANGED',
        'HOT_RANK_CHANGED_V2',
        'LIVE',
        'LIVE_INTERACTIVE_GAME',
        'NOTICE_MSG',
        'ONLINE_RANK_COUNT',
        'ONLINE_RANK_TOP3',
        'ONLINE_RANK_V2',
        'PK_BATTLE_END',
        'PK_BATTLE_FINAL_PROCESS',
        'PK_BATTLE_PROCESS',
        'PK_BATTLE_PROCESS_NEW',
        'PK_BATTLE_SETTLE',
        'PK_BATTLE_SETTLE_USER',
        'PK_BATTLE_SETTLE_V2',
        'PREPARING',
        'ROOM_REAL_TIME_MESSAGE_UPDATE',
        'STOP_LIVE_ROOM_LIST',
        'SUPER_CHAT_MESSAGE_JPN',
        'USER_TOAST_MSG',
        'WIDGET_BANNER',
    }
    
    # 命令到处理方法的映射
    _CMD_CALLBACK_DICT = {
        # 收到心跳包（blivedm自造的消息）
        '_HEARTBEAT': '_on_heartbeat_callback',
        # 弹幕
        'DANMU_MSG': '_on_danmaku_callback',
        'DANMU_MSG_MIRROR': '_on_danmaku_mirror_callback',
        # 礼物
        'SEND_GIFT': '_on_gift_callback',
    }
    
    def handle(self, client: 'DanmakuClient', command: dict):
        """处理消息"""
        cmd = command.get('cmd', '')
        
        # 处理带参数的命令（B站弹幕协议升级后的格式）
        pos = cmd.find(':')
        if pos != -1:
            cmd = cmd[:pos]
        
        # 查找并调用对应的处理方法
        if cmd not in self._CMD_CALLBACK_DICT:
            # 只有第一次遇到未知cmd时打日志
            if cmd not in self._logged_unknown_cmds:
                logger.debug('room=%s unknown cmd=%s', client.room_id, cmd)
                self._logged_unknown_cmds.add(cmd)
            return
        
        callback_name = self._CMD_CALLBACK_DICT[cmd]
        callback = getattr(self, callback_name, None)
        if callback:
            callback(client, command)
    
    # ===== 回调方法 =====
    
    def _on_heartbeat_callback(self, client: 'DanmakuClient', command: dict):
        """心跳回调"""
        message = danmaku_models.HeartbeatMessage.from_command(command.get('data', {}))
        self._on_heartbeat(client, message)
    
    def _on_danmaku_callback(self, client: 'DanmakuClient', command: dict):
        """弹幕回调"""
        message = danmaku_models.DanmakuMessage.from_command(command.get('info', []), is_mirror=False)
        self._on_danmaku(client, message)
    
    def _on_danmaku_mirror_callback(self, client: 'DanmakuClient', command: dict):
        """跨房弹幕回调"""
        message = danmaku_models.DanmakuMessage.from_command(command.get('info', []), is_mirror=True)
        self._on_danmaku(client, message)
    
    def _on_gift_callback(self, client: 'DanmakuClient', command: dict):
        """礼物回调"""
        message = danmaku_models.GiftMessage.from_command(command.get('data', {}))
        self._on_gift(client, message)
    
    # ===== 可重写的方法 =====
    
    def _on_heartbeat(self, client: 'DanmakuClient', message: danmaku_models.HeartbeatMessage):
        """收到心跳包
        
        Args:
            client: 弹幕客户端
            message: 心跳消息
        """
        pass
    
    def _on_danmaku(self, client: 'DanmakuClient', message: danmaku_models.DanmakuMessage):
        """收到弹幕
        
        Args:
            client: 弹幕客户端
            message: 弹幕消息
        """
        pass
    
    def _on_gift(self, client: 'DanmakuClient', message: danmaku_models.GiftMessage):
        """收到礼物
        
        Args:
            client: 弹幕客户端
            message: 礼物消息
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
    
    def _on_danmaku(self, client: 'DanmakuClient', message: danmaku_models.DanmakuMessage):
        """收到弹幕，转发到面板"""
        if self._panel and hasattr(self._panel, 'on_danmaku'):
            self._panel.on_danmaku(client.room_id, message)
    
    def _on_gift(self, client: 'DanmakuClient', message: danmaku_models.GiftMessage):
        """收到礼物，可扩展显示礼物信息"""
        logger.debug(f"收到礼物: {message.uname} 送了 {message.num}x {message.gift_name}")
    
    def on_client_stopped(self, client: 'DanmakuClient', exception: Optional[Exception]):
        """客户端停止"""
        if self._panel:
            if exception:
                if hasattr(self._panel, 'on_error'):
                    self._panel.on_error(client.room_id, exception)
            else:
                if hasattr(self._panel, 'on_disconnect'):
                    self._panel.on_disconnect(client.room_id)

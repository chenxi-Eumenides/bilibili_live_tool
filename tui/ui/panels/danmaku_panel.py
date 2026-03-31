"""弹幕面板

显示直播间弹幕列表，支持发送弹幕。
"""

import http.cookies
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import aiohttp
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.app import ComposeResult
from textual.reactive import reactive

from ...utils.constants import AppState
from ...utils.danmaku_config import (
    DanmakuType,
    DanmakuCategory,
    DANMAKU_COLORS,
    get_danmaku_color,
    get_danmaku_category,
    get_badge_type,
    get_notice_type,
)
from ...core.danmaku_models import DanmakuMessage as FetcherDanmakuMessage
from ...core.danmaku_fetcher import DanmakuClient
from ...core.danmaku_handler import UIPanelHandler

if TYPE_CHECKING:
    from ..app import BiliLiveApp

logger = logging.getLogger(__name__)


# 配置常量
DEFAULT_AUTO_SCROLL_LINES = 10  # 默认自动滚动范围（行数）
DEFAULT_MAX_DANMAKU_COUNT = 300  # 默认最大弹幕数量


class DanmakuMessage:
    """弹幕消息数据类（UI层）"""

    def __init__(
        self,
        username: str,
        content: str,
        badge: str = "",
        danmaku_type: DanmakuType = DanmakuType.USER_NORMAL,
        timestamp: datetime | None = None,
    ):
        self.username = username
        self.content = content
        self.badge = badge
        self.danmaku_type = danmaku_type
        self.timestamp = timestamp or datetime.now()

    @classmethod
    def from_fetcher_message(cls, msg: FetcherDanmakuMessage) -> "DanmakuMessage":
        """从获取器消息创建UI消息"""
        logger = logging.getLogger(__name__)
        
        # 根据勋章信息判断用户类型
        danmaku_type = DanmakuType.USER_NORMAL
        badge = msg.badge_text
        
        # 根据badge映射到类型，优先舰队等级
        if msg.privilege_type == 1:
            danmaku_type = DanmakuType.USER_ZONGDU
        elif msg.privilege_type == 2:
            danmaku_type = DanmakuType.USER_TIDU
        elif msg.privilege_type == 3:
            danmaku_type = DanmakuType.USER_JIANZHANG
        elif msg.admin:
            danmaku_type = DanmakuType.USER_ADMIN
            badge = "房管" if not badge else badge
        elif msg.medal_name:
            # 用户佩戴了粉丝牌，视为粉丝
            danmaku_type = DanmakuType.USER_FAN
        
        logger.debug(f"弹幕用户: {msg.uname}, privilege_type={msg.privilege_type}, badge={badge}, medal={msg.medal_name}, type={danmaku_type}")
            
        return cls(
            username=msg.uname,
            content=msg.msg,
            badge=badge,
            danmaku_type=danmaku_type,
            timestamp=datetime.fromtimestamp(msg.timestamp / 1000),
        )

    def format_rich(self) -> str:
        """格式化为富文本显示"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        time_part = f"[{DANMAKU_COLORS.TIMESTAMP}]{time_str}[/{DANMAKU_COLORS.TIMESTAMP}]"

        category = get_danmaku_category(self.danmaku_type)
        color = get_danmaku_color(self.danmaku_type)

        if category == DanmakuCategory.NOTICE:
            type_name = self._get_notice_type_name()
            content_part = f"[{color}]{type_name} {self.content}[/{color}]"
            return f"{time_part} {content_part}"

        parts = [time_part]
        if self.badge:
            parts.append(f"[{color}][{self.badge}][/{color}]")
        parts.append(f"[{color}]{self.username}:[/{color}]")
        parts.append(f"[{DANMAKU_COLORS.CONTENT}]{self.content}[/{DANMAKU_COLORS.CONTENT}]")

        return " ".join(parts)

    def _get_notice_type_name(self) -> str:
        """获取通知类型名称"""
        return {
            DanmakuType.NOTICE_IMPORTANT: "[重要]",
            DanmakuType.NOTICE_SYSTEM: "[系统]",
            DanmakuType.NOTICE_NORMAL: "[通知]",
        }.get(self.danmaku_type, "[通知]")


class DanmakuPanel(Vertical):
    """弹幕面板 - 显示弹幕列表和发送弹幕"""

    messages: reactive[list[DanmakuMessage]] = reactive([])

    @property
    def app(self) -> "BiliLiveApp":
        return super().app  # type: ignore

    def __init__(
        self,
        auto_scroll_lines: int = DEFAULT_AUTO_SCROLL_LINES,
        max_danmaku_count: int = DEFAULT_MAX_DANMAKU_COUNT,
    ):
        super().__init__()
        self._auto_scroll_lines = auto_scroll_lines
        self._max_danmaku_count = max_danmaku_count
        self._last_message_count = 0
        self._fetcher: DanmakuClient | None = None
        self._placeholder_removed = False
        self._session: 'aiohttp.ClientSession | None' = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="danmaku-container"):
            with Vertical(classes="danmaku-list-wrapper"):
                yield Button("↓ 有新弹幕", id="new-danmaku-hint", classes="new-danmaku-hint hidden", variant="default")
                with ScrollableContainer(id="danmaku-list", classes="danmaku-list"):
                    yield Static("当前没有直播间", id="danmaku-placeholder")

            with Horizontal(classes="danmaku-input-row"):
                yield Input(placeholder="发送弹幕...", id="danmaku-input", classes="danmaku-input")
                yield Button("发送", id="danmaku-send", variant="primary", classes="danmaku-send-btn")

    def on_mount(self):
        """组件挂载时启动弹幕获取"""
        # 启动弹幕获取（如果已登录且有房间ID）
        self._start_danmaku_fetch()

    def on_unmount(self):
        """组件卸载时停止弹幕获取"""
        self._stop_danmaku_fetch()

    async def _fetch_room_info(self, session: aiohttp.ClientSession, room_id: int) -> dict:
        """获取直播间信息"""
        try:
            url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("code") == 0:
                        return data.get("data", {})
        except Exception:
            pass
        return {}

    def _start_danmaku_fetch(self):
        """启动弹幕获取"""
        # 从配置获取房间ID
        room_id = self.app.config_manager.config.room_id
        
        # 没有房间ID则不启动
        if room_id <= 0:
            return
        
        async def do_start():
            try:
                # 获取cookies
                cookies_str = self.app.config_manager.config.cookies_str
                
                # 创建带cookie的session
                if cookies_str:
                    cookies = http.cookies.SimpleCookie()
                    cookies.load(cookies_str)
                    self._session = aiohttp.ClientSession()
                    self._session.cookie_jar.update_cookies(cookies)
                else:
                    self._session = aiohttp.ClientSession()
                
                # 获取直播间信息
                room_info = await self._fetch_room_info(self._session, room_id)
                room_title = room_info.get("title", "")
                logger.info(f"弹幕直播间信息: [{room_id}] {room_title}")
                
                # 移除占位符文字
                try:
                    placeholder = self.query_one("#danmaku-placeholder", Static)
                    placeholder.update("暂无弹幕")
                except Exception:
                    pass
                
                # 创建客户端和处理器，传入带cookie的session
                self._fetcher = DanmakuClient(room_id, session=self._session)
                handler = UIPanelHandler(self)
                self._fetcher.set_handler(handler)
                
                # 启动客户端（非阻塞）
                self._fetcher.start()
                
            except Exception as e:
                self.app.show_notification(f"弹幕连接失败: {e}")
        
        # 启动异步任务
        self.run_worker(do_start(), exclusive=True)

    def _stop_danmaku_fetch(self):
        """停止弹幕获取"""
        if self._fetcher:
            # 先停止客户端
            self._fetcher.stop()
            # 异步关闭资源
            self.run_worker(self._async_close_fetcher(), exclusive=True)
    
    async def _async_close_fetcher(self):
        """异步关闭获取器资源"""
        try:
            if self._fetcher:
                # 等待客户端完全停止
                await self._fetcher.join()
                # 关闭session
                await self._fetcher.close()
                self._fetcher = None
            # 关闭面板持有的session
            if self._session:
                await self._session.close()
                self._session = None
        except Exception:
            pass

    # ===== DanmakuHandler 回调方法 =====

    def on_danmaku(self, room_id: int, message: FetcherDanmakuMessage):
        """收到弹幕消息（回调）
        
        注意：此回调可能在异步协程中执行，需要使用 call_later 确保UI更新在主线程
        """
        # 使用 call_later 在主事件循环中执行UI更新
        self.app.call_later(self._add_message_from_fetcher, message)

    def _add_message_from_fetcher(self, msg: FetcherDanmakuMessage):
        """添加来自获取器的消息"""
        # 第一次收到消息时移除占位符
        if not self._placeholder_removed:
            try:
                placeholder = self.query_one("#danmaku-placeholder", Static)
                placeholder.remove()
                self._placeholder_removed = True
            except Exception:
                pass
        
        danmaku_msg = DanmakuMessage.from_fetcher_message(msg)
        self.messages.append(danmaku_msg)
        self._cleanup_messages()
        self._incremental_refresh()

    def on_connect(self, room_id: int):
        """连接成功"""
        logger.info(f"弹幕连接成功 [房间:{room_id}]")

    def on_disconnect(self, room_id: int):
        """断开连接"""
        logger.info(f"弹幕连接断开 [房间:{room_id}]")

    def on_error(self, room_id: int, error: Exception):
        """连接错误"""
        logger.error(f"弹幕错误 [房间:{room_id}]: {error}")

    # ===== UI 更新方法 =====

    def _is_near_bottom(self, container: ScrollableContainer) -> bool:
        """检查是否接近底部"""
        try:
            # 如果内容高度小于容器高度（弹幕很少），视为在底部
            content_height = container.virtual_size.height
            container_height = container.size.height
            if content_height <= container_height:
                return True
            
            if not container.scroll_offset:
                return False

            current_scroll = container.scroll_offset.y
            max_scroll = max(0, content_height - container_height)

            if max_scroll <= 0:
                return True

            scroll_threshold = min(container_height, self._auto_scroll_lines)
            distance_from_bottom = max_scroll - current_scroll
            return distance_from_bottom <= scroll_threshold
        except Exception:
            return False

    def _update_hint_visibility(self, is_near_bottom: bool):
        try:
            hint = self.query_one("#new-danmaku-hint", Button)
            hint.add_class("hidden") if is_near_bottom else hint.remove_class("hidden")
        except Exception:
            pass

    def _incremental_refresh(self):
        """增量刷新（只添加新弹幕）"""
        try:
            danmaku_list = self.query_one("#danmaku-list", ScrollableContainer)
            was_near_bottom = self._is_near_bottom(danmaku_list)

            current_count = len(self.messages)
            if current_count > self._last_message_count:
                new_messages = self.messages[self._last_message_count:]
                for msg in new_messages:
                    danmaku_list.mount(Static(msg.format_rich(), classes="danmaku-item"))
                self._last_message_count = current_count

                self._update_hint_visibility(was_near_bottom)
                if was_near_bottom:
                    danmaku_list.scroll_end(animate=False)

        except Exception:
            pass


    def _cleanup_messages(self):
        """清理弹幕数量"""
        if len(self.messages) > self._max_danmaku_count:
            self.messages = self.messages[-(self._max_danmaku_count // 2):]
            self._last_message_count = len(self.messages)

    # ===== 用户交互方法 =====

    def add_message(self, username: str, content: str, badge: str = "", danmaku_type: DanmakuType | None = None):
        """添加新弹幕消息（本地发送时使用）"""
        if danmaku_type is None:
            danmaku_type = get_badge_type(badge)
        self.messages.append(DanmakuMessage(username, content, badge, danmaku_type))
        self._cleanup_messages()
        self._incremental_refresh()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "danmaku-send":
            self._send_danmaku()
        elif event.button.id == "new-danmaku-hint":
            # 点击"有新弹幕"提示，滚动到底部
            try:
                danmaku_list = self.query_one("#danmaku-list", ScrollableContainer)
                danmaku_list.scroll_end(animate=False)
                # 隐藏提示
                hint = self.query_one("#new-danmaku-hint", Button)
                hint.add_class("hidden")
            except Exception:
                pass

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "danmaku-input":
            self._send_danmaku()

    def _send_danmaku(self):
        """发送弹幕"""
        input_widget = self.query_one("#danmaku-input", Input)
        content = input_widget.value.strip()

        if not content:
            self.app.show_notification("弹幕内容不能为空")
            return

        if self.app.app_state == AppState.UNAUTH:
            self.app.show_notification("请先登录")
            return

        # TODO: 调用实际的弹幕发送API
        self.add_message("我", content, "")
        input_widget.value = ""
        self.app.show_notification("弹幕发送成功")

"""主控制台面板

显示直播间信息和快捷操作。
"""

from datetime import datetime, timedelta

from textual.widgets import Static
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.app import ComposeResult

from ...utils.constants import AppState
from ...core.config import Config
from ..layout.header import Header

# 类型声明
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..app import BiliLiveApp

class DashboardPanel(Vertical):
    """主控制台面板"""
    @property
    def app(self) -> "BiliLiveApp":
        return super().app # type: ignore

    def __init__(self):
        super().__init__()
        self._start_time: datetime | None = None  # 开播时间点
        self._duration_timer = None  # 直播时长计时器（每秒更新显示）
        self._refresh_timer = None  # 5分钟刷新计时器

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="info-card"):
            yield Static("直播间信息", classes="section-title")
            # 标题（全宽）
            with Vertical(classes="full-width"):
                yield Static("标题", classes="info-label")
                yield Static("--", id="room-title", classes="info-value")
            # 2列信息网格
            with Grid(classes="info-grid"):
                # 左侧列
                with Vertical(classes="column-left"):
                    with Vertical(classes="info-item"):
                        yield Static("主播UID", classes="info-label")
                        yield Static("--", id="anchor-uid", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("粉丝数", classes="info-label")
                        yield Static("--", id="follower-count", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("在线人数", classes="info-label")
                        yield Static("--", id="room-online", classes="info-value")
                # 右侧列
                with Vertical(classes="column-right"):
                    with Vertical(classes="info-item"):
                        yield Static("房间号", classes="info-label")
                        yield Static("--", id="room-id", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("分区", classes="info-label")
                        yield Static("--", id="room-area", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("直播时长", classes="info-label")
                        yield Static("--", id="room-duration", classes="info-value")
            # 推流地址（全宽）
            with Vertical(classes="full-width"):
                yield Static("推流地址", classes="info-label")
                yield Static("--", id="rtmp-addr", classes="info-value")
            # 推流码（全宽）
            with Vertical(classes="full-width"):
                yield Static("推流码", classes="info-label")
                yield Static("--", id="rtmp-code", classes="info-value")

    def on_mount(self):
        """组件挂载时更新信息"""
        self._update_from_config()
        # DashboardPanel 初始化时获取一次直播间信息
        self.run_worker(self._fetch_and_update, thread=True)
        # 启动5分钟定时刷新
        self._start_refresh_timer()

    def on_unmount(self):
        """组件卸载时清理计时器"""
        self._stop_duration_timer()
        self._stop_refresh_timer()

    def _start_duration_timer(self):
        """启动直播时长计时器（每秒更新显示）"""
        self._stop_duration_timer()
        self._duration_timer = self.set_interval(1, self._update_duration_display)

    def _stop_duration_timer(self):
        """停止直播时长计时器"""
        if self._duration_timer:
            self._duration_timer.stop()
            self._duration_timer = None

    def _start_refresh_timer(self):
        """启动5分钟定时刷新"""
        self._stop_refresh_timer()
        # 5分钟 = 300秒
        self._refresh_timer = self.set_interval(300, self._periodic_refresh)

    def _stop_refresh_timer(self):
        """停止刷新计时器"""
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None

    def _periodic_refresh(self):
        """定时刷新直播间信息"""
        # 只在已登录状态下刷新
        if self.app.app_state.value in [1, 2]:  # IDLE or LIVE
            self.run_worker(self._fetch_and_update, thread=True, exclusive=True)

    def _parse_start_time(self, live_time_str: str) -> datetime | None:
        """解析开播时间点字符串

        Args:
            live_time_str: 开播时间点字符串，格式如:
                - "YYYY-MM-DD HH:MM:SS" (API返回的开播时间)
                - "0000-00-00 00:00:00" (未开播时的默认值)

        Returns:
            datetime对象，表示开播时间点
            解析失败或未开播时返回None
        """
        if not live_time_str or live_time_str in ["--", "0000-00-00 00:00:00"]:
            return None

        try:
            return datetime.strptime(live_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    def _format_duration(self, duration: timedelta) -> str:
        """格式化时长为 HH:MM:SS 格式

        Args:
            duration: 时长timedelta对象

        Returns:
            格式化字符串，如 "02:30:45"
        """
        total_seconds = int(duration.total_seconds())
        if total_seconds < 0:
            return "00:00:00"

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _update_duration_display(self):
        """更新直播时长显示（每秒调用）"""
        if self._start_time is None:
            self.query_one("#room-duration", Static).update("--")
            return

        # 实时计算从开播到现在的时间差
        duration = datetime.now() - self._start_time
        duration_str = self._format_duration(duration)
        self.query_one("#room-duration", Static).update(duration_str)

    def _update_from_config(self):
        """从配置更新显示"""
        try:
            config: Config = self.app.config_manager.get_config()
            room_data = config.room_data if config else {}

            if room_data:
                # 更新基本信息
                self.query_one("#room-title", Static).update(
                    room_data.get("title", "未设置")
                )
                self.query_one("#anchor-uid", Static).update(
                    str(room_data.get("uid", "--"))
                )
                parent_area = room_data.get("parent_area_name", "未知")
                area = room_data.get("area_name", "未知")
                self.query_one("#room-area", Static).update(f"{parent_area}/{area}")
                self.query_one("#room-online", Static).update(
                    str(room_data.get("online", "--"))
                )
                self.query_one("#follower-count", Static).update(
                    str(room_data.get("attention", "--"))
                )
                self.query_one("#room-id", Static).update(
                    str(config.room_id) if config.room_id > 0 else "--"
                )
                self.query_one("#rtmp-addr", Static).update(
                    str(config.rtmp_addr) if config.rtmp_addr else "--"
                )
                self.query_one("#rtmp-code", Static).update(
                    str(config.rtmp_code) if config.rtmp_code else "--"
                )

                # 处理直播时长
                live_time_str = room_data.get("live_time", "")
                is_live = room_data.get("live_status") == 1

                if is_live:
                    # 正在直播：解析开播时间点并启动计时器
                    self._start_time = self._parse_start_time(live_time_str)
                    if self._start_time:
                        self._start_duration_timer()
                        self._update_duration_display()
                    else:
                        self.query_one("#room-duration", Static).update("--")
                else:
                    # 未开播：显示默认值，停止计时器
                    self._stop_duration_timer()
                    self._start_time = None
                    self.query_one("#room-duration", Static).update("--")
            else:
                # 没有room_data时显示默认值
                self._stop_duration_timer()
                self._start_time = None
                self.query_one("#room-online", Static).update("--")
                self.query_one("#anchor-uid", Static).update(
                    str(config.user_id) if config.user_id > 0 else "--"
                )
                self.query_one("#follower-count", Static).update("--")
                self.query_one("#room-id", Static).update(
                    str(config.room_id) if config.room_id > 0 else "--"
                )
                self.query_one("#room-duration", Static).update("--")

        except Exception:
            pass

    def _fetch_and_update(self):
        """后台获取最新数据并更新"""
        try:
            # 设置更新状态为"更新中"
            self.app.call_from_thread(self._set_update_status, "更新中...", "yellow")

            # 获取最新直播间信息
            info = self.app.live_manager.fetch_room_info()
            config: Config = self.app.config_manager.get_config()

            if info:
                # 更新UI基本信息
                self.app.call_from_thread(
                    self.query_one("#room-title", Static).update, info.title or "未设置"
                )
                self.app.call_from_thread(
                    self.query_one("#anchor-uid", Static).update,
                    str(info.uid) if info.uid else "--",
                )
                self.app.call_from_thread(
                    self.query_one("#room-id", Static).update,
                    str(info.room_id) if info.room_id else "--",
                )
                self.app.call_from_thread(
                    self.query_one("#room-area", Static).update,
                    f"{info.parent_area_name}/{info.area_name}",
                )
                self.app.call_from_thread(
                    self.query_one("#room-online", Static).update,
                    str(info.online) if info.online is not None else "--",
                )
                self.app.call_from_thread(
                    self.query_one("#follower-count", Static).update,
                    str(info.attention) if info.attention is not None else "--",
                )
                self.app.call_from_thread(
                    self.query_one("#rtmp-addr", Static).update,
                    str(config.rtmp_addr) if config.rtmp_addr else "--"
                )
                self.app.call_from_thread(
                    self.query_one("#rtmp-code", Static).update,
                    str(config.rtmp_code) if config.rtmp_code else "--"
                )

                # 处理直播时长
                def update_live_duration():
                    config = self.app.config_manager.get_config()
                    room_data = config.room_data if config else {}
                    live_time_str = room_data.get("live_time", "")
                    is_live = info.live_status == 1

                    if is_live:
                        # 正在直播：解析开播时间点并启动计时器
                        self._start_time = self._parse_start_time(live_time_str)
                        if self._start_time:
                            self._start_duration_timer()
                            self._update_duration_display()
                        else:
                            self.query_one("#room-duration", Static).update("--")
                    else:
                        # 未开播：显示默认值，停止计时器
                        self._stop_duration_timer()
                        self._start_time = None
                        self.query_one("#room-duration", Static).update("--")

                self.app.call_from_thread(update_live_duration)
                self.app.app_state = (
                    self.app.app_state
                    if self.app.app_state == AppState.UNAUTH
                    else (AppState.LIVE if info.live_status == 1 else AppState.IDLE)
                )

            # 清除更新状态
            self.app.call_from_thread(self._set_update_status, "", "")

        except Exception as e:
            # 出错时显示错误状态
            self.app.call_from_thread(self._set_update_status, "更新失败", "red")
            self.app.status_message = f"更新直播间信息失败: {str(e)}"
    
    def _set_update_status(self, status_text: str, color: str = ""):
        """设置更新状态显示

        Args:
            status_text: 状态文本 (如 "更新中...", "已更新")
            color: 颜色 (red, green, yellow, blue)
        """
        try:
            header: Header = self.app.query_one("Header", Header)
            header.set_update_status(status_text, color)
        except Exception:
            pass

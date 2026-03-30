"""Textual App主类

定义BiliLiveApp主类和全局状态管理。
"""

import logging
import threading

from textual.app import App
from textual.reactive import reactive
from textual.binding import Binding
from textual.containers import Horizontal

from ..core.config import ConfigManager
from ..core.auth import AuthManager
from ..core.live import LiveManager
from ..utils.constants import AppState, KeyBindings, VERSION_STR, Messages

from .layout.header import Header
from .layout.sidebar import Sidebar
from .layout.main_panel import MainPanel
from .layout.status_bar import StatusBar
from .screen.QRDisplayScreen import QRDisplayScreen


class BiliLiveApp(App):
    """B站直播工具TUI应用主类"""

    # CSS文件路径列表 - 按顺序加载
    CSS_PATH = [
        "styles/global.tcss",
        "styles/layout.tcss",
        "styles/auth_panel.tcss",
        "styles/dashboard_panel.tcss",
        "styles/settings_panel.tcss",
        "styles/help_panel.tcss",
        "styles/stream_panel.tcss",
    ]

    # 全局状态 - 响应式属性
    app_state = reactive(AppState.UNAUTH)
    status_message = reactive("")
    is_loading = reactive(False)
    qr_status = reactive(True)

    # 当前选中的侧边栏项目
    current_panel = reactive("info")  # "info", "manage", "help"

    # 快捷键绑定
    BINDINGS = [
        Binding(KeyBindings.QUIT, "quit_action", "退出"),
    ]

    def __init__(self):
        super().__init__()

        # 添加明显分隔线，用于区分不同运行实例的日志
        import logging
        logger = logging.getLogger("tui.app")
        logger.info("=" * 40)

        # 初始化核心管理器
        self.config_manager = ConfigManager()
        self.auth_manager = AuthManager(self.config_manager)
        self.live_manager = LiveManager(self.config_manager)

    def compose(self):
        """组合UI组件"""
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield MainPanel()
        yield StatusBar()

    def on_mount(self):
        """应用挂载时检查初始状态"""
        self._check_initial_state()

    def _check_initial_state(self):
        """检查初始登录状态

        1. 尝试加载配置
        2. 如果能读取，检查cookie是否过期
        3. 从服务器获取真实直播状态
        4. 设置全局状态并显示相应提示
        """
        # 尝试加载配置
        load_success = self.config_manager.load()

        if not load_success:
            # 配置文件不存在或读取失败
            self.app_state = AppState.UNAUTH
            self.show_notification("配置文件不存在，请先登录")
            return

        # 配置加载成功，检查登录态
        if self.auth_manager.check_auth():
            # 获取分区列表（如果为空）
            if not self.config_manager.config.area_list:
                self.live_manager.fetch_area_list()

            # 从服务器获取真实直播状态
            room_info = self.live_manager.fetch_room_info()
            if room_info and room_info.live_status == 1:
                self.app_state = AppState.LIVE
            else:
                self.app_state = AppState.IDLE
        else:
            # 登录态过期
            self.app_state = AppState.UNAUTH
            self.config_manager.clear()
            self.show_notification("登录已过期，请重新登录")

    def watch_app_state(self, state: AppState):
        """监听状态变化，更新UI"""
        try:
            # 更新主面板内容
            main_panel = self.query_one(MainPanel)
            main_panel.update_for_state(state, self.current_panel)

            # 更新侧边栏按钮样式
            sidebar = self.query_one(Sidebar)
            sidebar.update_button_states(state, self.current_panel)

            # 更新头部状态
            header = self.query_one(Header)
            if state == AppState.UNAUTH:
                header.update_status("未登录", "red")
            elif state == AppState.LIVE:
                header.update_status("直播中", "blue")
            else:  # IDLE
                header.update_status("已登录", "green")
        except Exception:
            pass

    def watch_current_panel(self, panel: str):
        """监听面板切换"""
        try:
            main_panel = self.query_one(MainPanel)
            main_panel.update_for_state(self.app_state, panel)

            sidebar = self.query_one(Sidebar)
            sidebar.update_button_states(self.app_state, panel)
        except Exception:
            pass

    def watch_status_message(self, message: str):
        """监听状态消息变化"""
        if message:
            logging.info(message)

    def action_quit_action(self):
        """退出应用"""
        # 停止登录流程（如果正在运行）
        self._stop_auth_worker()
        # 配置在on_unmount中统一保存，这里不重复保存
        self.exit()

    def on_unmount(self):
        """应用卸载时的清理"""
        # 停止登录流程
        self._stop_auth_worker()
        # 关闭二维码界面（这会触发人脸识别流程的回调）
        self.close_qr()
        # 统一在这里保存配置（无论是正常退出还是异常退出）
        self.config_manager.save()

    def _stop_auth_worker(self):
        """停止登录worker"""
        try:
            from ..ui.panels.auth_panel import AuthPanel
            auth_panel = self.query_one(AuthPanel)
            auth_panel.stop_login()
        except Exception:
            pass

    # ===== 面板切换 =====

    def show_info_panel(self):
        """显示信息面板"""
        self.current_panel = "info"

    def show_manage_panel(self):
        """显示管理面板"""
        self.current_panel = "manage"

    def show_help_panel(self):
        """显示帮助面板"""
        self.current_panel = "help"

    # ===== 登录回调 =====

    def on_login_success(self):
        """登录成功回调"""
        self.live_manager.fetch_room_info()

        if self.live_manager.is_living():
            self.app_state = AppState.LIVE
        else:
            self.app_state = AppState.IDLE

        self.status_message = "登录成功"

    # ===== 提示框 =====

    def show_notification(self, message: str):
        """显示通知提示

        Args:
            message: 提示消息
        """
        # 使用Textual的通知功能
        self.notify(message, timeout=3)

    # ===== 二维码显示 =====

    def show_qr(self, qr_url: str, title: str = "扫码登录", callback=None):
        """显示二维码

        Args:
            qr_url: 二维码URL
            title: 面板标题
            callback: 二维码关闭时的回调函数，接收一个bool参数(True=成功, False=失败/取消)
        """
        try:
            # 先关闭已存在的二维码面板
            self.close_qr()
            # 挂载新的二维码面板
            screen = QRDisplayScreen(qr_url, title)
            self.push_screen(screen, callback=callback)
            return screen
        except Exception as e:
            self.show_notification(f"显示二维码失败: {e}")
            return None

    def close_qr(self):
        """关闭二维码"""
        try:
            # 检查当前屏幕是否是二维码屏幕
            if len(self.screen_stack) > 1:
                self._logger.info(f"{self.screen_stack[-1].title} 已关闭")
                self.pop_screen()
                
        except Exception:
            pass

    # ===== 开播/下播 =====

    def action_toggle_live(self):
        """开播/下播切换"""
        if self.app_state == AppState.UNAUTH:
            # 未登录，弹出提示
            self.show_notification(Messages.NOT_LOGGED_IN)
            return

        if self.app_state == AppState.IDLE:
            # 检查信息是否完整
            if not self.config_manager.can_start_live():
                self.show_notification(Messages.MISSING_INFO)
                return
            # 执行开播
            self._start_live()
        elif self.app_state == AppState.LIVE:
            # 执行下播
            self._stop_live()

    def _start_live(self):
        """执行开播操作"""
        self.is_loading = True

        try:
            # 调用核心层开播
            success, message, need_face_auth, qr_url = self.live_manager.start_live()

            if success:
                # 开播成功，重新获取直播间信息并更新UI
                self._refresh_room_info_after_start()
                self.app_state = AppState.LIVE
                self.status_message = "开播成功"
            elif need_face_auth and self.qr_status and qr_url:
                # 需要人脸识别且二维码URL有效
                self._do_face_auth(qr_url)
                self.qr_status = False
                # 回到主线程重新开播
                self.call_from_thread(self._start_live)
                self.qr_status = True
            else:
                # 开播失败
                self.status_message = f"开播失败: {message}"
        except Exception as e:
            self.status_message = f"开播异常: {e}"
        finally:
            self.is_loading = False

    def _refresh_room_info_after_start(self):
        """开播成功后刷新直播间信息"""
        def refresh():
            try:
                # 重新获取直播间信息
                self.live_manager.fetch_room_info()
                # 通知DashboardPanel刷新显示
                from .panels.dashboard_panel import DashboardPanel
                dashboard = self.query_one(DashboardPanel)
                if dashboard:
                    dashboard.run_worker(dashboard._fetch_and_update, thread=True)
            except Exception:
                pass
        # 在后台线程执行
        threading.Thread(target=refresh, daemon=True).start()

    def _do_face_auth(self, qr_url: str):
        """执行人脸识别流程
        
        Args:
            qr_url: 人脸识别二维码URL
        """

        # 创建停止事件
        stop_event = threading.Event()
        face_success_result = [False]  # 使用列表来存储结果，避免nonlocal问题

        def on_qr_closed(success: bool):
            """二维码关闭回调 - 只在用户主动关闭时停止流程"""
            if not success and not face_success_result[0]:
                # 用户主动关闭且人脸验证未成功，停止人脸识别流程
                stop_event.set()

        # 显示二维码
        self.show_qr(qr_url, "人脸识别", callback=on_qr_closed)

        # face_success = self.live_manager.check_face_auth(qr_url, stop_event)
        # face_success_result[0] = face_success
        
        # if face_success:
        #     # 人脸识别成功，关闭二维码（会触发on_qr_closed(True)，但不会停止流程）
        #     self.call_from_thread(self.close_qr)
        # else:
        #     # 人脸识别失败或取消
        #     if not stop_event.is_set():
        #         # 不是用户主动取消，显示失败信息
        #         self.call_from_thread(
        #             lambda: setattr(self, "status_message", "人脸识别失败或超时")
        #         )
        #     self.call_from_thread(self.close_qr)
        # return

        # 在后台线程中检查人脸识别状态
        def check_face_auth_worker():
            face_success = self.live_manager.check_face_auth(qr_url, stop_event)
            face_success_result[0] = face_success
            
            if face_success:
                # 人脸识别成功，关闭二维码（会触发on_qr_closed(True)，但不会停止流程）
                self.call_from_thread(self.close_qr)
            else:
                # 人脸识别失败或取消
                if not stop_event.is_set():
                    # 不是用户主动取消，显示失败信息
                    self.call_from_thread(
                        lambda: setattr(self, "status_message", "人脸识别失败或超时")
                    )
                self.call_from_thread(self.close_qr)

        # 启动后台线程
        threading.Thread(target=check_face_auth_worker, daemon=True).start()

    def _stop_live(self):
        """执行下播操作"""
        self.is_loading = True
        self.status_message = "正在下播..."

        try:
            success, message = self.live_manager.stop_live()
            if success:
                self.app_state = AppState.IDLE
                self.status_message = "下播成功"
            else:
                self.status_message = f"下播失败: {message}"
        except Exception as e:
            self.status_message = f"下播异常: {e}"
        finally:
            self.is_loading = False
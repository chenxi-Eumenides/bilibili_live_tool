"""推流信息面板

显示推流地址和推流码。
"""

from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult


class StreamPanel(Vertical):
    """推流信息面板"""

    DEFAULT_CSS = """
    StreamPanel {
        height: 100%;
    }
    StreamPanel .stream-card {
        background: $surface-darken-1;
        border: solid $primary;
        padding: 2;
        margin: 1 0;
    }
    StreamPanel .stream-label {
        color: $text-muted;
        margin-bottom: 1;
    }
    StreamPanel .stream-value {
        background: $surface-darken-2;
        color: $text;
        padding: 1;
        text-style: bold;
        margin-bottom: 2;
    }
    StreamPanel .button-row {
        height: auto;
        margin-top: 2;
    }
    StreamPanel #live-indicator {
        text-align: center;
        text-style: bold;
        color: $error;
        margin-bottom: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[直播中]", id="live-indicator")

        with Vertical(classes="stream-card"):
            yield Static("推流地址 (服务器):", classes="stream-label")
            yield Static("未获取", id="rtmp-addr", classes="stream-value")
            yield Button("复制地址", id="btn-copy-addr")

            yield Static("推流码 (串流密钥):", classes="stream-label")
            yield Static("未获取", id="rtmp-code", classes="stream-value")
            yield Button("复制推流码", id="btn-copy-code")

        with Horizontal(classes="button-row"):
            yield Button("复制全部", id="btn-copy-all", variant="primary")
            yield Button("刷新", id="btn-refresh")
            yield Button("结束直播", id="btn-stop", variant="error")

        with Vertical(classes="stream-card"):
            yield Static("OBS配置指南:", classes="stream-label")
            yield Static(self._get_obs_guide(), id="obs-guide")

    def _get_obs_guide(self) -> str:
        """获取OBS配置说明"""
        return """1. 打开OBS → 设置 → 直播
2. 服务选择："自定义..."
3. 服务器：粘贴推流地址
4. 串流密钥：粘贴推流码
5. 点击"应用"然后"确定"
6. 点击"开始直播"按钮"""

    def on_mount(self):
        """组件挂载时更新推流信息"""
        self._update_stream_info()

    def _update_stream_info(self):
        """更新推流信息显示"""
        try:
            app = self.app
            config = app.config_manager.get_config()

            if config.rtmp_addr:
                self.query_one("#rtmp-addr", Static).update(config.rtmp_addr)
            if config.rtmp_code:
                self.query_one("#rtmp-code", Static).update(config.rtmp_code)

        except Exception as e:
            self.query_one("#rtmp-addr", Static).update(f"获取失败: {e}")

    def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击"""
        btn_id = event.button.id

        if btn_id == "btn-copy-addr":
            self._copy_addr()
        elif btn_id == "btn-copy-code":
            self._copy_code()
        elif btn_id == "btn-copy-all":
            self._copy_all()
        elif btn_id == "btn-refresh":
            self._update_stream_info()
            self.app.status_message = "已刷新"
        elif btn_id == "btn-stop":
            self.app.action_toggle_live()

    def _copy_addr(self):
        """复制推流地址到剪贴板"""
        try:
            import pyperclip
            app = self.app
            addr = app.config_manager.get_config().rtmp_addr
            pyperclip.copy(addr)
            self.app.status_message = "推流地址已复制"
        except Exception:
            self.app.status_message = "复制失败，请手动复制"

    def _copy_code(self):
        """复制推流码到剪贴板"""
        try:
            import pyperclip
            app = self.app
            code = app.config_manager.get_config().rtmp_code
            pyperclip.copy(code)
            self.app.status_message = "推流码已复制"
        except Exception:
            self.app.status_message = "复制失败，请手动复制"

    def _copy_all(self):
        """复制全部信息到剪贴板"""
        try:
            import pyperclip
            app = self.app
            config = app.config_manager.get_config()
            text = f"服务器: {config.rtmp_addr}\n串流密钥: {config.rtmp_code}"
            pyperclip.copy(text)
            self.app.status_message = "全部信息已复制"
        except Exception:
            self.app.status_message = "复制失败，请手动复制"

    def start_edit_title(self):
        """外部调用：开始编辑标题"""
        pass

    def start_edit_area(self):
        """外部调用：开始编辑分区"""
        pass

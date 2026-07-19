"""高精度二维码显示组件.

支持两种渲染模式:
  现代终端 --- 使用半块字符压缩, 二维码接近正方形
  兼容终端 --- 使用全块字符, 逐行渲染, 适合 cmd.exe 等老式终端
"""

import logging

from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button
from textual.reactive import reactive
from textual.binding import Binding

from ...utils.constants import KeyBindings
from ...utils.qrcode_utils import build_qr_matrix, build_qr_lines

logger = logging.getLogger(__name__)


class QRDisplayScreen(ModalScreen):
    """二维码显示面板"""

    BINDINGS = [
        Binding(KeyBindings.QUIT, "quit_action", "退出"),
    ]

    qr_url = reactive("")
    qr_text = reactive("")

    def __init__(self, qr_url: str, title: str = "扫码登录"):
        super().__init__()
        self.qr_url = qr_url
        self.title_text = title
        self._compat = False

    def compose(self):
        with Vertical(id="qr-card"):
            with Horizontal(id="qr-header"):
                yield Static(self.title_text, id="qr-title")
                yield Button("切换兼容显示", id="qr-toggle-btn")
            yield Static("", id="qr-content")
            yield Static("窗口太小，请放大后查看二维码", id="qr-too-small")

    def on_mount(self):
        """挂载时显示二维码"""
        self._update_display()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "qr-toggle-btn":
            return
        self._compat = not self._compat
        btn = event.button
        if self._compat:
            btn.label = "切换压缩显示"
        else:
            btn.label = "切换兼容显示"
        self._update_display()

    def _update_display(self):
        """更新二维码显示"""
        if not self.qr_url:
            return

        try:
            self._generate_qr_data()

            container_width = self.size.width if self.size else 80
            container_height = self.size.height if self.app else 40

            qr_content = self.query_one("#qr-content", Static)
            too_small_msg = self.query_one("#qr-too-small", Static)

            if self._compat:
                min_width = self.qr_size + 16
                min_height = self.qr_size // 2 + 11
            else:
                min_width = self.qr_size + 12
                min_height = self.qr_size // 2 + 9

            if container_width < min_width or container_height < min_height:
                qr_content.styles.display = "none"
                too_small_msg.styles.display = "block"
                too_small_msg.update(
                    f"窗口太小，请调整大小\n"
                    f"需要: {min_width}x{min_height}, "
                    f"当前: {container_width}x{container_height}"
                )
            else:
                too_small_msg.styles.display = "none"
                qr_content.styles.display = "block"

                qr_content.update(self.qr_text)

        except Exception as e:
            self.query_one("#qr-content", Static).update(f"[二维码生成失败: {e}]")

    def _generate_qr_data(self) -> None:
        try:
            matrix = build_qr_matrix(self.qr_url)
            self._qr_compat_lines = build_qr_lines(matrix, True)
            self._qr_modern_lines = build_qr_lines(matrix, False)

            if self._compat:
                self.qr_text = "\n".join(self._qr_compat_lines)
                self.qr_size = len(matrix) * 2
            else:
                self.qr_text = "\n".join(self._qr_modern_lines)
                self.qr_size = len(self._qr_modern_lines) * 2
        except Exception as e:
            self.qr_size = 0
            self.qr_text = f"[二维码生成失败: {e}]"

    def on_resize(self):
        """窗口大小改变时重新检查"""
        if self.qr_url:
            self._update_display()

    def action_quit_action(self):
        """退出窗口 - 用户主动关闭，返回False表示未登录成功"""
        self.dismiss(False)
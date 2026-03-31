"""高精度二维码显示组件

使用2x2字符格子表示二维码模块，提高扫描成功率。
显示在窗口顶部，支持登录和人脸识别两种场景。
"""

from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive
from textual.binding import Binding
import qrcode

from ...utils.constants import KeyBindings


class QRDisplayScreen(ModalScreen):
    """二维码显示面板"""

    BINDINGS = [
        Binding(KeyBindings.QUIT, "quit_action", "退出"),
    ]

    DEFAULT_CSS = """
    QRDisplayScreen {
        align: center middle;
        background: $surface 30%;
    }

    QRDisplayScreen #qr-card {
        width: 90%;
        height: 90%;
        padding: 0 2;
        background: $surface;
        border: thick $primary;
    }

    QRDisplayScreen #qr-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1;
        padding: 0;
    }

    QRDisplayScreen #qr-content {
        content-align: center middle;
        text-align: center;
        height: auto;
        width: 100%;
    }

    QRDisplayScreen #qr-too-small {
        text-align: center;
        color: $warning;
        text-style: bold;
        display: none;
    }
    """

    qr_url = reactive("")
    qr_text = reactive("")

    def __init__(self, qr_url: str, title: str = "扫码登录"):
        super().__init__()
        self.qr_url = qr_url
        self.title_text = title

    def compose(self):
        with Vertical(id="qr-card"):
            yield Static(self.title_text, id="qr-title")
            yield Static("", id="qr-content")
            yield Static("窗口太小，请放大后查看二维码", id="qr-too-small")

    def on_mount(self):
        """挂载时显示二维码"""
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

            min_width = self.qr_size + 11
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
        CHARS = {
            (False, False): " ",
            (True, False): "▀",
            (False, True): "▄",
            (True, True): "█",
        }
        qr_data = []
        try:
            qr = qrcode.QRCode(
                version=6,
                error_correction=1,
                box_size=1,
                border=0,
            )
            qr.add_data(self.qr_url)
            qr.make(fit=False)
            matrix = qr.get_matrix()
            size = len(matrix)
            for row in range(0, size, 2):
                qr_line = ""
                for line in range(size):
                    qr_line += CHARS[
                        (
                            matrix[row][line],
                            matrix[row + 1][line] if row + 1 < size else False,
                        )
                    ]
                qr_data.append(qr_line)
            self.qr_size = len(qr_data) * 2
            self.qr_text = "\n".join(qr_data)
        except Exception as e:
            self.qr_size = 0
            self.qr_text = f"[二维码生成失败]\n" + str(e) + "\n" + "\n".join(qr_data)

    def on_resize(self):
        """窗口大小改变时重新检查"""
        if self.qr_url:
            self._update_display()

    def action_quit_action(self):
        """退出窗口 - 用户主动关闭，返回False表示未登录成功"""
        self.dismiss(False)
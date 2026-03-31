"""帮助面板

显示使用帮助和快捷键信息。
"""

from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.app import ComposeResult


class HelpPanel(ScrollableContainer):
    """帮助面板 - 可滚动"""

    def compose(self) -> ComposeResult:
        with Vertical(classes="help-card"):
            yield Static("BiliLiveTool 帮助", classes="help-title")

            yield Static("快捷键", classes="section-title")
            with Horizontal(classes="key-row"):
                yield Static("Q / Esc", classes="key-name")
                yield Static("退出程序", classes="key-desc")

            yield Static("使用说明", classes="section-title")
            yield Static("1. 首次使用需扫描二维码登录", classes="help-text")
            yield Static("2. 登录后可设置直播标题和分区", classes="help-text")
            yield Static("3. 点击开播按钮开始直播", classes="help-text")
            yield Static("4. 直播前请先在OBS配置推流信息", classes="help-text")

            yield Static("版本信息", classes="section-title")
            yield Static("BiliLiveTool v0.4.1", classes="help-text")
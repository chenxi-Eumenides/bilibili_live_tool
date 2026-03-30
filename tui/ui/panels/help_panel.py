"""帮助面板

显示使用帮助和快捷键信息。
"""

from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.app import ComposeResult


class HelpPanel(ScrollableContainer):
    """帮助面板 - 可滚动"""

    DEFAULT_CSS = """
    HelpPanel {
        height: 100%;
        align: center middle;
    }
    HelpPanel .help-card {
        width: 70;
        height: auto;
        background: $surface-darken-1;
        border: solid $primary;
        padding: 2 3;
    }
    HelpPanel .help-title {
        text-align: center;
        text-style: bold;
        color: $text;
        margin-bottom: 2;
    }
    HelpPanel .section-title {
        color: $primary;
        text-style: bold;
        margin: 1 0;
        height: 1;
    }
    HelpPanel .key-row {
        layout: horizontal;
        height: auto;
        margin: 0 2;
    }
    HelpPanel .key-name {
        width: 15;
        color: $text;
        text-style: bold;
    }
    HelpPanel .key-desc {
        width: 1fr;
        color: $text-muted;
    }
    HelpPanel .help-text {
        color: $text-muted;
        margin: 0 2;
    }
    HelpPanel .button-row {
        height: auto;
        margin-top: 2;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="help-card"):
            yield Static("BiliLiveTool 帮助", classes="help-title")

            yield Static("快捷键", classes="section-title")
            with Horizontal(classes="key-row"):
                yield Static("Space", classes="key-name")
                yield Static("开播/下播切换", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("T", classes="key-name")
                yield Static("修改直播标题", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("A", classes="key-name")
                yield Static("修改直播分区", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("R", classes="key-name")
                yield Static("刷新状态", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("C", classes="key-name")
                yield Static("复制推流码", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("Shift+C", classes="key-name")
                yield Static("复制全部推流信息", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("Q / Esc", classes="key-name")
                yield Static("退出程序", classes="key-desc")
            with Horizontal(classes="key-row"):
                yield Static("Tab", classes="key-name")
                yield Static("切换焦点", classes="key-desc")

            yield Static("", classes="section-title")
            yield Static("使用说明", classes="section-title")
            yield Static("1. 首次使用需扫描二维码登录", classes="help-text")
            yield Static("2. 登录后可设置直播标题和分区", classes="help-text")
            yield Static("3. 点击开播按钮开始直播", classes="help-text")
            yield Static("4. 直播前请先在OBS配置推流信息", classes="help-text")

            yield Static("", classes="section-title")
            yield Static("版本信息", classes="section-title")
            yield Static("BiliLiveTool v0.4.0", classes="help-text")

            with Horizontal(classes="button-row"):
                yield Button("返回", id="btn-back", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击"""
        if event.button.id == "btn-back":
            self.app.show_info_panel()

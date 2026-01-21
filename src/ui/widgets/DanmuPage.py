from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Label, Static


class DanmuPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with Vertical(id="danmu-page-container"):
            yield Static("弹幕列表", id="danmu-title")
            yield Label("欢迎来到直播间！", id="danmu-1")
            yield Label("主播今天播什么？", id="danmu-2")
            yield Label("这个功能不错", id="danmu-3")
            yield Label("支持主播", id="danmu-4")
            yield Label("666", id="danmu-5")
            yield Label("关注了", id="danmu-6")
            yield Label("礼物走一波", id="danmu-7")
            yield Label("主播声音真好听", id="danmu-8")
            yield Label("明天还播吗？", id="danmu-9")
            yield Label("技术大佬", id="danmu-10")

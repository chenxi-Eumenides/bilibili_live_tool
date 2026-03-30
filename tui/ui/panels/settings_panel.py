"""设置面板

用于直播前的配置（标题和分区）。
"""

from textual.widgets import Static, Button, Input, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.app import ComposeResult

from textual.types import NoSelection

# 类型声明
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..app import BiliLiveApp

class SettingsPanel(Vertical):
    """设置面板"""
    @property
    def app(self) -> BiliLiveApp:
        return super().app # type: ignore

    def __init__(self):
        super().__init__()
        self._is_initializing = False  # 标记是否正在初始化

    def compose(self) -> ComposeResult:
        with Vertical(classes="settings-content"):
            # 居中的内容容器
            with ScrollableContainer(classes="settings-card"):
                yield Static("直播标题", classes="settings-label")
                yield Input(placeholder="输入直播标题", id="title-input")

                yield Static("选择分区", classes="settings-label")
                with Horizontal(classes="area-row"):
                    yield Select[int](
                        [],
                        id="parent-area-select",
                        prompt="主分区",
                        classes="area-select",
                    )
                    yield Select[int](
                        [],
                        id="child-area-select",
                        prompt="子分区",
                        disabled=True,
                        classes="area-select",
                    )

            # 固定在底部的按钮
            with Horizontal(classes="button-row"):
                yield Button("更新配置", id="btn-save", variant="primary")
                yield Button("取消", id="btn-cancel", variant="default")

    def on_mount(self):
        """组件挂载时加载数据"""
        self._load_data()

    def _load_data(self):
        """加载配置数据"""
        # 后台加载分区数据
        self.run_worker(self._load_areas_worker, thread=True)
        self._load_default_title()

    def _load_areas_worker(self):
        """后台加载分区列表"""
        try:
            app = self.app
            config_manager = app.config_manager

            # 获取分区列表（不保存，只在更新配置或退出时保存）
            if not config_manager.config.area_list:
                app.live_manager.fetch_area_list()

            # 在主线程更新UI
            self.app.call_from_thread(self._update_area_selects)
        except Exception:
            pass

    def _update_area_selects(self):
        """在主线程更新分区选择器"""
        try:
            area_list = self.app.config_manager.config.area_list

            if area_list:
                # 创建主分区选项
                options = [(area["name"], area["id"]) for area in area_list]
                parent_select = self.query_one("#parent-area-select", Select)
                parent_select.set_options(options)

                # 如果有默认分区，找到对应的主分区并选中
                default_area_id = self.app.config_manager.config.area_id
                default_parent_area_id = self.app.config_manager.get_parent_area_id(
                    default_area_id
                )

                self._is_initializing = True  # 标记开始初始化
                try:
                    if default_parent_area_id:
                        parent_select.value = default_parent_area_id
                        child_areas = self.app.config_manager.get_child_areas(
                            default_parent_area_id
                        )
                        self._load_child_areas(child_areas, default_area_id)
                    else:
                        # 没有默认分区，选中第一个主分区和子分区
                        child_areas = area_list[0]
                        parent_select.value = child_areas.get("id", 0)
                        self._load_child_areas(child_areas.get("list", []))
                finally:
                    self._is_initializing = False  # 重置初始化标记

        except Exception as e:
            pass

    def _load_child_areas(
        self, child_areas: list[dict[str, int | str]], default_child_id: int = 0
    ):
        """加载子分区列表"""
        try:
            child_select = self.query_one("#child-area-select", Select)

            if child_areas:
                # 准备选项
                options: list[tuple] = [(child["name"], child["id"]) for child in child_areas]

                # 如果没有指定或找不到，使用第一个
                if default_child_id == 0 and child_areas:
                    target_child_id = child_areas[0]["id"]
                else:
                    target_child_id = default_child_id

                child_select.disabled = True
                child_select.set_options(options)
                child_select.value = target_child_id
                child_select.disabled = False
            else:
                child_select.set_options([])
                child_select.disabled = True

        except Exception as e:
            pass

    def _load_default_title(self):
        """加载默认标题"""
        try:
            config = self.app.config_manager.get_config()
            if config.title:
                title_input = self.query_one("#title-input", Input)
                title_input.value = config.title
        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed):
        """处理选择器变化"""
        if event.select.id == "parent-area-select":
            parent_id = event.value
            if isinstance(parent_id, int) and parent_id:
                area = self.app.config_manager.get_child_areas(parent_id)
                self._load_child_areas(area)

    def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击"""
        btn_id = event.button.id

        if btn_id == "btn-save":
            self._save_config()
        elif btn_id == "btn-cancel":
            self._cancel()

    def _save_config(self):
        """更新配置"""
        title_input = self.query_one("#title-input", Input)
        child_select = self.query_one("#child-area-select", Select[int])

        title = title_input.value.strip()
        area_id = child_select.value

        if not title:
            self.app.show_notification("请输入直播标题")
            return

        if isinstance(area_id, NoSelection) or area_id == 0:
            self.app.show_notification("请选择直播分区")
            return

        # 获取当前配置
        config = self.app.config_manager.get_config()

        # 调用update_room更新直播间信息
        success, message = self.app.live_manager.update_room(
            title=title if title != config.title else config.title,
            area_id=area_id if area_id != config.area_id else config.area_id,
        )

        if success:
            # 更新本地配置
            config.title = title
            config.area_id = area_id
            self.app.config_manager.save()
            # 刷新直播间信息（第3个获取时机：更新配置后）
            self.app.live_manager.fetch_room_info()
            self.app.show_notification("配置已更新")
        else:
            self.app.show_notification(f"更新失败: {message}")
        # 不自动跳转，留在管理页面

    def _cancel(self):
        """取消 - 重置为config中的数据"""
        self._load_data()
        # 返回信息页面
        self.app.show_info_panel()

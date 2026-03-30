"""分区选择器组件

提供分级分区选择功能。
"""

from textual.widgets import Static, Select, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from typing import Optional, List, Tuple


class AreaSelector(Vertical):
    """分区选择器组件"""

    DEFAULT_CSS = """
    AreaSelector {
        height: auto;
        padding: 1;
    }
    AreaSelector .area-level {
        margin: 1 0;
    }
    AreaSelector .area-label {
        color: $text-muted;
        margin-bottom: 1;
    }
    AreaSelector .button-row {
        margin-top: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self._area_list = []
        self._selected_parent_id = 0
        self._selected_area_id = 0

    def compose(self) -> ComposeResult:
        """组合组件"""
        # 主分区选择
        with Vertical(classes="area-level"):
            yield Static("选择主分区:", classes="area-label")
            yield Select([("请选择", 0)], id="parent-area-select")

        # 子分区选择
        with Vertical(classes="area-level"):
            yield Static("选择子分区:", classes="area-label")
            yield Select([("请先选择主分区", 0)], id="sub-area-select")

        # 按钮行
        with Horizontal(classes="button-row"):
            yield Button("确认", id="btn-confirm-area", variant="primary")
            yield Button("取消", id="btn-cancel-area", variant="default")

    def on_mount(self):
        """组件挂载时加载分区数据"""
        self._load_area_data()

    def _load_area_data(self):
        """加载分区数据"""
        try:
            app = self.app
            config = app.config_manager.get_config()
            
            if not config.area_list:
                # 如果没有分区数据，尝试获取
                app.live_manager.fetch_area_list()
                config = app.config_manager.get_config()

            self._area_list = config.area_list or []
            self._update_parent_area_options()

        except Exception as e:
            self.query_one("#parent-area-select", Select).set_options([(f"加载失败: {e}", 0)])

    def _update_parent_area_options(self):
        """更新主分区选项"""
        parent_select = self.query_one("#parent-area-select", Select)
        
        if not self._area_list:
            parent_select.set_options([("无分区数据", 0)])
            return

        options = [("请选择", 0)]
        for area in self._area_list:
            options.append((area.name, area.id))

        parent_select.set_options(options)

        # 如果有当前选中的分区，尝试选中它
        config = self.app.config_manager.get_config()
        if config.area_id:
            self._try_select_area(config.area_id)

    def _update_sub_area_options(self, parent_id: int):
        """更新子分区选项"""
        sub_select = self.query_one("#sub-area-select", Select)
        
        # 查找选中的主分区
        parent_area = None
        for area in self._area_list:
            if area.id == parent_id:
                parent_area = area
                break

        if not parent_area or not parent_area.children:
            sub_select.set_options([("无子分区", 0)])
            sub_select.disabled = True
            return

        options = [("请选择", 0)]
        for child in parent_area.children:
            options.append((child.name, child.id))

        sub_select.set_options(options)
        sub_select.disabled = False

    def _try_select_area(self, area_id: int):
        """尝试选中指定的分区"""
        # 查找分区
        target_area = None
        parent_area = None
        
        for area in self._area_list:
            if area.id == area_id:
                target_area = area
                parent_area = area
                break
            for child in area.children:
                if child.id == area_id:
                    target_area = child
                    parent_area = area
                    break
            if target_area:
                break

        if parent_area and target_area:
            # 选中主分区
            parent_select = self.query_one("#parent-area-select", Select)
            parent_select.value = parent_area.id
            
            # 更新子分区选项
            self._update_sub_area_options(parent_area.id)
            
            # 选中子分区
            if target_area != parent_area:
                sub_select = self.query_one("#sub-area-select", Select)
                sub_select.value = target_area.id

    def on_select_changed(self, event: Select.Changed):
        """处理选择变化"""
        if event.select.id == "parent-area-select":
            parent_id = event.select.value or 0
            self._selected_parent_id = parent_id
            self._update_sub_area_options(parent_id)
            
            # 如果选择了主分区但没有子分区，直接选中主分区
            if parent_id > 0:
                parent_area = None
                for area in self._area_list:
                    if area.id == parent_id:
                        parent_area = area
                        break
                
                if parent_area and not parent_area.children:
                    self._selected_area_id = parent_id

        elif event.select.id == "sub-area-select":
            sub_id = event.select.value or 0
            if sub_id > 0:
                self._selected_area_id = sub_id

    def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击"""
        if event.button.id == "btn-confirm-area":
            self._confirm_selection()
        elif event.button.id == "btn-cancel-area":
            self._cancel_selection()

    def _confirm_selection(self):
        """确认选择"""
        if self._selected_area_id <= 0:
            self.app.notify("请选择分区", severity="error")
            return

        # 调用应用的回调
        if hasattr(self.app, "on_update_area"):
            self.app.on_update_area(self._selected_area_id)
        
        # 返回主面板
        self.app.app_state = self.app.app_state.IDLE

    def _cancel_selection(self):
        """取消选择"""
        # 返回主面板
        self.app.app_state = self.app.app_state.IDLE
# TUI 层开发规格书

> **开发分支**: `feat/tui`
> **合并目标**: `dev`
> **状态**: 🔶 开发中

## 一、整体架构

### 1.1 TUI 层在项目中的位置

```
入口分发 (src/BiliLiveTool.py)
├── CLI 模式 (src/cli/)       ✅ 已完成
└── TUI 模式 (src/tui/)       🔶 开发中
    ├── app.py                — Textual App 入口
    ├── main.py               — CLI 入口 (FLAGS/run/help_lines)
    ├── screens/              — 屏幕层
    │   ├── main.py/.tcss     — 主屏幕
    │   └── quit.py/.tcss     — 退出确认
    └── widgets/              — 组件层
        ├── left_panel.py     — 左侧导航
        ├── login.py          — 登录页面
        ├── live.py           — 直播操作
        ├── info.py           — 信息展示
        └── danmaku.py        — 弹幕显示
```

### 1.2 TUI 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    BiliLiveToolApp                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Header                                              │ │
│  ├──────────┬──────────────────────────────────────────┤ │
│  │LeftPanel │     ContentSwitcher                      │ │
│  │ (导航)   │  ┌────────────────────────────────────┐  │ │
│  │          │  │ LoginPage (登录：扫码+状态显示)     │  │ │
│  │ [登录]   │  │ ActionPage (直播：开播/停播/修改)  │  │ │
│  │ [操作]   │  │ InfoPage (信息：账户+直播状态)     │  │ │
│  │ [信息]   │  │ DanmuPage (弹幕：监听+显示)        │  │ │
│  │ [弹幕]   │  └────────────────────────────────────┘  │ │
│  └──────────┴──────────────────────────────────────────┤ │
│  Footer                                                │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │  QuitScreen (弹出层 — 退出确认对话框)              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 1.3 设计原则

1. **事件驱动**：TUI 通过 `session.on(SessionEvent.XXX, callback)` 订阅逻辑层事件，逻辑层通过 `session._emit()` 触发事件
2. **按需加载**：每个 Widget 在 `on_mount` 中订阅所需事件
3. **无直接 API 调用**：Widget 不 import `src/utils/api.py`，只通过 `src/logic/` 函数操作
4. **样式分离**：Python 定义结构与行为，`.tcss` 定义样式
5. **黑色主题**：以 `#09090b` (最深背景) 和 `#18181b` (二级背景) 为主

## 二、开发规范

### 2.1 代码规范

- **导入原则**：`from xxx import a, b`，不用 `import xxx`。相对导入项目内模块（`from ..logic import Session`）
- **常量管理**：所有可复用常量放 `src/utils/constant.py` 对应类中，模块私有常量留在模块内
- **文档格式**：统一使用 Google Style docstring
- **类型注解**：所有函数参数和返回值必须标注类型
- **ruff 检查**：代码通过 `ruff F401`（无未使用导入）

### 2.2 文件组织

| 类别 | 存放路径 | 说明 |
|------|---------|------|
| TUI 常量 | `src/utils/constant.py` → `TUIColors` | 颜色、样式常量 |
| 弹幕颜色 | `src/utils/constant.py` → `DanmakuColors` | 弹幕颜色（保持不变） |
| 快捷键 | `src/utils/constant.py` → `KeyBindings` | 键盘绑定定义 |
| 工具函数 | `src/utils/lib.py` | 纯函数，TUI可能需要的渲染工具 |
| 参数对象 | `src/utils/data.py` | TUI使用的数据结构 |
| Widget | `src/tui/widgets/*.py` | 组件实现 |
| Screen | `src/tui/screens/*.py` | 屏幕实现 |
| 样式 | `src/tui/screens/*.tcss` | CSS 样式 |

### 2.3 样式规范

- **边框/边距**：只在需要的地方设置 `padding` 和 `margin`，不过度使用
- **颜色系统**：使用 `TUIColors` 中定义的变量，通过 `$accent` 等 CSS 变量引用
- **黑色主题**：`background: $surface` → `#18181b`，`background: $panel` → `#27272a`
- **弹幕颜色**：使用 `DanmakuColors`，不得修改已有定义

### 2.4 分支策略

```
dev ──→ feat/tui ──→ dev (合并后删除 feat/tui)
```

开发在 `feat/tui` 分支进行，完成后 PR 合并到 `dev`。

## 三、模块设计

### 3.1 新增大数据量常量

需要在 `src/utils/constant.py` 新增：

```python
class TUIColors:
    """UI样式常量 - 深色主题"""
    
    ACCENT_COLOR = "#06b6d4"       # 青色强调
    SUCCESS_COLOR = "#22c55e"      # 成功绿
    WARNING_COLOR = "#f59e0b"      # 警告黄
    ERROR_COLOR = "#ef4444"        # 错误红
    TEXT_PRIMARY = "#ffffff"       # 主文字
    TEXT_SECONDARY = "#a1a1aa"     # 次文字
    TEXT_MUTED = "#71717a"         # 辅助文字
    BG_PRIMARY = "#09090b"         # 最深背景
    BG_SECONDARY = "#18181b"       # 二级背景
    BG_TERTIARY = "#27272a"        # 三级背景
    BORDER_COLOR = "#3f3f46"       # 边框
```

> 注意：`TUIColors` 已在 `constant.py` 中定义为示例，需确认是否完整可用。

### 3.2 App 层 (`src/tui/app.py`)

**BiliLiveToolApp**：
- 继承 `textual.app.App`
- 管理全局 `Session` 实例
- 注册屏幕：`SCREENS = {"main": MainScreen}`
- `on_mount()` 推入 main 屏幕
- CSS 路径指向 `app.tcss`

**变更**：
- `run_tui()` 函数保持不变（被 `main.py` 的 `run()` 调用）
- 添加全局 CSS 变量定义（颜色 token）

### 3.3 入口层 (`src/tui/main.py`)

**当前状态**：`run()` 是占位（打印 "TUI 模式尚未实现"）

**变更**：
```python
FLAGS = frozenset({"--tui"})

def run():
    from .app import run_tui
    run_tui()
```

### 3.4 主屏幕 (`src/tui/screens/main.py` + `main.tcss`)

**MainScreen**：
- 横向布局：`Header` + `Horizontal(LeftPanel + ContentSwitcher)` + `Footer`
- ContentSwitcher 管理 4 个页面切换
- 键盘绑定：`q/escape` 退出，`space` 确认
- 页面导航栈 `current_page`

**当前状态**：基本完成

**变更**：
- 优化 `Footer` 显示当前登录状态（可选）
- 完善 CSS 样式（深色主题）

### 3.5 退出屏幕 (`src/tui/screens/quit.py` + `quit.tcss`)

**QuitScreen**：
- Grid 布局对话框
- 键盘/按钮双重确认
- `current_choice` 状态跟踪

**当前状态**：基本完成

**变更**：CSS 风格适配黑色主题

### 3.6 左侧导航 (`src/tui/widgets/left_panel.py`)

**LeftPanel**：
- 垂直排列 4 个导航按钮（登录/操作/信息/弹幕）
- 所有按钮 `classes="can-enter"`
- 根据登录状态动态启用/禁用按钮

**当前状态**：基本完成

**变更**：
- 订阅 `AUTH_LOGIN_SUCCESS` / `AUTH_LOGOUT_DONE` 事件，登录后显示用户名
- 登录后禁用"登录"按钮或将其改为"已登录（用户名）"

### 3.7 登录页面 (`src/tui/widgets/login.py`)

**LoginPage**：
- 扫码登录流程：获取二维码 → 显示二维码 → 轮询登录状态 → 回调结果
- 状态显示：获取中/待扫码/已扫码/已过期/登录成功

**当前状态**：基本完成

**问题与变更**：
1. **二维码显示**：当前用 `generate_qr_text()` 生成文本二维码并显示在 Label 中，可以工作
2. **轮询超时**：90 次 × 2 秒 = 180 秒，符合 `Tuning.LOGIN_POLL_TIMEOUT`
3. **状态反馈**：登录成功后应保存 config 并 emit 事件 → `session.config.save_config()`
4. **登录后**：禁用登录按钮，显示登录成功信息
5. **错误处理**：捕获可能的 `FuncResult` FAIL 状态

### 3.8 直播操作页面 (`src/tui/widgets/live.py`)

**ActionPage**：
- 开始直播 / 结束直播 / 修改标题 / 修改分区 / 刷新信息

**当前状态**：部分完成

**变更**：
1. **开始直播**：需要前置校验（已登录、有分区）、显示推流码（如果有）
2. **结束直播**：需要确认对话框
3. **修改标题**：需实现 Textual `Input` 弹出框，调用 `live_update_room(session, title=...)`
4. **修改分区**：新增，需实现分区选择器
5. **分区选择器**：显示分区列表（主分区→子分区），支持键盘选择
6. **刷新信息**：调用 `live_refresh_room_info` 后更新 InfoPage

**按钮状态管理**：
- 未登录 → 全部禁用
- 未开播 → 只启用"开始直播"
- 直播中 → 启用"结束直播"/"修改标题"/"修改分区"/"刷新"

### 3.9 信息展示页面 (`src/tui/widgets/info.py`)

**InfoPage**：
- 账户信息：名称、UID
- 直播间信息：房间号、标题、分区、观众数
- 直播状态：状态、开播时间、直播时长

**当前状态**：部分完成，动态更新逻辑不完整

**变更**：
1. 显示账户名称（需从 Session 获取）
2. 显示完整的 `room_data` 字段（观众数、开播时间、直播时长、分区名等）
3. 订阅 `AUTH_LOGIN_SUCCESS` / `AUTH_LOGOUT_DONE` 更新账户信息
4. `_on_info_updated` 从 `session.config.room_data` 读取完整数据
5. `_on_state_changed` 更新状态为 `"直播中"` / `"未开播"` / `"轮播中"`

### 3.10 弹幕页面 (`src/tui/widgets/danmaku.py`)

**DanmuPage**：
- 开始监听 / 停止监听按钮
- 状态显示
- 弹幕列表（滚动显示），使用 Rich markup 渲染

**当前状态**：部分完成——事件订阅已连接，但按钮未绑定到方法

**变更**：
1. **连接按钮**：绑定 `#danmaku-start` → `_start_listening()`，`#danmaku-stop` → `_stop_listening()`
2. **弹幕显示**：使用 `msg.format_rich()` 生成 Rich markup 文本，渲染到 Label
3. **滚动列表**：使用 RichLog 或 ScrollView 容器，限制最大条目数（如 500 条）
4. **颜色保持**：不修改 `DanmakuColors` 中任何弹幕颜色定义
5. **登录状态**：订阅 `AUTH_LOGIN_SUCCESS` / `AUTH_LOGOUT_DONE` 事件
6. **按钮状态**：
   - 未登录 → 全部禁用
   - 已登录 → 启用"开始监听"
   - 监听中 → 启用"停止监听"，禁用"开始监听"

**弹幕渲染**：
- `DanmakuMessage.format_rich()` 返回 Rich markup 字符串
- 可直接在支持 Rich markup 的 Widget 中显示
- 如果使用 RichLog，直接 `write(rich_text)`

### 3.11 全局样式 (`src/tui/app.tcss`)

需要定义 CSS 变量（使用 Textual 的 CSS 变量系统）：

```tcss
* {
    /* 背景色 */
    $surface: #18181b;
    $surface-darken-1: #09090b;
    $surface-darken-2: #0f0f12;
    $surface-lighten-1: #27272a;
    
    /* 强调色 */
    $accent: #06b6d4;
    $accent-darken-1: #0891b2;
    
    /* 文字色 */
    $text: #ffffff;
    $text-muted: #71717a;
    
    /* 状态色 */
    $success: #22c55e;
    $warning: #f59e0b;
    $error: #ef4444;
    
    /* 边框 */
    $border: #3f3f46;
}

Screen {
    background: $surface-darken-1;
    color: $text;
}
```

## 四、开发顺序

**核心原则**：每个功能在独立分支上开发，严格遵循「分支→开发→测试→合并」循环。不允许一次性开发多个小功能或整个阶段。

### 功能分支列表

优先级按依赖关系排列，数字越小越先开发。

| 序号 | 分支名 | 功能描述 | 涉及文件 | 依赖 |
|------|--------|---------|---------|------|
| F01 | `feat/tui-entry` | 修复 `main.py` 的 `run()` 调用 `app.run_tui()`，更新 `help_lines()` 文本 | `src/tui/main.py` | 无 |
| F02 | `feat/tui-styles` | 完善全局样式：`app.tcss` + `main.tcss` + `quit.tcss` 深色主题 CSS 变量 | `src/tui/app.tcss`, `screens/main.tcss`, `screens/quit.tcss` | F01 |
| F03 | `feat/tui-info-page` | InfoPage 动态更新：完善 `_on_info_updated` 和 `_on_state_changed` | `src/tui/widgets/info.py` | F01 |
| F04 | `feat/tui-left-panel` | LeftPanel 登录状态感知：订阅 AUTH 事件，动态显示用户状态 | `src/tui/widgets/left_panel.py` | F01 |
| F05 | `feat/tui-login-page` | LoginPage 完善：登录成功后保存 config + 状态反馈 + 错误处理 | `src/tui/widgets/login.py` | F01 |
| F06 | `feat/tui-live-buttons` | ActionPage 按钮状态管理：登录/开播状态感知，前置校验，结果展示 | `src/tui/widgets/live.py` | F01 |
| F07 | `feat/tui-live-title` | 修改标题功能：InputModal 弹窗 → 调用 `live_update_room` | `src/tui/widgets/live.py`, 新增 `screens/input_modal.py` | F06 |
| F08 | `feat/tui-live-area` | 分区选择器：显示分区列表 → 选择主/子分区 | `src/tui/widgets/live.py`, 新增 `screens/area_picker.py` | F06 |
| F09 | `feat/tui-danmaku-bind` | 弹幕按钮绑定：开始/停止监听连接按钮，按钮状态管理 | `src/tui/widgets/danmaku.py` | F01 |
| F10 | `feat/tui-danmaku-render` | 弹幕渲染：使用 RichLog 滚动显示 `format_rich()` + 500 条上限 | `src/tui/widgets/danmaku.py` | F09 |

### 工作流规范

每个功能分支执行以下循环：

```
1. git checkout dev && git pull
2. git checkout -b feat/tui-xxx
3. 开发 + 修改代码
4. ruff check src/   (代码风格检查)
5. git commit
6. git checkout dev && git merge feat/tui-xxx
7. git branch -d feat/tui-xxx
```

> **测试说明**：现有单元测试仅覆盖 logic 层，不含 TUI 测试，故不运行 `python -m unittest`。
> 代码验证仅依赖 `ruff check` + LSP 诊断。
> 如需判断 TUI 截图，委托 `unspecified-low` 子 agent 进行图片识别。

## 五、关键技术方案

### 5.1 二维码渲染

使用项目中已有的 `src/utils/lib.py:generate_qr_text()` 函数，返回 Unicode 双色方块构成的文本二维码。可直接显示在 `Label` 或 `Static` 组件中。

### 5.2 输入弹窗

修改标题/分区使用 Textual 的 `Input` 组件。有两种实现方式：
- **方式 A**：弹出 `ModalScreen` 包含 `Input` 组件（推荐，用户体验好）
- **方式 B**：在页面内嵌入 `Input` 组件（简单但不如弹窗直观）

推荐方式 A——创建通用的 `InputModal` Screen，支持输入文本和标题/提示。

### 5.3 分区选择器

显示分区列表（主分区→子分区的树形结构）：
1. 调用 `live_get_area_list(session)` 获取分区列表
2. 在 `ListView` 或自定义组件中显示
3. 用户选择后，将 area_id 传递给 `live_start` 或 `live_update_room`

### 5.4 弹幕显示

- 使用 `RichLog` 组件显示弹幕（支持 Rich markup、自动滚动、最大行数限制）
- 从 `DanmakuMessage.format_rich()` 获取 Rich markup 文本
- `RichLog.write(rich_text)` 追加弹幕
- 限制最大行数为 500 条

### 5.5 事件驱动更新

每个 Widget 在 `on_mount` 中订阅相关事件：

| Widget | 订阅事件 | 触发行为 |
|--------|---------|---------|
| LeftPanel | AUTH_LOGIN_SUCCESS, AUTH_LOGOUT_DONE | 更新登录状态显示 |
| InfoPage | LIVE_INFO_UPDATED, LIVE_STATE_CHANGED, AUTH_LOGIN_SUCCESS, AUTH_LOGOUT_DONE | 更新信息显示 |
| ActionPage | LIVE_STATE_CHANGED, LIVE_INFO_UPDATED | 更新按钮状态 |
| DanmuPage | DANMAKU_RECEIVED, DANMAKU_STOPPED, AUTH_LOGIN_SUCCESS | 显示弹幕、更新状态 |

### 5.6 按钮状态管理

通过订阅事件动态更新按钮状态：

```python
def _update_button_states(self):
    session = self.app.session
    is_logged_in = session.is_logged_in
    is_live = session.config.room_data.get("live_status") == 1
    
    self.query_one("#start-live", Button).disabled = not is_logged_in or is_live
    self.query_one("#stop-live", Button).disabled = not is_logged_in or not is_live
    self.query_one("#update-title", Button).disabled = not is_logged_in
    # ...
```

## 六、文件结构总览

```
src/tui/
├── __init__.py                 # 导出 FLAGS, run, help_lines
├── app.py                      # BiliLiveToolApp, run_tui()
├── app.tcss                    # 全局 CSS 变量与样式
├── main.py                     # TUI CLI 入口 (FLAGS/run/help_lines)
├── screens/
│   ├── __init__.py
│   ├── main.py                 # MainScreen — 主界面
│   ├── main.tcss               # 主界面样式
│   ├── quit.py                 # QuitScreen — 退出确认
│   └── quit.tcss               # 退出对话框样式
└── widgets/
    ├── __init__.py
    ├── left_panel.py           # LeftPanel — 左侧导航
    ├── login.py                # LoginPage — 扫码登录
    ├── live.py                 # ActionPage — 直播操作
    ├── info.py                 # InfoPage — 信息展示
    └── danmaku.py              # DanmuPage — 弹幕显示
```

## 七、状态追踪

| 序号 | 分支 | 描述 | 状态 |
|------|------|------|------|
| F01 | `feat/tui-entry` | 修复 run() 函数 | ✅ 已完成 |
| F02 | `feat/tui-styles` | 全局 + 屏幕深色主题样式 | ✅ 已完成 |
| F03 | `feat/tui-info-page` | InfoPage 动态更新 | ✅ 已完成 |
| F04 | `feat/tui-left-panel` | LeftPanel 登录状态感知 | ✅ 已完成 |
| F05 | `feat/tui-login-page` | LoginPage 完善 | ✅ 已完成 |
| F06 | `feat/tui-live-buttons` | ActionPage 按钮状态管理 | ✅ 已完成 |
| F07 | `feat/tui-live-title` | 修改标题 InputModal | ✅ 已完成 |
| F08 | `feat/tui-live-area` | 分区选择器 | ✅ 已完成 |
| F09 | `feat/tui-danmaku-bind` | 弹幕按钮绑定 | ✅ 已完成 |
| F10 | `feat/tui-danmaku-render` | 弹幕 RichLog 渲染 | ✅ 已完成 |

## 八、参考

- `plan/logic-layer-design-spec.md` — 逻辑层设计文档
- 旧版 UI 代码 `src/ui/` — 可参考的旧版 Textual 实现
- `tui` 分支 — TUI 早期版本的完整实现（架构不同，不直接复用）

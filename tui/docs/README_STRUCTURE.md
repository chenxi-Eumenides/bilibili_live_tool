# TUI 代码结构说明

## 项目概述

这是一个基于 [Textual](https://textual.textualize.io/) 框架开发的B站直播工具终端用户界面(TUI)版本。
当前版本: v0.4.1

---

## 目录结构

```
tui/
├── __init__.py                 # 包入口，定义版本信息（必需）
│
├── app/                        # 应用入口层
│   ├── __init__.py             # 导出main入口（必需，简化外部导入）
│   └── main.py                 # 命令行入口，配置日志并启动应用
│
├── core/                       # 核心业务逻辑层
│   ├── __init__.py             # 导出核心管理器类（必需，聚合Auth/Live/Config）
│   ├── auth.py                 # 登录管理（二维码登录、扫码状态轮询）
│   ├── config.py               # 配置管理（Config数据类/ConfigManager持久化）
│   ├── live.py                 # 直播操作（开播/下播/信息获取/分区列表）
│   └── stream.py               # 推流码管理（StreamInfo数据展示）
│
├── ui/                         # 用户界面层
│   ├── __init__.py             # UI包入口（必需，标识为包）
│   ├── app.py                  # 主应用类 BiliLiveApp（全局状态管理）
│   │
│   ├── layout/                 # 布局组件
│   │   ├── __init__.py         # 布局包入口（必需）
│   │   ├── header.py           # 顶部标题栏（状态指示/更新状态）
│   │   ├── sidebar.py          # 左侧导航栏（导航按钮/状态响应）
│   │   ├── main_panel.py       # 中央内容区容器（动态切换面板）
│   │   └── status_bar.py       # 底部状态栏（快捷键提示）
│   │
│   ├── panels/                 # 功能面板
│   │   ├── __init__.py         # 导出面板类（必需）
│   │   ├── auth_panel.py       # 登录面板（二维码显示/登录流程）
│   │   ├── dashboard_panel.py  # 控制台面板（直播间信息/时长计时）
│   │   ├── settings_panel.py   # 设置面板（标题/分区配置）
│   │   ├── stream_panel.py     # 推流面板（推流码显示/OBS配置）
│   │   └── help_panel.py       # 帮助面板（快捷键/使用说明）
│   │
│   ├── screen/                 # 屏幕层（弹窗/全屏）
│   │   └── QRDisplayScreen.py  # 二维码显示屏幕（登录/人脸验证弹窗）
│   │
│   ├── widgets/                # 可复用小组件
│   │   ├── __init__.py         # 组件包入口（必需）
│   │   └── area_selector.py    # 分区选择器组件（主分区+子分区联动）
│   │
│   └── styles/                 # TCSS样式文件
│       ├── global.tcss         # 全局样式（组件基础样式/颜色变量）
│       ├── layout.tcss         # 布局组件样式（Header/Sidebar等）
│       ├── auth_panel.tcss     # 登录面板样式
│       ├── dashboard_panel.tcss # 信息面板样式
│       ├── settings_panel.tcss # 设置面板样式
│       ├── help_panel.tcss     # 帮助面板样式
│       └── stream_panel.tcss   # 推流面板样式
│
├── utils/                      # 工具模块
│   ├── __init__.py             # 工具包入口（必需，标识为包）
│   └── constants.py            # 常量定义（版本/API/状态/快捷键/样式）
│
└── docs/                       # 文档目录
    └── README_STRUCTURE.md     # 本文件（代码结构说明）
```

---

## 架构设计

### 1. 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer (ui/)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Layout     │  │   Panels     │  │   Widgets    │       │
│  │  (布局组件)   │  │  (功能面板)   │  │  (可复用组件) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     App Layer (app/app.py)                   │
│                 BiliLiveApp - 全局状态管理                    │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer (core/)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ AuthManager  │  │ LiveManager  │  │StreamManager │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐                                           │
│  │ConfigManager │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│              (Bilibili API / File System)                    │
└─────────────────────────────────────────────────────────────┘
```

### 2. 状态管理

应用使用 **3种全局状态** 驱动UI：

| 状态 | 枚举值 | 描述 |
|------|--------|------|
| UNAUTH | `AppState.UNAUTH` | 未登录状态，显示登录面板 |
| IDLE | `AppState.IDLE` | 已登录未开播，显示控制台面板 |
| LIVE | `AppState.LIVE` | 直播中，显示推流面板 |

### 3. 响应式数据流

```python
# BiliLiveApp中的响应式属性
app_state = reactive(AppState.UNAUTH)               # 全局状态
status_message = reactive("")                        # 状态消息
is_loading = reactive(False)                         # 加载状态
current_panel = reactive("info")                     # 当前面板

# 状态变化时自动触发watch方法
watch_app_state(state)        # 更新UI布局
watch_current_panel(panel)    # 切换面板内容
watch_status_message(message) # 显示通知
```

---

## 核心模块详解

### 1. app/main.py - 入口模块

**职责**: 命令行入口，配置日志，启动应用

```python
def setup_logging():
    """配置日志，仅写入文件不输出到控制台"""
    
def main():
    """应用入口，创建并运行BiliLiveApp"""
```

**关键点**: 日志仅写入文件，避免干扰TUI界面

### 2. core/auth.py - 登录管理

**类**: `AuthManager`

| 方法 | 功能 |
|------|------|
| `generate_qr()` | 生成二维码，保存为qr.jpg |
| `poll_login_status(qr_key)` | 轮询登录状态 |
| `login_with_qr(callback)` | 完整的登录流程 |
| `check_auth()` | 验证登录状态是否有效 |

**状态流转**:
```
PENDING(等待扫码) → SCANNED(已扫描) → SUCCESS(登录成功)
                          ↓
                    EXPIRED(二维码过期)
```

### 3. core/config.py - 配置管理

**数据类**: `Config`
- 存储用户信息、直播间配置、推流信息
- 支持v1/v2两种配置格式
- 提供配置有效性验证

**类**: `ConfigManager`
- 配置文件读写（config.json）
- 配置持久化
- 分区名称查询

### 4. core/live.py - 直播管理

**类**: `LiveManager`

| 方法 | 功能 |
|------|------|
| `fetch_room_id(uid)` | 根据UID获取房间ID |
| `fetch_room_info()` | 获取直播间详细信息 |
| `start_live()` | 开播操作（含人脸识别流程） |
| `stop_live()` | 下播操作 |
| `fetch_area_list()` | 获取分区列表 |
| `update_room_title()` | 修改直播间标题 |
| `update_room_area()` | 修改直播间分区 |
| `check_face_auth()` | 检查人脸识别状态 |

### 5. core/stream.py - 推流管理

**数据类**: `StreamInfo`
- rtmp_addr: 推流地址
- rtmp_code: 推流码
- full_url: 完整推流URL

**类**: `StreamManager`
- 推流信息获取与展示
- OBS配置指南生成

---

## UI模块详解

### 1. BiliLiveApp (ui/app.py)

**Textual App主类**，全局状态管理中心。

**CSS加载顺序**:
```python
CSS_PATH = [
    "styles/global.tcss",         # 1. 全局基础样式
    "styles/layout.tcss",         # 2. 布局组件样式
    "styles/auth_panel.tcss",     # 3. 登录面板样式
    "styles/dashboard_panel.tcss",# 4. 控制台面板样式
    "styles/settings_panel.tcss", # 5. 设置面板样式
    "styles/help_panel.tcss",     # 6. 帮助面板样式
    "styles/stream_panel.tcss",   # 7. 推流面板样式
]
```

**快捷键绑定**:
- `q/esc`: 退出应用

### 2. Screen组件

#### QRDisplayScreen (screen/QRDisplayScreen.py)
- 二维码显示弹窗
- 支持登录二维码和人脸识别二维码
- 提供关闭回调机制

### 3. Layout组件

#### Header (layout/header.py)
- 显示应用名称和版本
- 状态指示器（未登录/已登录/直播中）
- 数据更新状态显示

#### Sidebar (layout/sidebar.py)
- 导航按钮：信息、管理、开播/下播、帮助
- 根据状态动态更新按钮样式

#### MainPanel (layout/main_panel.py)
- 中央内容容器
- 根据 `app_state` 和 `current_panel` 动态切换面板

#### StatusBar (layout/status_bar.py)
- 底部快捷键提示
- 简化设计，只显示退出提示

### 4. Panel组件

#### AuthPanel (panels/auth_panel.py)
- 二维码登录界面
- 使用后台Worker处理登录流程
- 显示ASCII二维码和登录状态

#### DashboardPanel (panels/dashboard_panel.py)
- 直播间信息展示
- 显示：标题、主播UID、房间号、分区、在线人数、粉丝数、直播时长
- 直播时长格式：HH:MM:SS（如 02:30:45）
- 后台自动刷新数据（5分钟间隔）
- 开播后自动启动时长计时器

#### SettingsPanel (panels/settings_panel.py)
- 直播配置：标题输入框
- 分区选择：主分区+子分区二级联动
- 保存/取消按钮

#### StreamPanel (panels/stream_panel.py)
- 推流地址和推流码显示
- 一键复制功能（使用pyperclip）
- OBS配置指南
- 下播按钮

#### HelpPanel (panels/help_panel.py)
- 快捷键说明
- 使用说明
- 版本信息

### 5. Widget组件

#### AreaSelector (widgets/area_selector.py)
- 分区选择器
- 主分区+子分区二级联动
- 支持搜索和快速选择

---

## 样式系统

### 颜色规范

| 用途 | 颜色值 | 变量名 |
|------|--------|--------|
| B站蓝（主色） | `#00a1d6` | `$primary` |
| 成功绿 | `#52c41a` | `$success` |
| 警告黄 | `#faad14` | `$warning` |
| 错误红 | `#f5222d` | `$error` |
| 主要文字 | `#e5e5e5` | `$text` |
| 次要文字 | `#999999` | `$text-muted` |
| 深色背景 | `#1a1a1a` | - |
| 卡片背景 | `#2a2a2a` | `$surface-darken-1` |
| 边框颜色 | `#3a3a3a` | - |

### 组件样式类

- `.nav-button`: 导航按钮
- `.info-card`: 信息卡片容器
- `.info-label`: 信息标签
- `.info-value`: 信息值
- `.settings-card`: 设置卡片
- `.stream-card`: 推流信息卡片
- `.help-card`: 帮助卡片
- `.status-online/offline/live`: 状态指示

---

## 数据流说明

### 开播流程

```
用户点击开播
    ↓
BiliLiveApp._start_live()
    ↓
LiveManager.start_live()
    ↓
是否需要人脸验证?
    ├─ 是 → 显示QRDisplayScreen → 轮询check_face_auth → 成功后重试开播
    └─ 否 → 开播成功
        ↓
刷新直播间信息 fetch_room_info()
更新配置中的live_status
更新UI状态 app_state = AppState.LIVE
DashboardPanel启动时长计时器
```

### 登录流程

```
用户点击登录
    ↓
AuthPanel._login_worker() (后台线程)
    ↓
AuthManager.generate_qr() → 获取qr_url
    ↓
显示QRDisplayScreen
    ↓
轮询AuthManager.poll_login_status()
    ↓
登录成功 → 保存cookies → 获取房间信息 → 更新UI状态
```

---

## 开发规范

### 1. 添加新面板

1. 在 `ui/panels/` 创建新文件
2. 继承 ` textual.containers.Vertical/Horizontal/Grid`
3. 实现 `compose()` 方法定义UI结构
4. 在 `ui/panels/__init__.py` 导出
5. 在 `main_panel.py` 中添加面板切换逻辑
6. 创建对应的 `.tcss` 样式文件

### 2. 添加新功能

1. **API调用**: 在 `core/live.py` 添加方法
2. **状态管理**: 在 `ui/app.py` 的响应式属性中添加
3. **UI展示**: 在对应Panel中添加显示组件
4. **快捷键**: 在 `utils/constants.py` 的 `KeyBindings` 中添加

### 3. 注意事项

- 所有耗时操作必须在后台线程执行（使用 `self.run_worker(thread=True)`）
- UI更新必须通过 `self.app.call_from_thread()` 回到主线程
- 配置变更后调用 `self.config_manager.save()` 持久化

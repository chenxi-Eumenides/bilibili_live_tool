# bilibili_live_tool 项目说明

> **代码结构文档** — 反映仓库当前实际状态
> 注意：logic 层已部分重构，danmaku/CLI/TUI 尚未适配新 API。
> **最后更新**: 2026-04-29
> **当前分支**: `dev`

---

## 一、项目概述

基于 **Textual** 框架的 B 站直播终端工具（TUI+CLI），支持扫码登录、开播/下播、修改标题/分区、弹幕监听等功能。

| 项目 | 内容 |
|------|------|
| 名称 | bili_live_tool |
| 版本 | **0.5.0** |
| Python | >=3.9 |
| 构建 | uv + pyinstaller |
| 入口 | `uv run bili` → `src.BiliLiveTool:main` |

### 开发基线

- 方向：**自下而上**（基础层 → 逻辑层 → 用户层）
- 当前：**基础层定稿 ✅，逻辑层主体定稿 ✅，用户层待适配 🔶**

---

## 二、开发要求记录

| 编号 | 日期 | 来源 | 要求 | 状态 |
|------|------|------|------|------|
| R01 | 2026-04-28 | 用户 | 完成 TUI 层开发 | 🔶 逻辑层完成后继续 |
| R02 | 2026-04-28 | 用户 | 开发计划放在 `plan/` 下 | ✅ |
| R03 | 2026-04-28 | 用户 | 每个小功能单独分支 | ✅ |
| R04 | 2026-04-28 | 用户 | 边框边距按需使用 | ✅ |
| R05 | 2026-04-28 | 用户 | 黑色终端主题 | ✅ |
| R06 | 2026-04-28 | 用户 | 不变更弹幕颜色定义 | ✅ |
| R07 | 2026-04-28 | 用户 | 代码风格适配规范 | ✅ |
| R08 | 2026-04-28 | 用户 | 生成项目说明文件 | ✅ |
| R09-R17 | — | — | Logic 修复项、测试规范、分支策略 | ✅ |

---

## 三、三层架构概览

```
┌────────────────────────────────────────────────────┐
│                    入口分发                         │
│         src/BiliLiveTool.py (总入口)                │
├──────────────┬─────────────────┬───────────────────┤
│   用户层     │  CLI 模式       │  TUI 模式         │
│ (View)       │  src/cli/ 🔶    │  src/tui/ 🔶      │
│              │  待适配         │  待适配           │
├──────────────┴─────────────────┴───────────────────┤
│                    逻辑层                           │
│  src/logic/  session/auth/live ✅                  │
│              danmaku.py 🔶 待更新                  │
├────────────────────────────────────────────────────┤
│                    基础层                           │
│  src/utils/  ✅ 全部定稿                            │
└────────────────────────────────────────────────────┘
```

核心原则（详见 `architecture-spec.md`）：
- 基础层纯函数零状态
- 逻辑层通过 `FuncResult` + `SessionEvent` 双通道通知
- 用户层只 import 逻辑层

---

## 四、各层模块清单

### 4.1 基础层 `src/utils/` ✅ 定稿

| 文件 | 职责 | 关键导出 |
|------|------|---------|
| `constant.py` | 常量定义 | `VERSION`, `ApiData`, `ApiUrl`, `SessionEvent`, `BiliCode`, `Tuning` |
| `config.py` | 配置数据类 | `CONFIG` (dataclass, v1/v2/v3) |
| `lib.py` | 工具函数 | `sign_data`, `generate_qr_text`, `pack_ws_body`, `unpack_ws_message`, `encWbi` |
| `data.py` | 数据结构 | `FuncResult`, `DanmakuMessage`, `GiftMessage`, `LiveAreaList`, `AppState` |
| `error.py` | 错误类型 | `FuncType`, `FAIL`, `API_BILI_CODE_ERROR`, `FAIL_BILI_CODE` |
| `api.py` | API 调用 | `api()`, `api_with_sign()`, `ws_listen_danmaku` |

### 4.2 逻辑层 `src/logic/`

| 文件 | 关键导出 | 状态 |
|------|---------|------|
| `session.py` | `Session` (is_login/is_live/can_live/app_state, 事件系统) | ✅ 定稿 |
| `auth.py` | `auth_get_qr`, `auth_poll_qr`, `auth_update_safety`, `auth_validate_login`, `auth_logout` | ✅ 定稿 |
| `live.py` | `live_init`, `live_start`, `live_stop`, `live_update_room`, `live_refresh_room_data` | ✅ 定稿 |
| `danmaku.py` | `danmaku_start`, `danmaku_stop`, `_listen_loop` | 🔶 待更新 |

> `danmaku.py` 当前仍引用旧版 Session 属性（`session.is_logged_in`、`session.user_id`、`session.room_id`），需适配新版 Session API。

### 4.3 用户层 CLI `src/cli/` 🔶 未适配

| 文件 | 备注 |
|------|------|
| `main.py` | 基于旧版 logic API，多处不兼容 |

### 4.4 用户层 TUI `src/tui/` 🔶 未适配

| 目录 | 文件 | 备注 |
|------|------|------|
| 根 | `main.py`, `app.py`, `__init__.py` | 原始代码 |
| `layout/` | `header.py`, `sidebar.py`, `main_panel.py`, `status_bar.py` | 原始代码 |
| `panels/` | `auth_panel.py`, `dashboard_panel.py`, `settings_panel.py`, `danmaku_panel.py`, `help_panel.py` | 原始代码 |
| `styles/` | 7 个 tcss 文件 | ✅ 视觉可用 |

> TUI 的 layout/panels/styles 结构已搭建，但内部引用的 logic API 仍为旧版。
> 适配将在 logic 层（含 danmaku）定稿后进行。

---

## 五、文件结构总览

```
src/
├── BiliLiveTool.py              # 总入口 ✅
├── cli/main.py                  # CLI 🔶 待适配
├── logic/
│   ├── session.py               # ✅ 定稿
│   ├── auth.py                  # ✅ 定稿
│   ├── live.py                  # ✅ 定稿
│   ├── danmaku.py               # 🔶 待更新
│   └── __init__.py
├── tui/
│   ├── app.py, main.py          # 🔶 待适配
│   ├── layout/ (4 files)       # 🔶 待适配
│   ├── panels/ (5 files)       # 🔶 待适配
│   └── styles/ (7 tcss)        # ✅
└── utils/ (6 files)             # ✅ 全部定稿
```

---

## 六、技术栈与依赖

| 包 | 用途 |
|----|------|
| textual >=7.3.0 | TUI 框架 |
| requests >=2.32.3 | HTTP 请求 |
| websockets >=15.0.1 | WebSocket（弹幕）|
| brotli >=1.2.0 | Brotli 解压 |
| qrcode >=8.2 | 二维码生成 |

---

## 七、关键数据结构

### FuncResult
```python
@dataclass(frozen=True)
class FuncResult:
    type: FuncType  # SUCCESS | FAIL | ERROR
    result: Any
```

### DanmakuMessage
- 属性：`uname`, `uid`, `msg`, `timestamp`, `privilege_type`, `medal_name`, `color`, `badge_text`
- 方法：`format_rich()` → Rich markup 文本

### AppState
```python
class AppState(Enum):
    UNAUTH = auto()  # 未登录
    IDLE = auto()    # 已登录未开播
    LIVE = auto()    # 直播中
    REPLAY = auto()  # 轮播中
```

---

## 八、配置文件格式（v3）

```json
{
    "version": 3,
    "user": { "uid": 0, "cookies_str": "", "csrf": "",
        "refresh_token": "", "refresh_time": 0,
        "bili_ticket": "", "bili_ticket_timestamp": 0,
        "bili_ticket_ttl": 0,
        "wbi_img_key": "", "wbi_sub_key": "",
        "need_update_bili_ticket": false, "need_update_wbi": false },
    "live": { "room_id": 0, "title": "", "area_id": 0, "parent_area_id": 0,
        "rtmp_addr": "", "rtmp_code": "" },
    "data": { "room": {}, "area": [] },
    "app": { "default_mode": "help" }
}
```

> v3 相对 v2 新增：`bili_ticket`, `wbi_key`, `parent_area_id`, `need_update_*` 标记

---

## 九、当前模块进度

| 模块 | 状态 | 备注 |
|------|------|------|
| utils/api | ✅ 定稿 | B站 API（HTTP + WebSocket）|
| utils/lib | ✅ 定稿 | 签名/编解码/WS封包/二维码 |
| utils/data | ✅ 定稿 | 数据结构 |
| utils/error | ✅ 定稿 | 错误类型 |
| utils/config | ✅ 定稿 | v1/v2/v3 识别 |
| utils/constant | ✅ 定稿 | 所有常量 |
| logic/session | ✅ 定稿 | Session 状态 + 事件系统 |
| logic/auth | ✅ 定稿 | 扫码登录全流程 |
| logic/live | ✅ 定稿 | 开播/下播/改标题/分区/刷新 |
| logic/danmaku | 🔶 待更新 | 引用旧版 Session 属性 |
| CLI | 🔶 待适配 | 基于旧版 logic API |
| TUI | 🔶 待适配 | 基于旧版 logic API |
| 单元测试 | 🔶 待更新 | 需同步适配 |

---

## 十、已完成的关键修复

| 修复项 | 说明 |
|--------|------|
| `api_update_room` area_id | 修正为 `config.area_v2` 属性 |
| `unpack_ws_message` ver=3 | Brotli 支持（`_member_map_` 名值混淆修复）|
| `ws_listen_danmaku` 静默退出 | 改为 yield ERROR |
| `ws_send_auth` | 捕获 ConnectionClosedError |
| `lib.py` 错误类型 | 裸 raise 改为 `FUNC_DATA_ERROR` |

---

## 十一、测试与构建

```bash
python -m unittest unittest.test_src_logic  # Logic 层（需同步适配）
ruff check src/                             # 代码检查
```

---

## 十二、plan 文档索引

| 文件 | 说明 |
|------|------|
| `requirements-summary.md` | 需求汇总（不动）|
| `architecture-spec.md` | **架构设计规格书** — 目标设计 + 适配路线图 |
| `project-overview.md`（本文件） | **代码结构文档** |
| `logic-layer-design-spec.md` | 旧版 logic 规格（内容已并入 architecture-spec）|
| `tui-layer-design-spec.md` | 旧版 TUI 规格（内容已并入 architecture-spec）|

---

## 十三、Git 分支策略

```
master → dev（当前）
```
- 功能分支开发完成后合并到 `dev`
- 合并后删除功能分支

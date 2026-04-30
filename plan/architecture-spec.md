# bilibili_live_tool 架构设计规格书

> **目标设计文档** — 描述系统应该呈现的最终架构
> 合并自 `logic-layer-design-spec.md` + `tui-layer-design-spec.md`
> 标注"待更新"/"待适配"的模块为尚未实现的目标设计
> 对应 committed 版本: **0.5.0**

---

## 一、整体架构（三层模型）

```
┌──────────────────────────────────────────────────────────────┐
│                       入口分发                                │
│              src/BiliLiveTool.py (总入口)                     │
│          _dispatcher() 按 flags 匹配分发                      │
├──────────────┬────────────────────┬──────────────────────────┤
│   用户层     │   CLI 模式          │   TUI 模式              │
│ (View)       │  src/cli/           │  src/tui/               │
│              │  同步调用 无状态     │  事件订阅驱动 有状态    │
│              │  FLAGS + run()      │  BiliLiveToolApp (App)  │
├──────────────┴────────────────────┴──────────────────────────┤
│                       逻辑层                                  │
│  src/logic/  session ✅ / auth ✅ / live ✅ / danmaku ✅     │
│              Session 持有状态 + 事件系统                       │
├──────────────────────────────────────────────────────────────┤
│                       基础层                                  │
│  src/utils/  ✅ 全部定稿                                      │
│              (api / lib / data / error / config / constant)   │
└──────────────────────────────────────────────────────────────┘
```

**核心原则**：
- 基础层纯函数，零状态，不 import 上层模块
- 逻辑层持有 Session 状态，`FuncResult` 返回 + `SessionEvent` 事件双通道通知
- 用户层只 import 逻辑层，不直接 import 基础层（入口文件除外）
- CLI 和 TUI 各自导出 `FLAGS`、`run()`、`help_lines()`

**当前状态**：基础层 ✅ 定稿 → 逻辑层 ✅ 全部定稿 → 用户层 CLI ✅，TUI 🔶

> 开发规范（导入原则、常量管理、文档格式、分层规则、测试规范、分支策略）详见 `development-standards.md`。

---

## 二、基础层 `src/utils/` ✅ 定稿

### 2.1 模块清单

| 文件 | 关键导出 |
|------|---------|
| `api.py` | `api()`, `api_with_sign()`, `ws_listen_danmaku`, `get_danmaku_info`, `get_wbi_key` |
| `lib.py` | `sign_data`, `generate_qr_text`, `pack_ws_body`, `unpack_ws_message`, `encWbi`, `hmac_sha256` |
| `data.py` | `FuncResult`, `DanmakuMessage`, `GiftMessage`, `NoticeMessage`, `LiveAreaList`, `AppState`, `ApiResult` |
| `error.py` | `FuncType`, `FAIL`, `API_BILI_CODE_ERROR`, `FAIL_BILI_CODE` |
| `config.py` | `CONFIG` (dataclass, 支持 v1/v2/v3 格式) |
| `constant.py` | `VERSION`, `ApiData`, `ApiUrl`, `SessionEvent`, `BiliCode`, `Tuning` |

### 2.2 关键修复
| 修复项 | 说明 |
|--------|------|
| `api_update_room` area_id | 修正为 `config.area_v2` |
| `unpack_ws_message` ver=3 | Brotli 支持 |
| `ws_listen_danmaku` 静默退出 | 改为 yield ERROR |
| `ws_send_auth` | 捕获 ConnectionClosedError |
| `lib.py` 裸 raise | 改为 `FUNC_DATA_ERROR` |

---

## 三、逻辑层 `src/logic/`

### 3.1 session.py ✅ 定稿

`Session` 类：持有 CONFIG，管理 AppState，提供事件系统。

```python
class Session:
    # 状态
    config: CONFIG           # property: _config
    app_state: AppState      # property: _app_state  (UNAUTH/IDLE/LIVE/REPLAY)
    is_login: bool           # config.has_cookies && _login_verified && app_state != UNAUTH
    is_live: bool            # app_state == LIVE
    is_replay: bool          # app_state == REPLAY
    can_live: bool           # is_login && room_id && uid && area_id && app_state == IDLE
    room_data: dict          # 房间信息
    area_list: LiveAreaList  # 分区列表

    # 事件系统
    on(event, callback)      # 注册
    off(event, callback)     # 取消
    once(event, callback)    # 一次性
    _emit(event, *args)      # 触发（内部使用）
```

> 公开属性：`danmaku_room_id`、`qr_cache`、`face_qr_cache` 均为直接公开字段（无下划线前缀）

### 3.2 auth.py ✅ 定稿

| 函数 | 说明 |
|------|------|
| `auth_get_qr(session)` | 生成二维码，触发 `AUTH_QR_READY / AUTH_QR_FAIL` |
| `auth_poll_qr(session, qr_key, timeout_sec, stop_event)` | 轮询扫码状态 |
| `auth_update_safety(session)` | 更新 bili_ticket + wbi_key |
| `auth_validate_login(session)` | 验证 cookies 有效性 |
| `auth_logout(session)` | 清空登录态 |

### 3.3 live.py ✅ 定稿

| 函数 | 说明 |
|------|------|
| `live_init(session)` | 开播准备：分区列表 + 直播间号 + 房间信息 |
| `live_start(session, area_id)` | 开播 |
| `live_stop(session)` | 下播 |
| `live_update_room(session, title, area_id)` | 改标题/分区 |
| `live_refresh_room_data(session)` | 拉取最新 room_data |

### 3.4 danmaku.py ✅ 定稿

| 函数 | 说明 |
|------|------|
| `danmaku_start(session)` | 准备弹幕监听（同步，前置校验）|
| `danmaku_stop(session)` | 设置停止信号 |
| `_listen_loop(session)` | 异步主循环：获取信息 → 连接 → 认证 → 心跳 → 接收 → 清理 |

**适配完成**：旧属性替换（`session.is_logged_in` → `session.is_login`、`session.user_id` → `session.config.uid`、`session.room_id` → `session.config.room_id`），新增事件发布。

### 3.5 事件系统（SessionEvent）✅ 定稿

| 事件 | 触发函数 |
|------|---------|
| `AUTH_QR_READY` | auth_get_qr |
| `AUTH_QR_FAIL` | auth_get_qr |
| `AUTH_QR_WAITING` | auth_poll_qr |
| `AUTH_QR_SCANNED` | auth_poll_qr |
| `AUTH_LOGIN_SUCCESS` | auth_poll_qr, auth_validate_login |
| `AUTH_LOGIN_FAILED` | auth_poll_qr, auth_validate_login |
| `AUTH_LOGOUT` | auth_logout |
| `AUTH_UPDATE_SAFETY` | auth_update_safety |
| `AUTH_SAFETY_SKIPPED` | auth_update_safety |
| `AUTH_UPDATE_SAFETY_FAIL` | auth_update_safety |
| `LIVE_STATE_CHANGED` | live_start, live_stop |
| `LIVE_INFO_UPDATED` | live_init, live_update_room, live_refresh_room_data |
| `LIVE_INFO_UPDATED_FAIL` | live_init, live_update_room, live_refresh_room_data |
| `LIVE_AREA_UPDATED` | live_init |
| `LIVE_AREA_UPDATED_FAIL` | live_init |
| `LIVE_FACE_AUTH_REQUIRED` | live_start |
| `LIVE_START_FAIL` | live_start |
| `LIVE_STOP_FAIL` | live_stop |
| `DANMAKU_RECEIVED` | _listen_loop |
| `DANMAKU_STOPPED` | _listen_loop, danmaku_stop |
| `DANMAKU_STARTED` | danmaku_start |
| `DANMAKU_START_FAIL` | danmaku_start |
| `DANMAKU_STOP_FAIL` | danmaku_stop |
| `ERROR` | 各处 |
| `EXCEPTION` | 各处 |

---

## 四、用户层 CLI `src/cli/` ✅ 已适配

**目标设计**（已在 `dev-cli-migration` 分支实现）：

### 入口标志
```python
CLI_FLAGS = frozenset({"--login", "--start", "--stop", "--status", "--update", "--area", "--danmaku", "--cli"})
```

### 命令列表
| 命令 | 说明 |
|------|------|
| `--login` | 扫码登录 |
| `--logout` | 清除登录态 |
| `--start [-a ID] [-t TITLE]` | 开播 |
| `--stop` | 下播 |
| `--status` | 房间状态 |
| `--update [-a ID] [-t TITLE]` | 改标题/分区 |
| `--area [list] [父分区ID]` | 列出分区 |
| `--danmaku [直播间号]` | 弹幕监听 |
| `--cli` | 一键登录+自动开/下播 |

### 文件结构（目标）
```
src/cli/
├── __init__.py   # 导出 FLAGS, help_lines, run
├── main.py       # 入口：flat ArgumentParser + async dispatch + session lifecycle
├── auth.py       # handle_login, handle_logout（事件驱动）
├── live.py       # handle_live_start/stop/status/update/area/cli（事件驱动）
└── danmaku.py    # handle_danmaku（事件驱动 + async _listen_loop）
```

### 关键设计点
- Flat CLI 接口：`--start/--stop/--status/--update` 取代旧 `--live start/stop/status`
- 事件驱动 handlers：通过 `session.once()` 订阅 SessionEvent，不再检查 `FuncResult.type`
- 全异步入口：`asyncio.run()`，handler 均为 async 函数
- Session 自动初始化：`auth_validate_login` → `auth_update_safety` → `live_init`

### 适配要点

| 旧代码 | 应改为 |
|--------|--------|
| `session.is_logged_in` | `session.is_login` |
| `session.user_id` | `session.config.uid` |
| `session.room_id` | `session.config.room_id` |
| `session.config.room_data` | `session.room_data` |
| `live_get_area_list(session)` | `live_init(session)` + `session.area_list` |

---

## 五、用户层 TUI `src/tui/` 🔶 待适配

**当前状态**：layout/panels/styles 结构已搭建，但内部引用的 logic API 仍为旧版。

### 5.1 整体架构（目标设计）

```
BiliLiveToolApp (App)
├── Header                 (layout/header.py)
├── Sidebar                (layout/sidebar.py)
├── MainPanel              (layout/main_panel.py)
│   ├── AuthPanel          — 扫码登录
│   ├── DashboardPanel     — 信息展示
│   ├── SettingsPanel      — 管理操作
│   ├── DanmakuPanel       — 弹幕
│   └── HelpPanel          — 帮助
└── StatusBar              (layout/status_bar.py)
```

### 5.2 事件订阅（目标设计）

| Widget | 订阅事件 |
|--------|---------|
| Header | `AUTH_LOGIN_SUCCESS`, `AUTH_LOGOUT`, `LIVE_STATE_CHANGED` |
| Sidebar | `AUTH_LOGIN_SUCCESS`, `AUTH_LOGOUT`, `LIVE_STATE_CHANGED` |
| AuthPanel | `AUTH_QR_READY`, `AUTH_QR_WAITING`, `AUTH_QR_SCANNED`, `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED` |
| DashboardPanel | `LIVE_INFO_UPDATED` |
| SettingsPanel | `LIVE_STATE_CHANGED`, `LIVE_INFO_UPDATED` |
| DanmakuPanel | `DANMAKU_RECEIVED`, `DANMAKU_STOPPED` |

### 5.3 适配要点

| 旧代码 | 位置 | 应改为 |
|--------|------|--------|
| `auth_post_login(session)` | `app.py:103` | `auth_update_safety(session)` + `live_init(session)` |
| `self.app.qr_cache` | `auth_panel.py:63,81` | `self.app.session.qr_cache` |
| `config.room_data` | `dashboard_panel.py:64` | `session.room_data` |
| `live_get_area_list(session)` | `settings_panel.py:7,36` | `live_init(session)` + `session.area_list` |
| `session.room_id` | `danmaku_panel.py:26` | `session.config.room_id` |
| `auth_validate_login` 未处理结果 | `app.py:76-77` | 成功后调用 `auth_update_safety` + `live_init` |

### 5.4 样式系统（✅ TCSS 颜色变量统一）

7 个 `.tcss` 文件头部统一声明了 18 个颜色变量：

```tcss
/* 背景色 */
$bg-darkest: #1a1a1a     /* 最深背景 */
$bg-dark: #2a2a2a        /* 面板/侧栏背景 */
$bg-medium: #3a3a3a      /* 次级背景/卡片 */

/* 文字色 */
$text-primary: #e5e5e5   /* 主文本 */
$text-muted: #999999     /* 次要文本 */

/* B站强调色 */
$accent: #00a1d6         /* 强调色（B站蓝）*/
$accent-hover: #0088b3   /* 悬停 */
$accent-active: #006f95  /* 激活 */
$accent-dim: #005574     /* 边框 / 非活跃状态 */

/* 语义色 */
$success: #52c41a        /* 成功 */
$error: #f5222d          /* 错误/警告信息 */
$warning: #f59e0b        /* 警告 */

/* 弹幕头衔色 */
$badge-tidu: #0066CC     /* 提督 */
$badge-jianzhang: #66CCFF /* 舰长 */
$badge-fan: #FFB6C1      /* 粉丝 */

/* 弹幕系统通知色 */
$system-light: #FF6B6B   /* 系统消息（亮）*/
$system-dark: #CC0000    /* 系统消息（暗）*/

/* 边框 */
$border-dim: #555555     /* 次级边框 */
```

> 修改颜色仅需同步 7 个 `.tcss` 文件头部变量定义。`header.py` 中的 `color_map` 字典同样使用上述 hex 值。

---

## 六、入口分发 `src/BiliLiveTool.py` ✅ 定稿

1. `--help` 拼接 cli/tui 的 `help_lines()`
2. `--set-default MODE` 存 `config.json`
3. `_dispatcher()` 按 `cli.FLAGS` vs `tui.FLAGS` 匹配
4. 无匹配时读 `config.default_mode`

### 可用入口

```
uv run bili                       # 按 default_mode
uv run bili --help
uv run bili --tui                 # TUI
uv run bili --cli                 # 交互式 CLI
```

---

## 七、数据流

### 7.1 FuncResult 模式
```python
result = live_start(session, area_id=123)
if result.type == FuncType.SUCCESS:
    data = result.result
else:
    print(f"失败: {result.result}")
```

### 7.2 Session 属性（适配后）

| 属性 | 来源 | 说明 |
|------|------|------|
| `session.is_login` | Session property | 是否已登录 |
| `session.is_live` | Session property | 是否直播中 |
| `session.can_live` | Session property | 能否开播 |
| `session.app_state` | Session property | 应用状态枚举 |
| `session.config` | Session property | CONFIG 实例 |
| `session.config.uid` | CONFIG field | B站 UID |
| `session.config.room_id` | CONFIG field | 直播间号 |
| `session.config.cookies` | CONFIG field | cookies |
| `session.config.area_id` | CONFIG field | 分区 ID |
| `session.room_data` | Session attr | 最新房间数据 dict |

---

## 八、配置格式

### v3 格式（当前定稿）

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

---

## 九、适配路线图

### 第一阶段：Logic 层收尾（已完成 ✅）
- [x] `danmaku.py` — 旧 Session 属性替换 + 新增事件
- [x] `Session` — `danmaku_room_id`、`qr_cache`、`face_qr_cache` 改为公开字段
- [x] 同步更新 `__init__.py` 导出
- [x] 新增 5 个事件常量 + 所有 return 事件通知

### 第二阶段：CLI 层适配（已完成 ✅）
- [x] 文件拆分：main → main/auth/live/danmaku
- [x] Flat CLI 接口：`--start/--stop/--status/--update`
- [x] 事件驱动 handlers（`session.once()` 替代 `FuncResult` 判断）
- [x] 全异步入口 + Session 自动初始化
- [x] 替换所有旧属性路径

### 第三阶段：TUI 层适配
- [ ] `app.py` — 替换 `auth_post_login` → `auth_update_safety` + `live_init`
- [ ] `auth_panel.py` — 通过 `session.qr_cache` 访问缓存
- [ ] `dashboard_panel.py` — `config.room_data` → `session.room_data`
- [ ] `settings_panel.py` — 替换 `live_get_area_list`
- [ ] `danmaku_panel.py` — 修正属性路径 + 事件集成
- [ ] 统一验证事件流

### 第四阶段：测试
- [ ] 同步更新 `unittest/test_src_logic.py`
- [ ] `ruff check src/` 验证

---

## 十、参考

- `plan/project-overview.md` — 代码结构文档
- `plan/development-standards.md` — 开发规范

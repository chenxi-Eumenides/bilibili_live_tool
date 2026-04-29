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
│  src/logic/  session ✅ / auth ✅ / live ✅ / danmaku 🔶     │
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

**当前状态**：基础层 ✅ 定稿 → 逻辑层 ✅ 主体定稿（danmaku 🔶）→ 用户层 🔶 待适配

---

## 二、开发规范

### 2.1 导入原则
- **最小导入**：`from xxx import a, b`，不用 `import xxx`
- **函数内禁止导入**：所有 import 在文件顶部
- **无未使用导入**：`ruff F401` 检查
- **相对导入**：项目内 `from ..logic import Session`

### 2.2 常量管理
所有可复用常量在 `src/utils/constant.py` 的类中：

| 类 | 内容 |
|---|------|
| `ApiData` | API 默认参数 |
| `ApiUrl` | API 地址 |
| `BiliCode` | B站 API 状态码 |
| `SessionEvent` | 事件名称（字符串常量）|
| `Tuning` | 运行时调优参数 |

> 颜色常量不放入 constant.py。TUI 颜色统一在 `.tcss` 中写十六进制值。

### 2.3 文档格式
```python
"""简短说明。

Args:
    session: Session 实例
    param: 说明
Returns:
    FuncResult(SUCCESS, ...) 或 FAIL
Events:
    EVENT_NAME: 何时触发
"""
```

### 2.4 分层规则

| 层 | 可依赖 | 不可 |
|----|--------|------|
| utils | 标准库 + 第三方 SDK | logic/cli/tui |
| logic | utils | cli/tui，不直接调 `api()` |
| cli/tui | logic（入口文件可调 config）| utils/api.py |

### 2.5 测试规范
- Logic 层 mock 测试，不依赖网络
- API 层集成测试，需要真实 `unittest/config.json`
- 测试不污染真实 `config.json`

### 2.6 分支策略
- 每个功能/修复单独分支，完成后合并回 `dev`
- 当前开发分支：`dev`

---

## 三、基础层 `src/utils/` ✅ 定稿

### 3.1 模块清单

| 文件 | 关键导出 |
|------|---------|
| `api.py` | `api()`, `api_with_sign()`, `ws_listen_danmaku`, `get_danmaku_info`, `get_wbi_key` |
| `lib.py` | `sign_data`, `generate_qr_text`, `pack_ws_body`, `unpack_ws_message`, `encWbi`, `hmac_sha256` |
| `data.py` | `FuncResult`, `DanmakuMessage`, `GiftMessage`, `NoticeMessage`, `LiveAreaList`, `AppState`, `ApiResult` |
| `error.py` | `FuncType`, `FAIL`, `API_BILI_CODE_ERROR`, `FAIL_BILI_CODE` |
| `config.py` | `CONFIG` (dataclass, 支持 v1/v2/v3 格式) |
| `constant.py` | `VERSION`, `ApiData`, `ApiUrl`, `SessionEvent`, `BiliCode`, `Tuning` |

### 3.2 关键修复
| 修复项 | 说明 |
|--------|------|
| `api_update_room` area_id | 修正为 `config.area_v2` |
| `unpack_ws_message` ver=3 | Brotli 支持 |
| `ws_listen_danmaku` 静默退出 | 改为 yield ERROR |
| `ws_send_auth` | 捕获 ConnectionClosedError |
| `lib.py` 裸 raise | 改为 `FUNC_DATA_ERROR` |

---

## 四、逻辑层 `src/logic/`

### 4.1 session.py ✅ 定稿

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

> **待补充公开 property**（当前为私有字段，适配用户层时需要）：
> - `danmaku_room_id` → getter/setter for `_danmaku_room_id`
> - `qr_cache` → getter for `_qr_cache`

### 4.2 auth.py ✅ 定稿

| 函数 | 说明 |
|------|------|
| `auth_get_qr(session)` | 生成二维码，触发 `AUTH_QR_READY / AUTH_QR_FAIL` |
| `auth_poll_qr(session, qr_key, timeout_sec, stop_event)` | 轮询扫码状态 |
| `auth_update_safety(session)` | 更新 bili_ticket + wbi_key |
| `auth_validate_login(session)` | 验证 cookies 有效性 |
| `auth_logout(session)` | 清空登录态 |

### 4.3 live.py ✅ 定稿

| 函数 | 说明 |
|------|------|
| `live_init(session)` | 开播准备：分区列表 + 直播间号 + 房间信息 |
| `live_start(session, area_id)` | 开播 |
| `live_stop(session)` | 下播 |
| `live_update_room(session, title, area_id)` | 改标题/分区 |
| `live_refresh_room_data(session)` | 拉取最新 room_data |

### 4.4 danmaku.py 🔶 待更新

**当前状态**：仍引用旧版 Session 属性（`session.is_logged_in`、`session.user_id`、`session.room_id`），需适配新版 Session API。

**目标设计**：

| 函数 | 说明 |
|------|------|
| `danmaku_start(session)` | 准备弹幕监听（同步，前置校验）|
| `danmaku_stop(session)` | 设置停止信号 |
| `_listen_loop(session)` | 异步主循环：获取信息 → 连接 → 认证 → 心跳 → 接收 → 清理 |

**适配要点**：
- `session.is_logged_in` → `session.is_login`
- `session.cookies` → `session.config.cookies`
- `session.user_id` → `session.config.uid`
- `session.room_id` → `session.config.room_id`

### 4.5 事件系统（SessionEvent）✅ 定稿

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
| `LIVE_STATE_CHANGED` | live_start, live_stop |
| `LIVE_INFO_UPDATED` | live_init, live_update_room, live_refresh_room_data |
| `LIVE_INFO_UPDATED_FAIL` | live_init, live_update_room, live_refresh_room_data |
| `LIVE_AREA_UPDATED` | live_init |
| `LIVE_AREA_UPDATED_FAIL` | live_init |
| `LIVE_FACE_AUTH_REQUIRED` | live_start |
| `LIVE_START_FAIL` | live_start |
| `LIVE_STOP_FAIL` | live_stop |
| `DANMAKU_RECEIVED` | _listen_loop |
| `DANMAKU_STOPPED` | _listen_loop |
| `ERROR` | 各处 |
| `EXCEPTION` | 各处 |

---

## 五、用户层 CLI `src/cli/main.py` 🔶 待适配

**当前状态**：基于旧版 logic API（旧函数名 + 旧 Session 属性），尚未适配。

**目标设计**：

### 入口标志
```python
CLI_FLAGS = frozenset({"--login", "--logout", "--live", "--title", "--area", "--danmaku", "--cli"})
```

### 命令列表
| 命令 | 说明 |
|------|------|
| `--login` | 扫码登录 |
| `--logout` | 清除登录态 |
| `--live start [--area ID] [--title TITLE]` | 开播 |
| `--live stop` | 下播 |
| `--live status` | 房间状态 |
| `--title TITLE [--area ID]` | 改标题 |
| `--area ID [--title TITLE]` | 改分区 |
| `--area list [父分区ID]` | 列出分区 |
| `--danmaku [直播间号]` | 弹幕监听 |
| `--cli` | 一键登录+自动开/下播 |

### 适配要点

| 旧代码 | 应改为 |
|--------|--------|
| `session.is_logged_in` | `session.is_login` |
| `session.user_id` | `session.config.uid` |
| `session.room_id` | `session.config.room_id` |
| `session.config.room_data` | `session.room_data` |
| `live_get_area_list(session)` | `live_init(session)` + `session.area_list` |
| `session.danmaku_room_id` | `session.danmaku_room_id`（需加 property）|

### 函数引用映射
```
old → new
auth_generate_qrcode → auth_get_qr
auth_poll_login → auth_poll_qr
live_refresh_room_info → live_refresh_room_data
AUTH_QRCODE_READY → AUTH_QR_READY
AUTH_LOGOUT_DONE → AUTH_LOGOUT
```

---

## 六、用户层 TUI `src/tui/` 🔶 待适配

**当前状态**：layout/panels/styles 结构已搭建，但内部引用的 logic API 仍为旧版。

### 6.1 整体架构（目标设计）

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

### 6.2 事件订阅（目标设计）

| Widget | 订阅事件 |
|--------|---------|
| Header | `AUTH_LOGIN_SUCCESS`, `AUTH_LOGOUT`, `LIVE_STATE_CHANGED` |
| Sidebar | `AUTH_LOGIN_SUCCESS`, `AUTH_LOGOUT`, `LIVE_STATE_CHANGED` |
| AuthPanel | `AUTH_QR_READY`, `AUTH_QR_WAITING`, `AUTH_QR_SCANNED`, `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED` |
| DashboardPanel | `LIVE_INFO_UPDATED` |
| SettingsPanel | `LIVE_STATE_CHANGED`, `LIVE_INFO_UPDATED` |
| DanmakuPanel | `DANMAKU_RECEIVED`, `DANMAKU_STOPPED` |

### 6.3 适配要点

| 旧代码 | 位置 | 应改为 |
|--------|------|--------|
| `auth_post_login(session)` | `app.py:103` | `auth_update_safety(session)` + `live_init(session)` |
| `session.qr_cache` | `auth_panel.py:31` | `session._qr_cache`（或加 property）|
| `config.room_data` | `dashboard_panel.py:64` | `session.room_data` |
| `live_get_area_list(session)` | `settings_panel.py:7,36` | `live_init(session)` + `session.area_list` |
| `session.room_id` | `danmaku_panel.py:26` | `session.config.room_id` |
| `session.danmaku_room_id` | `danmaku_panel.py:33` | `session.config.danmaku_room_id`（或加 property）|

### 6.4 样式系统（✅ 已有，无需变更）

```tcss
$bg-primary: #1a1a1a     /* 最深背景 */
$bg-panel: #2a2a2a       /* 面板背景 */
$bg-sub: #3a3a3a          /* 次级背景 */
$accent: #00a1d6          /* 强调色（B站蓝）*/
$border: #006f95          /* 边框色 */
$success: #52c41a         /* 成功 */
$error: #f5222d           /* 错误 */
$warning: #f59e0b         /* 警告 */
```

---

## 七、入口分发 `src/BiliLiveTool.py` ✅ 定稿

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

## 八、数据流

### 8.1 FuncResult 模式
```python
result = live_start(session, area_id=123)
if result.type == FuncType.SUCCESS:
    data = result.result
else:
    print(f"失败: {result.result}")
```

### 8.2 Session 属性（适配后）

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

## 九、配置格式

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

## 十、适配路线图

### 第一阶段：Logic 层收尾
- [ ] `danmaku.py` — 将旧 Session 属性名替换为新 API
- [ ] `Session` — 添加 `danmaku_room_id` property、`qr_cache` property
- [ ] 同步更新 `__init__.py` 导出

### 第二阶段：CLI 层适配
- [ ] 替换 5 个错误 Session 属性路径
- [ ] 替换 `live_get_area_list` → `live_init` + `session.area_list`
- [ ] 验证全部 CLI 命令

### 第三阶段：TUI 层适配
- [ ] `app.py` — 替换 `auth_post_login` → `auth_update_safety` + `live_init`
- [ ] `auth_panel.py` — 通过 property 访问 qr_cache
- [ ] `dashboard_panel.py` — `config.room_data` → `session.room_data`
- [ ] `settings_panel.py` — 替换 `live_get_area_list`
- [ ] `danmaku_panel.py` — 修正属性路径
- [ ] 统一验证事件流

### 第四阶段：测试
- [ ] 同步更新 `unittest/test_src_logic.py`
- [ ] `ruff check src/` 验证

---

## 十一、参考

- `plan/project-overview.md` — 代码结构文档
- `plan/requirements-summary.md` — 需求汇总（不动）

# bilibili_live_tool 开发规格书

## 一、整体架构（三层模型）

```
┌────────────────────────────────────────────────────┐
│                    入口分发                         │
│         src/BiliLiveTool.py (总入口)                │
│         按 cli/tui 导出的 FLAGS 匹配分发            │
├──────────────┬─────────────────┬───────────────────┤
│   用户层     │    CLI 模式     │    TUI 模式       │
│ (View)       │  src/cli/       │  src/tui/         │
│              │  同步调用       │  事件订阅驱动     │
├──────────────┴─────────────────┴───────────────────┤
│                    逻辑层                           │
│  src/logic/  ┌──────┬──────┬──────────┐            │
│              │ auth │ live │ danmaku  │            │
│              └──────┴──────┴────┬─────┘            │
│                       session (状态 + 观察者)       │
├────────────────────────────────────────────────────┤
│                    基础层                           │
│  src/utils/  (api / lib / data / error / config)   │
│              纯函数式，零状态                       │
└────────────────────────────────────────────────────┘
```

**核心原则**：
- 基础层纯函数，零状态，不 import 上层模块
- 逻辑层持有 Session 状态，通过 `FuncResult` 返回 + `SessionEvent` 事件双通道通知用户层
- 用户层只 import 逻辑层，不直接 import 基础层（除入口文件外）
- CLI 和 TUI 各自导出 `FLAGS`、`run()`、`help_lines()`，总入口据此自动分发

## 二、开发规范

### 2.1 导入原则

1. **最小导入**：只用 `from xxx import a, b`，不用 `import xxx` 整包导入
2. **函数内禁止导入**：所有 import 必须在文件顶部
3. **无未使用导入**：全部代码通过 `ruff F401` 检查
4. **相对导入**：项目内使用相对导入（`from ..logic import Session`）

### 2.2 常量管理

所有可复用常量聚合在 `src/utils/constant.py` 的类中：

| 类 | 内容 |
|---|------|
| `ApiData` | API 默认参数 |
| `ApiUrl` | API 地址 |
| `BiliCode` | B站 API 状态码 |
| `SessionEvent` | 事件名称 |
| `Tuning` | 运行时调优参数（延迟/超时/间隔）|
| `TUIColors` / `DanmakuColors` | 颜色常量 |

模块私有常量（仅本模块使用）留在模块内即可。

### 2.3 文档格式

所有 logic 层函数 docstring 使用统一格式：

```
"""简短说明。

Args:
    session: Session 实例
    param: 说明

Returns:
    FuncResult(SUCCESS, ...) 或 FAIL

Events:
    EVENT_NAME: 何时触发

Raises:
    TypeError: 何时抛出
"""
```

### 2.4 配置管理

- `config.json` 自动识别 v1（平铺格式）和 v2（嵌套格式）
- `CONFIG.default_mode` 存储在 `config.json` 的 `app` 节点
- 退出时通过 CLI 的 `finally` 块保存配置（仅登录态有效时）

### 2.5 分层规则

| 层 | 依赖 | 不可 |
|----|------|------|
| utils | 标准库 + 第三方 SDK | 不 import logic/cli/tui |
| logic | utils | 不 import cli/tui, 不直接调 `api()` |
| cli/tui | logic (仅入口文件可调 config) | 不 import utils/api.py |

### 2.6 测试规范

- Logic 层使用 mock 测试，不依赖网络
- API 层使用集成测试，需要真实 `unittest/config.json`
- 测试不得污染真实 `config.json`

### 2.7 分支策略

- 每个独立功能/修复在单独分支开发，完成后合并回 dev
- 合并后删除功能分支

## 三、基础层 (src/utils/)

### 3.1 模块清单

| 文件 | 职责 | 状态 |
|------|------|------|
| `api.py` | B站 API 调用（HTTP + WebSocket）| ✅ |
| `lib.py` | 工具函数（签名/编解码/WS封包/二维码）| ✅ |
| `data.py` | 数据结构（FuncResult/DanmakuMessage/WebSocketProtoVer）| ✅ |
| `error.py` | 错误类型 + FAIL_BILI_CODE 码表 | ✅ |
| `config.py` | CONFIG 数据类，支持 v1/v2 自动识别 | ✅ |
| `constant.py` | 常量聚合（ApiData/ApiUrl/BiliCode/SessionEvent/Tuning）| ✅ |

### 3.2 关键修复

- `api_update_room` area_id 参数修正为 `area_v2`
- `unpack_ws_message` ver=3 支持（`_member_map_` 名值混淆修复）
- `ws_listen_danmaku` 静默退出改为 yield ERROR
- `ws_send_auth` 吞 ConnectionClosedError 修复
- `lib.py` 裸 raise 改为具体 FUNC_DATA_ERROR

## 四、逻辑层 (src/logic/)

### 4.1 session.py

`Session` 类：持有 CONFIG，管理 AppState，提供事件系统。

| 属性 | 说明 |
|------|------|
| `is_logged_in` | 通过 API 验证后才为 True |
| `is_live` | AppState == LIVE |
| `room_id` / `user_id` / `cookies` / `csrf` | Config 便捷访问 |
| `bili_ticket` | 登录后自动获取 |
| `danmaku_room_id` | 弹幕监听房间号（可为其它房间）|

事件系统：`on(event, callback)` / `off()` / `once()` / `_emit()`，回调列表方案。

### 4.2 auth.py

| 函数 | 说明 |
|------|------|
| `auth_generate_qrcode(session)` | 生成登录二维码 |
| `auth_poll_login(session, qr_key)` | 轮询登录 + 自动获取 bili_ticket |
| `auth_validate_login(session)` | API 验证 cookies 有效性 |
| `auth_logout(session)` | 清空登录态 |

### 4.3 live.py

| 函数 | 说明 |
|------|------|
| `live_start(session, area_id)` | 开播（room_id=0 时自动获取）|
| `live_stop(session)` | 下播 |
| `live_update_room(session, title, area_id)` | 改标题/分区（一次 API）|
| `live_refresh_room_info(session)` | 拉取最新房间数据 |
| `live_get_room_info_cache(session)` | 读缓存（无网络）|
| `live_get_area_list(session)` | 获取分区列表 |

### 4.4 danmaku.py

| 函数 | 说明 |
|------|------|
| `danmaku_start(session)` | 同步准备，前置校验 |
| `danmaku_stop(session)` | 设置停止信号 |
| `_listen_loop(session)` | 异步主循环（获取信息→连接→认证→心跳→接收→清理）|
| `_heartbeat_loop(ws, session)` | 后台 30s 心跳 |

### 4.5 事件列表 (SessionEvent)

| 事件 | 触发时机 |
|------|---------|
| `AUTH_QRCODE_READY` | 二维码生成完成 |
| `AUTH_LOGIN_POLLING` | 每次轮询 |
| `AUTH_LOGIN_SUCCESS` | 登录校验成功 |
| `AUTH_LOGIN_FAILED` | 登录失败/过期 |
| `AUTH_LOGOUT_DONE` | 登出完成 |
| `LIVE_STATE_CHANGED` | 开播/下播 |
| `LIVE_INFO_UPDATED` | 房间信息变更 |
| `LIVE_FACE_AUTH_REQUIRED` | 需要人脸认证 |
| `DANMAKU_RECEIVED` | 收到弹幕 |
| `DANMAKU_STOPPED` | 监听停止 |
| `ERROR` | 异常错误 |

## 五、用户层

### 5.1 CLI (src/cli/main.py)

入口标志：`CLI_FLAGS = {"--login", "--logout", "--live", "--title", "--area", "--danmaku", "--cli"}`

| 命令 | 说明 |
|------|------|
| `--login` | 扫码登录 |
| `--logout` | 清除登录态 |
| `--live start [--area ID] [--title TITLE]` | 开播 |
| `--live stop` | 下播 |
| `--live status` | 房间状态（总是刷新）|
| `--title TITLE [--area ID]` | 改标题（可同时改分区）|
| `--area ID [--title TITLE]` | 改分区 |
| `--area list [父分区ID]` | 列出分区 |
| `--danmaku [直播间号]` | 弹幕监听 |
| `--cli` | 一键登录+自动开/下播 |

### 5.2 TUI (src/tui/) — 占位

入口标志：`TUI_FLAGS = {"--tui"}` 实际功能尚未实现。

## 六、入口分发 (src/BiliLiveTool.py)

1. `--help` 在总入口解析，拼接 cli/tui 的 `help_lines()`
2. `--set-default MODE` 存 `config.json` 的 `app.default_mode`
3. 其余参数按 `cli.FLAGS` vs `tui.FLAGS` 匹配分发
4. 无匹配时读 `config.default_mode` 决定

## 七、可用入口

```
uv run bili                       # 按 default_mode 启动
uv run bili --help                # 帮助
uv run python -m src.BiliLiveTool # 直接调用
```

## 八、当前进度

| 模块 | 状态 |
|------|------|
| 基础层 | ✅ 完成，6 个 bug 已修复 |
| logic/session | ✅ |
| logic/auth | ✅ |
| logic/live | ✅ |
| logic/danmaku | ✅ |
| CLI | ✅ |
| TUI | 🔶 占位 |
| 单元测试 | 🔶 47 个 logic 层测试通过 |

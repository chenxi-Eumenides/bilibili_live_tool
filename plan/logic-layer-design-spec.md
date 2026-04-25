# bilibili_live_tool 重构设计规格书

## 一、整体架构（三层模型）

```
┌────────────────────────────────────────────────────┐
│                    入口分发                         │
│         src/__main__.py (cli | tui | help)         │
├──────────────┬─────────────────┬───────────────────┤
│   用户层     │    CLI 模式     │    TUI 模式       │
│ (View)       │  src/cli/       │  src/tui/         │
│              │  纯同步调用     │  事件订阅驱动     │
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
- 基础层（utils）**纯函数**，无状态，不 import 任何上层模块
- 逻辑层有状态（session），直接调基础层函数，不 import 用户层
- 用户层只 import 逻辑层，不 import 基础层
- 逻辑层为 CLI 和 TUI 提供完全相同的 API——CLI 同步调用获取返回值，TUI 订阅事件获取推送

**三层职责**：

| 层 | 有状态？ | 依赖方向 | 返回方式 |
|---|---|---|---|
| 基础层 (utils) | ❌ 纯函数 | 只依赖标准库+第三方SDK | `FuncResult` |
| 逻辑层 (logic) | ✅ 持有 session | 依赖 utils | 返回值 + 事件 |
| 用户层 (cli/tui) | ✅ 各自UI状态 | 依赖 logic | 用户可见的输出 |

---

## 二、基础层 (src/utils/) — 已完成，有 bug 需修

### 2.1 当前模块清单

| 文件 | 行数 | 职责 | 状态 |
|------|------|------|------|
| `api.py` | 763 | 所有 B 站 API 调用（登录、直播、弹幕 WebSocket） | 有 4 个 bug 待修 |
| `lib.py` | 249 | 纯工具函数（签名、编码、WS 封包/解包、二维码） | 有 2 个 bug 待修 |
| `data.py` | 514 | 数据结构（FuncResult, ApiResult, DanmakuMessage 等） | ✅ |
| `constant.py` | 262 | 常量（ApiUrl, ApiData, 颜色常量等） | 含未定义的 CSS 引用待移除 |
| `error.py` | 155 | 错误类型体系 | ✅ |
| `config.py` | 193 | CONFIG 数据类 | ✅ |

### 2.2 需要修复的 6 个 bug

1. **`ws_send_auth` 吞异常**（api.py）：`ConnectionClosedError` 被 catch 后仍返回 `FuncResult(SUCCESS)`，应为 `FuncResult(FAIL)` 或 `FuncResult(ERROR)`
2. **缺失心跳循环**（api.py）：B 站弹幕 WS 要求每 30 秒发一次心跳包，目前只有 `ws_send_heart` 函数，没有循环逻辑
3. **`ws_listen_danmaku` 静默退出**（api.py）：生成器 `return` 时无声无息，调用方无从得知连接断开，需要 `yield` 一个 ERROR/STOPPED 结果
4. **裸 `raise`**（lib.py L129, L182）：无参数 `raise` 只能在 except 块内使用，如果恰好不在 except 块内会抛 `RuntimeError`
5. **数组越界**（lib.py L132）：`offset <= len(raw_msg)` 应为 `offset < len(raw_msg)`，当前写法最后一次递归会越界
6. **print 调试残留**（api.py 多处）：正式代码中不应有裸 `print()`

### 2.3 constant.py 的 CSS 常量

移除 `CCS_APP`、`CCS_MAIN_SCREEN` 等未定义的 CSS 常量引用——它们属于 TUI 层，不属基础层。颜色常量（`TUIColors`, `DanmakuColors`）保留，因为逻辑层不需要颜色。

### 2.4 二维码生成

`lib.generate_qr_text(qr_url) → list[str]` 已经在基础层。逻辑层调用它得到字符串列表，**不做任何渲染**。CLI 层 `print("\n".join(lines))`，TUI 层在 `RichLog` 或 `Label` widget 中用 monospace 字体逐行渲染。

---

## 三、逻辑层 (src/logic/) — 本次重点设计

### 3.1 目录结构

```
src/logic/
├── __init__.py        # 对外暴露所有公共 API 函数
├── session.py         # 状态中心 + 轻量观察者（回调列表）
├── auth.py            # 登录认证编排
├── live.py            # 直播管理编排
└── danmaku.py         # 弹幕处理编排
```

### 3.2 session.py — 状态与事件中心

#### 数据
- 持有全局唯一的 `CONFIG` 实例（来自 `utils.config`）
- 保存当前会话状态：是否已登录、当前 room_id、直播状态等
- **不保存中间态**（如 qrcode_key、轮询 token）——由各编排函数内部局部变量维护

#### 事件系统（轻量回调列表）

设计为方案 A（回调列表），手动管理订阅：

```python
session._listeners: dict[str, list[Callable]] = {
    "auth:qrcode_ready": [callback1, callback2],
    "auth:login_success": [...],
    ...
}
```

**API**：
- `session.on(event: str, callback: Callable)` → 注册回调
- `session.off(event: str, callback: Callable)` → 取消注册
- `session._emit(event: str, *args)` → 内部触发，遍历回调列表依次调用

#### 事件类型清单（10 种）

| 事件名 | 触发时机 | 携带参数 | 消费者 |
|--------|----------|----------|--------|
| `auth:qrcode_ready` | 二维码 URL 已获取 | `(qr_url: str)` | CLI: print 二维码; TUI: 渲染二维码图 |
| `auth:login_polling` | 正在轮询登录状态（周期性） | `(remaining: int)` 剩余秒数 | TUI: 更新倒计时 |
| `auth:login_success` | 登录成功 | `()` | 所有: 更新 UI 状态 |
| `auth:login_failed` | 登录失败/过期/取消 | `(reason: str)` | 所有: 显示失败原因 |
| `auth:logout_done` | 登出完成 | `()` | 所有: 清理 UI |
| `live:state_changed` | 直播状态变更 | `(is_live: bool, room_info: dict)` | 所有: 刷新直播面板 |
| `live:info_updated` | 房间信息刷新 | `(room_info: dict)` | 所有: 更新房间数据展示 |
| `danmaku:received` | 收到一条弹幕 | `(msg: DanmakuMessage)` | CLI: print; TUI: 追加到列表 |
| `danmaku:stopped` | 弹幕监听停止 | `()` | TUI: 更新按钮状态 |
| `error` | 任何未处理异常 | `(error: Exception)` | 所有: 错误提示/日志 |

**关键设计约束**：
- `_emit` 是同步调用，不等待回调完成
- 回调中不应抛异常（逻辑层不处理回调异常，用户层自行包裹）
- `_emit` 不作为公开 API，编排函数内部调用

#### 为什么选回调列表而非 Pub/Sub

| | 回调列表 (方案 A) | Pub/Sub (方案 B) |
|---|---|---|
| 代码量 | ~20 行 | ~80 行 |
| 依赖 | 无 | 可能需要引入第三方 |
| 功能 | 足够当前需求 | 过度设计 |
| 迁移兼容 | 保持 on/off 接口不变即可 | 内部重写 |

**迁移路径**：如果将来需要升级，只需修改 `session.py` 的内部实现，保持 `on()` / `off()` API 不变即可，logic 和用户层代码无需改动。

---

### 3.3 auth.py — 登录认证编排

#### 对外 API

```python
# 返回值: FuncResult
# 副作用: session._emit() 事件
# 注意: 这些函数不是 async，是可阻塞函数

auth_generate_qrcode(session) → FuncResult  # 生成二维码 URL 并 emit auth:qrcode_ready
auth_poll_login(session, timeout_sec=180) → FuncResult    # 轮询直到登录成功/超时/取消
auth_validate_login(session) → FuncResult                 # 验证当前登录有效性
auth_logout(session) → FuncResult                         # 登出
```

#### 登录流程

```
auth_generate_qrcode(session)
  ├── 调 api_get_qrcode_url_and_key(cookies=None) 得到 (url, qrcode_key)
  ├── qrcode_key 保存在函数局部变量中（不放入 session）
  └── 调 session._emit("auth:qrcode_ready", qr_url)
          └─→ CLI: print(generate_qr_text(qr_url))
          └─→ TUI: 在 widget 中渲染二维码

auth_poll_login(session, timeout=180)
  ├── 循环: 每 2 秒调 api_poll_qrcode_login(qrcode_key)  # key 从闭包/局部变量获取
  ├── 状态为"已扫码等待确认"时 emit "auth:login_polling", countdown
  ├── 状态为"确认成功"时:
  │   ├── 从返回结果中拿 cookies/token
  │   ├── 写入 session.config.cookies
  │   └── emit "auth:login_success"
  ├── 超时 → emit "auth:login_failed", "二维码已过期"
  └── 返回值: FuncResult(SUCCESS/FAIL, data={"cookies": ...})  # 给 CLI 同步用

auth_logout(session)
  ├── 调 api_logout(cookies)
  ├── 清除 session.config.cookies
  └── emit "auth:logout_done"
```

#### 中间状态管理

`qrcode_key` 不放入 session。auth.py 内部用以下方式之一管理：
- 函数返回一个包含 `key` 的上下文对象，调用方传入 `auth_poll_login(obj)`
- 或直接用嵌套函数/闭包，对外只暴露组合好的 `auth_login_flow(session)` 顶函数

**推荐**：`auth_generate_qrcode()` 返回的 `FuncResult` 的 `result` 字段携带 `qrcode_key`，`auth_poll_login` 接收这个 key 作为参数。

#### 二维码显示

所有用户层都使用 `lib.generate_qr_text(qr_url) → list[str]`：
- CLI：逐行 `print(line)` 或 `print("\n".join(lines))`
- TUI：在 `Label` 或 `RichLog` 中 monospace 渲染行列表

---

### 3.4 live.py — 直播管理编排

#### 对外 API

```python
live_start(session, area_id: int) → FuncResult         # 开播
live_stop(session) → FuncResult                        # 下播
live_update_title(session, new_title: str) → FuncResult # 修改直播标题
live_refresh_room_info(session) → FuncResult            # 刷新房间信息
live_get_room_info(session) → FuncResult                # 获取当前房间信息
```

#### 每个函数的内部流程

**`live_start`**:
1. 调 `select_room(session.config.room_id)` 或直接用 config 中的 room_id
2. 调 `select_area(area_id)` 选择分区
3. 调 `api_start_live(cookies, room_id, area_id)`
4. 成功 → 更新 `session.config` 中直播状态 → emit `live:state_changed(True, room_info)`
5. 返回 `FuncResult`

**`live_stop`**:
1. 调 `api_stop_live(cookies, room_id)`
2. 成功 → emit `live:state_changed(False, room_info)`
3. 返回 FuncResult

**`live_update_title`**:
1. 调 `api_update_live_title(cookies, room_id, new_title)`
2. 成功 → emit `live:info_updated(room_info)`
3. 返回 FuncResult

**`live_refresh_room_info`** / **`live_get_room_info`**:
1. 调 `api_get_room_data(cookies, room_id)` 获取房间数据
2. emit `live:info_updated(room_info)`
3. 返回 FuncResult （含完整房间数据，供 CLI 展示/用户层缓存）

#### 设计要点

- 所有 API 调用前检查 `session.config.cookies` 是否有效
- 如果 live 操作返回 API 未登录/过期错误，emit `error` 事件并返回 FAIL
- live 操作不对 cookies 做刷新（那是 auth 的职责）

---

### 3.5 danmaku.py — 弹幕处理编排

#### 背景：B 站弹幕 WebSocket 协议

这是整个系统中最复杂的部分。B 站弹幕使用自定义二进制协议：

1. **连接**：通过 HTTPS API 获取 WebSocket URL 和认证 token
2. **握手**：WebSocket 连接后发送认证包
3. **维持**：每 30 秒发送心跳包
4. **接收**：持续接收二进制消息，解包后得到弹幕数据

服务端发来的消息有多种类型：人气值更新、弹幕消息、系统通知等。`lib.unpack_ws_message` 负责解包和分类。

#### 对外 API

```python
danmaku_start(session) → FuncResult    # 启动弹幕监听（非阻塞，启动后台任务）
danmaku_stop(session) → FuncResult     # 停止弹幕监听
```

#### 关于 asyncio 的问题

`websockets` 库本身是异步的（所有操作都需要 `await`），所以 **无法完全避免 asyncio**。但策略如下：

| 场景 | 是否显式引入 asyncio | 替代方案 |
|------|-----|------|
| `danmaku.py` 内部 | **必须**，因为 `websockets` 要求 async | 尽可能少用——只用于 await 和 create_task |
| TUI 用户层 | **不需要** | 用 Textual 的 `self.run_worker(danmaku_start)` |
| CLI 用户层 | **需要一次** | 用 `asyncio.run(danmaku_start(session))` |

**设计目标**：用户层代码（cli/、tui/）**尽可能不 import asyncio**。TUI 层借 Textual 自身的事件循环；CLI 层只有一处 `asyncio.run()`，其余都是同步调用。

#### danmaku.py 内部实现设计

```python
# danmaku.py 伪代码（不是实际代码，只描述流程）

async def _listen_loop(session):
    """
    内部函数：完整的弹幕监听生命周期。
    此函数是 async，因为要 await websockets 操作。
    """
    try:
        # 1. 获取弹幕信息（HTTP 请求，同步函数即可）
        result = get_danmaku_info(session.config.cookies, session.config.room_id)
        danmaku_ws_url = result["ws_url"]
        danmaku_key = result["key"]

        # 2. 连接 WebSocket
        ws = await get_danmaku_websocket(danmaku_ws_url)

        # 3. 发送认证
        auth_result = await ws_send_auth(
            ws, session.config.user_id, session.config.room_id, danmaku_key
        )
        if not auth_result.success:
            session._emit("error", auth_result.error)
            return

        # 4. 启动心跳后台任务
        heartbeat_task = asyncio.create_task(_heartbeat_loop(ws, session))

        # 5. 持久接收弹幕
        async for result in ws_listen_danmaku(ws):
            if result.success:
                for msg in result.data:  # data 是 DanmakuMessage 列表
                    session._emit("danmaku:received", msg)
        # 注意：ws_listen_danmaku 修好 bug 后会在断开时 yield ERROR

    except Exception as e:
        session._emit("error", e)
    finally:
        heartbeat_task.cancel()
        await ws.close()
        session._emit("danmaku:stopped")


async def _heartbeat_loop(ws, session):
    """每 30 秒发送心跳包"""
    while True:
        await asyncio.sleep(30)
        await ws_send_heart(ws)


def danmaku_start(session) -> FuncResult:
    """启动弹幕监听。返回 FuncResult 指示任务是否成功创建。"""
    # 关键：这个函数是同步的，由用户层调用
    # 但内部需要创建后台异步任务
    # 利用 Textual 的 run_worker 或手动 asyncio.create_task
    ...

def danmaku_stop(session) -> FuncResult:
    """停止弹幕监听"""
    ...
```

#### 与用户层的集成方式

**TUI 层**（Textual）：
```python
# widget.py 中
def on_mount(self):
    # Textual 内部已经在 asyncio 事件循环中
    # self.run_worker() 轻松创建后台任务
    self.run_worker(danmaku._listen_loop(self.session))
```
Textual 层**不需要 import asyncio**。

**CLI 层**：
```python
# cli/danmaku.py 中
def handle_danmaku(args):
    # CLI 层只在入口有一处 asyncio.run
    asyncio.run(danmaku._listen_loop(session))
    # 其余代码都是同步的
```
CLI 层**只在 danmaku 命令处有一行 asyncio.run**。

#### 已知风险与注意事项

1. **WebSocket 断连**：网络问题导致 ws 断开会由 `websockets` 库抛异常，`_listen_loop` 的 `except` 块捕获。此时 emit `danmaku:stopped` 和 `error`，由用户层决定是否重连。

2. **heartbeat_task 泄漏**：`finally` 中 `cancel()` 确保心跳任务不会泄漏。但如果 `cancel()` 抛异常呢？heartbeat 内部套一层 try/except CancelledError 保护。

3. **并发停止**：如果用户在监听中途调用 `danmaku_stop`，通过一个 `asyncio.Event` 或标志位通知 `_listen_loop` 优雅退出。需要在 session 上保存一个 `_danmaku_stop_event`。

4. **状态防重**：`danmaku_start` 调用前检查是否已有在运行的监听任务（通过 session 上的标志位），防止重复启动。

5. **资源清理**：确保任何退出路径都会 close ws 和 cancel heartbeat。

#### danmaku.py 模块内 asyncio 使用清单

| asyncio 用法 | 位置 | 必要性 |
|---|---|---|
| `async def _listen_loop` | danmaku.py 内部 | ✅ websockets 要求 |
| `await ws.send()` | _listen_loop | ✅ websockets 要求 |
| `async for` | _listen_loop | ✅ websockets 要求 |
| `asyncio.create_task()` | _listen_loop 启动心跳 | ✅ 唯一方式 |
| `asyncio.sleep(30)` | _heartbeat_loop | ✅ 非阻塞等待 |
| `asyncio.Event` | 停止信号 | ✅ 优雅退出的最简方式 |
| **其他** | **不需要** | — |

共 ~5 处 `asyncio` 使用，全部局限在 `danmaku.py` 内部。

---

## 四、用户层设计

### 4.1 CLI 模式 (src/cli/)

```
src/cli/
├── __init__.py           # run_cli() 入口：解析命令，分发到各命令模块
├── commands/
│   ├── auth.py           # login / logout / status 命令
│   ├── live.py           # start / stop / title / info 命令
│   └── danmaku.py        # listen 命令
└── display.py            # 格式化输出工具（PrintFuncResult, PrintQRCode 等）
```

#### CLI 层规范
- **同步调用 logic 函数**，获取 FuncResult 后解析
- 每个 logic 函数的**返回值通道**给 CLI 用（事件通道 CLI 不监听）
- `danmaku listen` 是唯一使用 `asyncio.run()` 的地方
- `display.py` 提供统一的 FuncResult 打印格式
- 登录流程由 `auth.py` 的函数组合而成：`qr_url = gen_qrcode()` → `print_qr` → `poll_login()`

### 4.2 TUI 模式 (src/tui/)

```
src/tui/
├── __init__.py
├── app.py                # Textual App 子类，持有 session，挂载主屏幕
├── app.css               # TUI 层专属的 CSS 样式
├── screens/
│   ├── main.py           # 主界面布局（侧边导航 + 内容区切换）
│   └── quit.py            # 退出确认弹窗
└── widgets/
    ├── login.py           # 登录页（二维码渲染 + 状态提示）
    ├── live.py            # 直播操控页（开播/下播/改标题按钮 + 房间信息展示）
    ├── danmaku.py          # 弹幕页（实时弹幕列表）
    └── left_panel.py      # 侧边导航栏
```

#### TUI 层规范
- `app.py` 中实例化 `session`，传递给各 screen/widget
- Widget 的 `on_mount()` 中通过 `session.on("事件", self.callback)` 注册回调
- 回调中更新 Widget 的 UI（`self.refresh()` 或 Textual 的响应式属性）
- 弹幕监听通过 `self.run_worker()` 启动（不 import asyncio）
- CSS 常量 **仅在此层**定义，不放在 `utils/constant.py`

#### 与 utils/constant.py 的关系
- `TUIColors` 中的颜色字符串（`"#00a1d6"` 等）可以从 `constant.py` 引用
- CSS 选择器名（如 `#header`, `.left-panel`）只在 TUI 层定义
- `constant.py` 中删除 `CCS_APP`、`CCS_MAIN_SCREEN` 等 CSS 常量引用

---

## 五、入口分发 (__main__.py)

```python
# 伪代码示例
def main():
    args = parse_args()
    session = Session(Config.load())

    if args.mode == "cli":
        from src.cli import run_cli
        run_cli(session, args.command)
    elif args.mode == "tui":
        from src.tui import run_tui
        run_tui(session)
    else:
        print_help()
```

cli 和 tui 的 `run_*` 函数都是**独立入口**，彼此不交叉导入。

---

## 六、数据流总结

### 登录数据流

```
CLI 用户输入 "login"
  → cli/auth.py: auth_generate_qrcode(session)
    → logic/auth.py: api_get_qrcode_url_and_key()
    → 返回 (url, key)，key 由 auth.py 内部持有
    → emit("auth:qrcode_ready", url)
      → CLI: 捕获返回值中的 url，print QR
      → TUI: 在 on_mount 注册的回调中收到 url，渲染 QR 到 widget
  → cli/auth.py: auth_poll_login(session, key, timeout=180)
    → 循环轮询直到成功/失败
    → emit("auth:login_success")
      → CLI: 返回成功后 print "登录成功"
      → TUI: 回调中切换到直播页
```

### 弹幕数据流

```
用户（CLI 或 TUI 按钮）触发 "开始监播弹幕"
  → cli: asyncio.run(danmaku_start(session))
  → tui: self.run_worker(danmaku._listen_loop(session))
    → danmaku.py:
      1. HTTP 获取 ws_url + danmaku_key
      2. WebSocket 连接
      3. 发送认证包
      4. 启动心跳 Task
      5. 循环: ws_listen_danmaku → yield DanmakuMessage
          → 每次收到弹幕: emit("danmaku:received", msg)
            → CLI: 在 _listen_loop 中 print(msg)
            → TUI: 回调中 widget.append(msg)
      6. 连接断开 → emit("danmaku:stopped")
```

---

## 七、错误处理策略

### 三层各自的错误职责

| 层 | 处理方式 |
|---|---|
| 基础层 (utils) | 遇到错误返回 `FuncResult(type=FAIL/ERROR, error=exception)`。不 print，不 log |
| 逻辑层 (logic) | 将基础层错误向上传递。对业务级错误（如"未登录而操作直播"）主动检查并返回 FAIL。重大异常 emit `"error"` |
| 用户层 (cli/tui) | 消费 FuncResult 的 type 字段。FAIL → 显示错误信息给用户，ERROR → 显示+记录日志 |

### 特殊错误处理

- **登录过期**（API 返回 code=-101）：live.py 在操作前检查，如果发现过期则 emit `"error"` + 引导用户重新登录
- **WebSocket 断开**：danmaku.py 捕获异常后 emit `"danmaku:stopped"`，用户层可提供"重连"按钮
- **配置损坏**：session 初始化时校验 CONFIG，不合法则提示用户重新配置

---

## 八、迁移路径

| 当前状态 | 目标 | 如何迁移 |
|---------|------|---------|
| 回调列表 (方案 A) | Pub/Sub (方案 B) | 只改 session.py 内部，保持 on/off 接口不变 |
| 用户层 import session | logic 层持有 session | 入口创建 session 后注入到各 logic 函数 |
| CSS 常量在 utils | CSS 常量在 TUI | 移动定义，删除 utils/constant.py 中的引用 |
| UI widgets 无逻辑绑定 | widgets 订阅事件 | widget.on_mount() 中注册回调 |
| 只有一个 BiliLiveTool.py 入口 | __main__.py 分发 | 创建新入口，保留旧的作为过渡 |

---

## 九、不做的事情（防止过度设计）

1. ~~不引入第三方 Pub/Sub 库（如 `pypubsub`, `blinker`）~~ — 回调列表足够
2. ~~不抽象"命令模式"~~ — logic 函数就是命令，不需要再包装一层
3. ~~不搞插件系统~~ — 当前不需要动态加载
4. ~~logic 层不做 async 除了 danmaku~~ — auth 和 live 保持同步
5. ~~不引入依赖注入框架~~ — 手动传 session 参数即可

---

## 十、重构实施建议顺序

1. **修复基础层 6 个 bug** — 底层不稳，上层白搭
2. **清理 constant.py** — 移除 CSS 常量引用
3. **实现 logic/session.py** — 状态 + 事件系统
4. **实现 logic/auth.py** — 登录编排（含中间状态独立）
5. **实现 logic/live.py** — 直播编排
6. **实现 logic/danmaku.py** — 弹幕编排（asyncio 仅限此模块）
7. **创建 __main__.py** — 入口分发
8. **实现 CLI 层** — 从逻辑层返回值通道消费
9. **重构 TUI 层** — 从逻辑层事件通道消费
10. **集成测试** — 确保 CLI 和 TUI 都能正常工作

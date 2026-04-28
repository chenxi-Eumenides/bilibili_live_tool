# bilibili_live_tool 项目说明

> **最后更新**: 2026-04-28
> **当前分支**: `dev`
> **用途**: 后续任务统一参考，避免重复探索项目

---

## 一、项目概述

基于 **Textual** 框架的 B 站直播终端工具（TUI+CLI），支持开播/下播、修改标题/分区、查看直播间弹幕等功能。

| 项目 | 内容 |
|------|------|
| 名称 | bili_live_tool |
| 版本 | 0.4.5 |
| Python | >=3.9 |
| 构建 | uv + pyinstaller |
| 入口 | `uv run bili` → `src.BiliLiveTool:main` |

---

## 二、开发要求记录

以下是所有已提出的开发要求，每次新要求需追记于此以保持对齐：

| 编号 | 日期 | 来源 | 要求 | 状态 |
|------|------|------|------|------|
| R01 | 2026-04-28 | 用户 | 完成 TUI 层开发，重新实现（非从老版本复制） | 🔶 开发中 |
| R02 | 2026-04-28 | 用户 | TUI 开发计划放在 `plan/` 文件夹下 | ✅ 已完成 |
| R03 | 2026-04-28 | 用户 | 更新：每个小功能单独分支，严格"分支→开发→测试→合并"循环，不允许多功能或整个阶段一次开发 | 🔶 待执行 |
| R04 | 2026-04-28 | 用户 | 边框边距只在需要的地方设置，不过度使用 | 🔶 开发中 |
| R05 | 2026-04-28 | 用户 | 界面以黑色为主要颜色，终端风格 | 🔶 开发中 |
| R06 | 2026-04-28 | 用户 | 字体易读清晰，但不变更已有的弹幕颜色定义 | 🔶 开发中 |
| R07 | 2026-04-28 | 用户 | 代码风格适配现有规范（常量放 constant.py、库函数放 lib.py） | 🔶 开发中 |
| R08 | 2026-04-28 | 用户 | 生成项目说明文件，后续任务不用重复探索 | ✅ 已完成 |
| R09 | 2026-04-28 | logic-design | `live_update_room` area_id 参数使用 `area_v2` 属性 | ✅ 已修复 |
| R10 | 2026-04-28 | logic-design | `unpack_ws_message` ver=3 支持（`_member_map_` 名值混淆修复） | ✅ 已修复 |
| R11 | 2026-04-28 | logic-design | `ws_listen_danmaku` 静默退出改为 yield ERROR | ✅ 已修复 |
| R12 | 2026-04-28 | logic-design | `ws_send_auth` 吞 ConnectionClosedError 修复 | ✅ 已修复 |
| R13 | 2026-04-28 | logic-design | `lib.py` 裸 raise 改为具体 FUNC_DATA_ERROR | ✅ 已修复 |
| R14 | 2026-04-28 | logic-design | Logic 层使用 mock 测试不依赖网络；API 层集成测试不污染真实 config | ✅ 规范已建立 |
| R15 | 2026-04-28 | logic-design | 退出时保存配置：仅登录态有效时通过 `finally` 块保存 | ✅ 已实现 |
| R16 | 2026-04-28 | 用户 | 每个小功能在单独分支开发，遵循"分支→开发→测试→合并"循环 | 🔶 待执行 |
| R17 | 2026-04-28 | 用户 | TUI 开发不运行现有单元测试（单元测试仅覆盖 logic 层），验证仅用 ruff + LSP | 🔶 待执行 |

---

## 三、三层架构

```
┌────────────────────────────────────────────────────┐
│                    入口分发                         │
│         src/BiliLiveTool.py (总入口)                │
│         按 cli/tui 导出的 FLAGS 匹配分发            │
├──────────────┬─────────────────┬───────────────────┤
│   用户层     │    CLI 模式     │    TUI 模式       │
│ (View)       │  src/cli/ ✅    │  src/tui/ 🔶      │
│              │  同步调用       │  事件订阅驱动      │
├──────────────┴─────────────────┴───────────────────┤
│                    逻辑层                           │
│  src/logic/  ✅  auth / live / danmaku / session   │
│              Session 持有状态 + 事件系统            │
├────────────────────────────────────────────────────┤
│                    基础层                           │
│  src/utils/  ✅  api / lib / data / error / config │
│              纯函数式，零状态                       │
└────────────────────────────────────────────────────┘
```

### 核心原则
- 基础层纯函数，零状态，不 import 上层模块
- 逻辑层持有 Session 状态，通过 `FuncResult` 返回 + `SessionEvent` 事件双通道通知
- 用户层只 import 逻辑层，不直接 import 基础层（入口文件除外）
- CLI 和 TUI 各自导出 `FLAGS`、`run()`、`help_lines()`

---

## 四、各层模块清单

### 4.1 基础层 `src/utils/`

| 文件 | 职责 | 关键导出 |
|------|------|---------|
| `constant.py` | 常量定义 | `VERSION`, `ApiData`, `ApiUrl`, `SessionEvent`, `BiliCode`, `Tuning`, `TUIColors`, `DanmakuColors`, `KeyBindings` |
| `config.py` | 配置数据类 | `CONFIG` (dataclass, v1/v2 格式) |
| `lib.py` | 工具函数 | `sign_data`, `generate_qr_text`, `pack_ws_body`, `unpack_ws_message`, `encWbi`, `hmac_sha256`, `random_cooldown` |
| `data.py` | 数据结构 | `FuncResult`, `DanmakuMessage`, `GiftMessage`, `NoticeMessage`, `STATUS`, `LiveAreaList`, `AppState`, `ApiResult` |
| `error.py` | 错误类型 | `FuncType`, `FAIL`, `API_BILI_CODE_ERROR`, `FAIL_BILI_CODE` |
| `api.py` | API 调用 | `api()`, `api_with_sign()`, `ws_listen_danmaku` |

### 4.2 逻辑层 `src/logic/`

| 文件 | 职责 | 关键导出 |
|------|------|---------|
| `session.py` | 状态管理 | `Session` (持有 CONFIG，事件系统 `on/off/once/_emit`) |
| `auth.py` | 登录认证 | `auth_generate_qrcode`, `auth_poll_login`, `auth_validate_login`, `auth_logout` |
| `live.py` | 直播管理 | `live_start`, `live_stop`, `live_update_room`, `live_refresh_room_info`, `live_get_area_list` |
| `danmaku.py` | 弹幕监听 | `danmaku_start`, `danmaku_stop`, `_listen_loop` |

### 4.3 用户层 - CLI `src/cli/`

| 文件 | 职责 | 状态 |
|------|------|------|
| `main.py` | CLI 入口，解析 --login --live --title --area --danmaku --cli | ✅ |

### 4.4 用户层 - TUI `src/tui/`

| 文件 | 职责 | 状态 |
|------|------|------|
| `main.py` | CLI 入口 (FLAGS/run/help_lines) | ✅ |
| `app.py` | BiliLiveToolApp | ✅ |
| `app.tcss` | 全局样式 | ⚠️ 基础 |
| `screens/main.py` | MainScreen 主界面 | ✅ |
| `screens/main.tcss` | 主界面样式 | ⚠️ 基础 |
| `screens/quit.py` | QuitScreen 退出确认 | ✅ |
| `screens/quit.tcss` | 退出对话框样式 | ✅ |
| `widgets/left_panel.py` | LeftPanel 左侧导航 | ✅ |
| `widgets/login.py` | LoginPage 扫码登录 | ⚠️ 部分 |
| `widgets/live.py` | ActionPage 直播操作 | ⚠️ 部分 |
| `widgets/info.py` | InfoPage 信息展示 | ⚠️ 部分 |
| `widgets/danmaku.py` | DanmuPage 弹幕显示 | ⚠️ 部分 |

---

## 五、事件系统

### SessionEvent 事件列表

```
AUTH_QRCODE_READY     — 二维码生成完成
AUTH_LOGIN_POLLING    — 每次轮询
AUTH_LOGIN_SUCCESS    — 登录校验成功
AUTH_LOGIN_FAILED     — 登录失败/过期
AUTH_LOGOUT_DONE      — 登出完成

LIVE_STATE_CHANGED    — 开播/下播状态变更
LIVE_INFO_UPDATED     — 房间信息变更
LIVE_FACE_AUTH_REQUIRED — 需要人脸认证

DANMAKU_RECEIVED      — 收到弹幕消息（传入 DanmakuMessage 对象）
DANMAKU_STOPPED       — 弹幕监听停止

ERROR                 — 异常错误
```

### 事件订阅模式
```python
# Widget on_mount 中订阅
session = self.app.session
session.on(SessionEvent.LIVE_INFO_UPDATED, self._on_info_updated)

# 回调签名
def _on_info_updated(self, data=None):
    ...
```

---

## 六、代码规范

### 6.1 导入规范
- 最小导入：`from xxx import a, b`，不用 `import xxx`
- 函数内禁止导入（除特殊情况）
- 相对导入项目内模块：`from ..logic import Session`
- 通过 `ruff F401` 检查（无未使用导入）

### 6.2 文档格式
```python
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

### 6.3 常量管理
- 可复用常量 → `src/utils/constant.py` 对应类中
- 模块私有常量 → 模块内

### 6.4 分层规则
| 层 | 可依赖 | 不可依赖 |
|----|------|---------|
| utils | 标准库+第三方 | logic/cli/tui |
| logic | utils | cli/tui, 不直接调 api() |
| cli/tui | logic | utils/api.py |

---

## 七、数据流

### 逻辑函数返回模式
```python
result = live_start(session, area_id=123)
if result.type == FuncType.SUCCESS:
    data = result.result  # 成功数据
else:
    print(f"失败: {result.result}")  # 错误信息
```

### Session 属性
| 属性 | 说明 |
|------|------|
| `session.is_logged_in` | 是否已登录（通过 API 验证） |
| `session.user_id` | B站 UID |
| `session.room_id` | 直播间号 |
| `session.config` | CONFIG 实例 |
| `session.config.room_data` | 房间信息字典 |
| `session.danmaku_room_id` | 弹幕监听目标房间号 |

---

## 八、配置文件格式

### config.json (v2)
```json
{
    "version": 2,
    "user": { "uid": 0, "cookies_str": "...", "csrf": "", "refresh_token": "", "refresh_time": 0 },
    "live": { "room_id": 0, "title": "", "area_id": 0, "rtmp_addr": "", "rtmp_code": "" },
    "data": { "room": {...}, "area": [...] },
    "app": { "default_mode": "help" }
}
```

---

## 九、关键数据结构

### FuncResult
```python
@dataclass(frozen=True)
class FuncResult:
    type: FuncType  # SUCCESS | FAIL | ERROR
    result: Any     # 成功时是数据，失败时是错误信息
```

### DanmakuMessage（弹幕消息）
- 属性：`uname`, `uid`, `msg`, `timestamp`, `privilege_type`, `medal_name`, `color`, `badge_text`
- 方法：`format_rich()` → 返回 Rich markup 格式化文本
- 方法：`.type` → `UserDanmakuType` 枚举

---

## 十、当前模块进度

| 模块 | 状态 | 备注 |
|------|------|------|
| utils/api | ✅ | B站 API（HTTP + WebSocket） |
| utils/lib | ✅ | 签名/编解码/WS封包/二维码 |
| utils/data | ✅ | FuncResult/DanmakuMessage 等数据结构 |
| utils/error | ✅ | 错误类型 + FAIL_BILI_CODE |
| utils/config | ✅ | CONFIG v1/v2 自动识别 |
| utils/constant | ✅ | 所有常量聚合 |
| logic/session | ✅ | Session 状态 + 事件系统 |
| logic/auth | ✅ | 扫码登录全流程 |
| logic/live | ✅ | 开播/下播/改标题/改分区/刷新 |
| logic/danmaku | ✅ | 弹幕监听（同步准备+异步循环） |
| CLI | ✅ | 全部命令可用 |
| TUI | 🔶 开发中 | 详见 `tui-layer-design-spec.md` |
| 单元测试 (logic) | ✅ | 47 个测试通过 |
| 单元测试 (API) | 🔶 | 需真实 config |

### 已完成的关键修复

以下修复已完成，后续开发需注意不被破坏：

| 修复项 | 说明 |
|--------|------|
| `api_update_room` area_id 参数 | 修正为使用 `config.area_v2` 属性 |
| `unpack_ws_message` ver=3 | 支持 Brotli 压缩协议（`_member_map_` 名值混淆修复） |
| `ws_listen_danmaku` 静默退出 | 改为 yield ERROR，不再静默吞错 |
| `ws_send_auth` ConnectionClosedError | 捕获处理，不抛异常 |
| `lib.py` 错误类型 | 裸 raise 改为具体 `FUNC_DATA_ERROR` |

---

## 十一、Test 与构建

### 11.1 测试
```bash
python -m unittest unittest.all_test      # 全部测试
python -m unittest unittest.test_src_logic # 仅 logic 层
```
- Logic 层使用 mock，不依赖网络
- API 层需要真实 `unittest/config.json`
- 测试不得污染真实 `config.json`

### 11.2 构建
```bash
uv sync                     # 安装依赖
uv sync --group build       # 安装构建依赖
uv run --group build pyinstaller ...  # 打包
```

### 11.3 代码检查
```bash
ruff check src/
```

---

## 十二、依赖

| 包 | 版本 | 用途 |
|----|------|------|
| textual | >=7.3.0 | TUI 框架 |
| rich | 15.0.0 (传递) | 富文本渲染 (textual 依赖) |
| requests | >=2.32.3 | HTTP 请求 |
| websockets | >=15.0.1 | WebSocket (弹幕连接) |
| brotli | >=1.2.0 | Brotli 解压 |
| qrcode | >=8.2 | 二维码生成 |

---

## 十三、plan 文件夹文档索引

| 文件 | 说明 |
|------|------|
| `logic-layer-design-spec.md` | 逻辑层开发规格书（已完成的 utils + logic + CLI 设计） |
| `tui-layer-design-spec.md` | TUI 层开发规格书（当前开发计划） |
| `project-overview.md`（本文件） | 项目整体说明，后续任务统一参考 |

---

## 十四、Git 分支策略

```
master  ← 稳定发布版
  └── dev  ← 开发主分支（当前）
        └── feat/tui  ← TUI 功能开发分支
```

- 新功能在独立功能分支开发
- 完成后 PR 合并到 dev
- 合并后删除功能分支

# AGENTS.md — 项目速览与开发规范

## 一句话定位

B 站直播终端工具（Textual TUI + CLI），支持扫码登录、开播/下播、改标题/分区、弹幕监听。

## 快速启动

```bash
uv run bili --help          # 帮助（会触发 TUI import，待修）
uv run python -m src.cli --help   # CLI 直接入口
uv run python -m src.cli --status # 查看状态
ruff check src/                   # 代码检查（cli/logic 应零错误）
```

## 三层架构

```
utils/       基础层 ✅  纯函数零状态（api, lib, data, error, config, constant）
logic/       逻辑层 ✅  Session + 事件系统（auth, live, danmaku）
cli/         用户层 ✅  事件驱动 + 异步（main, auth, live, danmaku）
tui/         用户层 🔶  待适配（app, layout/, panels/）
```

**铁律**：用户层只 import logic，不直接 import utils。

## 开发基线

- **方向**：自下而上（基础层→逻辑层→用户层）
- **当前**：基础层 ✅ → 逻辑层 ✅ → CLI ✅ → **TUI 🔶 下一步**

## 分支策略

```
master  — 正式版代码
tui     — 正式版开发分支
cli     — 旧版 CLI（历史版本，保留）
dev     — 重构版开发分支（当前）
```

规则：每个小功能 `feat/xxx` 从 `dev` 分叉→合并回。大型任务 `dev-xxx` → 子任务 → 合并回。

## 关键规则（违反 = 不合格）

### 导入
- **最小导入**：`from xxx import a, b`，禁止 `import xxx`
- 所有 import 在文件顶部，禁止函数内导入
- 用户层用相对导入：`from ..logic import Session`

### 事件
- 事件名**必须用** `SessionEvent.XXX` 常量，禁止裸字符串
- 每个 logic 函数 `return` 前**必须** `session._emit()` 对应事件
- CLI handler 用 `session.once()` 订阅事件接收结果，不检查 `FuncResult.type`

### Session
- 持久化数据存 `CONFIG`，临时数据存 `Session`
- 缓存字段用 `cache_` 前缀（`cache_qr_url`, `cache_danmaku_key` 等）

### 类型安全
- **禁止** `as any`、`@ts-ignore`、`@ts-expect-error`

### 提交
- 原子 commit，一个功能一个提交
- 消息格式：`类型: 中文简述`
- 破坏性操作前**必须**用 `question` 工具确认

## 核心文件索引

| 文件 | 职责 |
|------|------|
| `src/utils/constant.py` | 所有常量（`SessionEvent`, `BiliCode`, `ApiUrl` 等）|
| `src/utils/config.py` | 持久化配置 `CONFIG`（v3 格式）|
| `src/logic/session.py` | 状态中心 + `on/off/once/_emit` |
| `src/logic/auth.py` | 登录流程（QR→轮询→成功/失败）|
| `src/logic/live.py` | 开播/下播/改标题/分区/状态刷新 |
| `src/logic/danmaku.py` | 弹幕 WS 连接 + 监听 + 心跳 |
| `src/cli/main.py` | CLI 入口：argparse + async dispatch |
| `src/cli/auth.py` | `handle_login` |
| `src/cli/live.py` | `handle_live_start/stop/status/update/area/cli` |
| `src/cli/danmaku.py` | `handle_danmaku` |

## 文档索引

| 文件 | 说明 |
|------|------|
| `plan/architecture-spec.md` | 架构设计规格书 |
| `plan/project-overview.md` | 代码结构文档 |
| `plan/development-standards.md` | 开发规范与要求记录 |

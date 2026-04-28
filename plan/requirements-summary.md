# 开发要求总结

> 来源于整个开发会话 + `plan/` 下设计文档。分三级整理，越往下越通用。

---

## 第一级：本项目专属要求

### 1.1 架构

- 三层不可逾越：`utils`（零状态）→ `logic`（持有 Session）→ `cli/tui`（用户层）
- 用户层不直接调用 `src/utils/api.py` 中的函数，只通过 logic 层
- CLI 和 TUI 各自导出 `FLAGS`、`run()`、`help_lines()`，总入口 `BiliLiveTool.py` 据此分发
- 事件驱动优先：能用 `SessionEvent` 通信的不用返回值
- `room_id` 只在登录成功时获取一次（`auth_post_login`），其他 logic 函数不再重复获取

### 1.2 状态管理

- `Session` 持有全局状态：`is_logged_in`、`room_id`、`config`、事件系统
- TUI 的 `app_state` 由 `Session` 驱动：初始加载 config → 后台验证登录 → 设置 UNAUTH/IDLE/LIVE/REPLAY
- 登录轮询由 `app.py` 管理（`run_worker(thread=True)` + `threading.Event` 停止），不受 AuthPanel 生命周期影响
- 登录成功后自动调用 `auth_post_login` → 获取 room_id、房间信息、分区列表、保存 config

### 1.3 界面（TUI）

- 深色终端主题：背景 `#1a1a1a`，强调 `#00a1d6`，面板 `#2a2a2a`
- 弹幕颜色（`DanmakuColors`）不得修改
- 只在需要的地方设置 `padding`/`margin`，不过度使用
- Textual 的 `align` 将多个子元素视为整体块居中，窄元素会左对齐。正确做法：每个子元素用 `Center` 容器包裹
- Header 状态指示：圆点 `●` + 颜色（红未登录/绿已登录/蓝直播中/黄轮播中）+ 文字
- 版本号从 `constant.VERSION_STR` 获取
- 二维码缓存存 `qr_url` + `qr_key`（不存文本），需要时调用 `generate_qr_text(qr_url)` 生成

### 1.4 代码组织

- 常量放 `src/utils/constant.py` 对应类中，模块私有常量留在模块内
- 库函数放 `src/utils/lib.py`
- Docstring 格式：Google Style（Args/Returns/Events/Raises）

### 1.5 配置

- `config.json` 自动识别 v1/v2 格式
- 读取前先判断文件是否存在

### 1.6 分支策略

- 每个独立功能/修复在单独分支开发，完成后合并回 dev，删除功能分支
- 粒度：一个分支一个功能，不允许多功能或整阶段一次开发
- TUI 开发不运行现有单元测试（仅覆盖 logic 层），验证靠 `ruff` + LSP 诊断

---

## 第二级：Python 通用要求

### 2.1 导入规范

| 规则 | 示例 |
|------|------|
| 最小导入 | `from xxx import a, b` ✓ / `import xxx` ✗ |
| 函数内禁止导入 | 所有 import 在文件顶部 |
| 无未使用导入 | `ruff F401` 检查 |
| 相对导入 | 项目内用 `from ..logic import Session` |
| 删除 `from __future__ import annotations` | Python 3.13 原生支持 `X \| None` |

### 2.2 线程安全

- 后台线程中的 UI 更新用 `self.app.call_from_thread(lambda: ...)` 包装
- `call_from_thread` 必须从非主线程调用
- 参数求值在调用线程中执行 → `self.query_one()` 不可在 `call_from_thread` 参数中直接求值，放 lambda 内
- `time.sleep(2)` 无法中断 → 用 `threading.Event.wait(timeout=2)`，设置 event 后立即返回

### 2.3 事件驱动

- 优先通过事件（`session.on/off/_emit`）而非返回值获取状态
- 事件名用类常量管理（如 `SessionEvent.AUTH_LOGIN_SUCCESS`）
- 跨线程事件需 `call_from_thread` 将 UI 操作切回主线程

### 2.4 同步 vs 异步

- 同步 HTTP 调用（`requests`）在后台线程中运行，避免阻塞主事件循环
- 用 `asyncio.to_thread(func, *args)` 或 `run_worker(thread=True)` 将同步函数放到线程池

---

## 第三级：通用编程要求

### 3.1 AI 协作

| 规则 | 说明 |
|------|------|
| 不要自己选方案 | 提供多个方案，让用户决定，不要擅自选 |
| 按序执行 | 先有详细设计文档，再开发 |
| 不要提前实现 | 只做被要求的事，不擅自开始 |
| 不要自作主张删用户代码 | 删除前确认哪些是用户有意保留的 |
| 不要盲目扩散修复 | 找到根因后再改，不要加多层 hack |

### 3.2 设计与开发

- 一个功能一个分支，严格"分支→开发→验证→合并→删分支"循环
- 测试只测相关模块，不运行无关测试
- CSS/样式：自适应宽度（`min-width` + `max-width` + 百分比），不设死固定值
- 文件读取前先判断存在性
- 注释/docstring：只在必要时加（公共 API、复杂逻辑），代码自解释优先

### 3.3 错误处理

- `try/except Exception: pass` 吞异常可掩盖 bug，谨慎使用
- 跨线程 UI 更新失败时用 try/except 兜底，防止线程卡死

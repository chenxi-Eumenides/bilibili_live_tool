# bilibili_live_tool 开发规范

> **规范文档** — 项目层级规则、Python 通用规范、AI 协作约定
> 给开发工具（Agent）使用，保持信息密度
> **最后更新**: 2026-04-29
> ❗ = 必须遵守（违反 = 不合格），其余为用到再查

---

## 一、开发要求记录

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
| R18 | 2026-04-29 | 用户 | 分支工作流：小任务从 dev 分叉合并回 dev；大型任务从 dev 分叉 dev-xxx，其上再分叉子任务分支，全部完成后 dev-xxx→dev | ✅ |

---

## 二、项目专属规范

### ❗ 2.1 架构约束

- 三层不可逾越：`utils`（零状态）→ `logic`（持有 Session, 管理状态）→ `cli/tui`（用户层）
- 用户层不直接调用 `src/utils/api.py` 中的函数，只通过 logic 层
- CLI 和 TUI 各自导出 `FLAGS`、`run()`、`help_lines()`，总入口 `BiliLiveTool.py` 据此分发
- 事件驱动优先：能用 `SessionEvent` 通信的不用返回值
- 不变动的数据只在登录成功时获取一次，其他 logic 函数不再重复获取，保证对数据的最大化复用

### 2.2 状态管理

- `Session` 持有全局状态：`config`、事件系统
- TUI 的 `app_state` 由 `Session` 驱动：初始加载 config → 后台验证登录 → 设置 UNAUTH/IDLE/LIVE/REPLAY
- 登录轮询由 `app.py` 管理，不受 AuthPanel 生命周期影响

### 2.3 界面（TUI）

- 深色终端主题：背景 `#1a1a1a`，强调 `#00a1d6`，面板 `#2a2a2a`
- 弹幕颜色（`DanmakuColors`）不得修改
- 只在需要的地方设置 `padding`/`margin`，不过度使用
- Textual 的 `align` 将多个子元素视为整体块居中，窄元素会左对齐。正确做法：每个子元素用 `Center` 容器包裹
- Header 状态指示：圆点 `●` 颜色（红未登录/绿已登录/蓝直播中/黄轮播中）+ 文字
- 版本号从 `constant.VERSION_STR` 获取
- 二维码缓存存 `qr_url` + `qr_key`，需要时调用 `generate_qr_text(qr_url)` 生成
- CSS/样式：自适应宽度（`min-width` + `max-width` + 百分比），不设死固定值

### ❗ 2.4 代码组织

- 常量放 `src/utils/constant.py` 对应类中，模块私有常量留在模块内
- 库函数放 `src/utils/lib.py`
- 结构放 `src/utils/data.py`
- api 放 `src/utils/api.py`
- 错误及错误信息放 `src/utils/error.py`
- 需要持久化保存的数据由 `config` 管理
- 不需要持久化的数据由 `session` 管理
- Docstring 格式：Google Style（Args/Returns/Events/Raises）

### 2.5 配置

- `config.json` 自动识别 v1/v2/v3 格式
- 读取前先判断文件是否存在

### ❗ 2.6 分支策略

```
master → dev（主开发分支）
            ├── feat/xxx        # 单个小任务分支
            └── dev-xxx         # 大型任务集成分支（用连字符，因 dev 已是分支名）
                    └── feat/xxx # 大型任务下的子任务分支
```

#### 单个小任务工作流
1. 从 `dev` 分叉 `feat/<任务名>` 分支
2. 在 `feat/xxx` 上完成开发
3. 合并回 `dev`，删除分支

#### 大型任务工作流（由多个小任务组成）
1. 从 `dev` 分叉 `dev-<任务名>` 集成分支（注意用连字符）
2. 从 `dev-xxx` 分叉子任务分支 `feat/<子任务>`（可多个并行）
3. 子任务完成后逐个合并回 `dev-xxx`
4. 全部子任务完成后，将 `dev-xxx` 合并回 `dev`
5. 删除 `dev-xxx` 及其所有子任务分支

#### 当前分支状态

```
dev（主开发分支）
  └── TUI 层待适配
```

> 所有开发严格遵循上述分支工作流。

---

## 三、Python 通用规范

### ❗ 3.1 导入规范

| 规则 | 示例 |
|------|------|
| 最小导入 | `from xxx import a, b` ✓ / `import xxx` ✗ |
| 函数内禁止导入 | 所有 import 在文件顶部 |
| 无未使用导入 | `ruff F401` 检查 |
| 相对导入 | 项目内用 `from ..logic import Session` |
| 不用 `from __future__ import annotations` | Python 3.10 以上原生支持 `X \| None` |

### 3.2 线程安全

- 后台线程中的 UI 更新用 `self.app.call_from_thread()` 包装
- `call_from_thread` 必须从非主线程调用
- 参数求值在调用线程中执行 → `self.query_one()` 不可在 `call_from_thread` 参数中直接求值，放 lambda 内
- `time.sleep(2)` 无法中断 → 用 `threading.Event.wait(timeout=2)`，设置 event 后立即返回

### ❗ 3.3 事件驱动

- 优先通过事件（`session.on/off/_emit`）而非返回值获取状态
- 事件名用类常量管理（如 `SessionEvent.AUTH_LOGIN_SUCCESS`），**禁止裸字符串**
- 跨线程事件需 `call_from_thread` 将 UI 操作切回主线程
- 每个 logic 函数 `return` 前必须 `session._emit()` 对应事件

### ❗ 3.4 类型安全

- **禁止** `as any`、`@ts-ignore`、`@ts-expect-error`

### ❗ 3.5 提交规范

- 原子 commit，一个功能一个提交
- 消息格式：`类型: 中文简述`
- 破坏性操作前必须用 `question` 工具确认

### 3.6 同步 vs 异步

- 同步 HTTP 调用（`requests`）在后台线程中运行，避免阻塞主事件循环
- 用 `asyncio.to_thread(func, *args)` 或 `run_worker(thread=True)` 将同步函数放到线程池

### 3.7 错误处理

- `try/except Exception: pass` 吞异常可掩盖 bug，谨慎使用
- 跨线程 UI 更新失败时用 try/except 兜底，防止线程卡死

---

## 四、AI 协作规范

### 4.1 交互规则

| 规则 | 说明 |
|------|------|
| 不要自己选方案 | 提供多个方案，让用户决定，不要擅自选 |
| 按序执行 | 先有详细设计文档，再开发 |
| 不要提前实现 | 只做被要求的事，不擅自开始 |
| 不要自作主张删用户代码 | 删除前确认哪些是用户有意保留的 |
| 不要盲目扩散修复 | 找到根因后再改，不要加多层 hack |

### 4.2 设计与开发

- 一个功能一个分支，严格"分支→开发→验证→合并→删分支"循环
- 测试只测相关模块，不运行无关测试
- 文件读取前先判断存在性
- 注释/docstring：只在必要时加（公共 API、复杂逻辑），代码自解释优先

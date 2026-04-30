# AGENTS.md — 项目速览与新 Agent 导航

## 一句话定位

B 站直播终端工具（Textual TUI + CLI），支持扫码登录、开播/下播、改标题/分区、弹幕监听。

## 快速启动

```bash
uv run python -m src.cli --help     # CLI 入口
uv run python -m src.cli --status   # 查看状态
ruff check src/cli/ src/logic/      # 代码检查（cli/logic 应零错误）
```

## 你需要读哪些文档

| 优先级 | 文件 | 用途 |
|:---:|------|------|
| 1 | `docs/development-standards.md` | **先读这个** — 所有开发规范（违反 = 不合格）|
| 2 | `docs/architecture-spec.md` | 架构设计理解 |
| 3 | `docs/project-overview.md` | 代码索引（用到再看）|

## 三层架构（必须遵守）

```
utils/ → logic/ → cli/tui/
```

**铁律**：用户层只 import 逻辑层，不直接 import utils。

## 分支策略

```
master（正式版） → tui（正式版开发） → cli（历史版本）
                 → dev（重构版开发，**当前工作**）
```

- 小任务：`dev` → `feat/xxx` → 合并回 `dev`
- 大任务：`dev` → `dev-xxx` → `feat/子任务` → 合并回 `dev-xxx` → 合并回 `dev`

## 关键规则速查

| 规则 | 违反后果 |
|------|---------|
| `from xxx import a, b`，禁止 `import xxx` | 不合格 |
| 事件名用 `SessionEvent.XXX`，禁裸字符串 | 不合格 |
| 每个 logic return 前 `session._emit()` | 不合格 |
| 禁止 `as any` / `@ts-ignore` | 不合格 |
| 原子 commit，破坏性操作前 `question` 确认 | 不合格 |

> 完整规则见 `docs/development-standards.md`

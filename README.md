# bilibili_live_tool

一个基于 Textual 的 B站直播终端工具，用于绕过B站直播姬，直接获取推流码。

## 声明

本程序仅用于声明的功能，用户使用本程序产生的账号问题，与本程序无关。请勿用于不当用途。

## 软件功能

- [x] 开播/下播
- [x] 获取直播间信息
- [x] 获取rtmp推流地址与推流码
- [x] 修改直播间标题、分区
- [x] 获取直播间弹幕
- [ ] 获取直播间礼物、进场信息等

## 使用方法

### 运行exe

下载软件，双击程序运行。

- [releases](https://github.com/chenxi-Eumenides/bilibili_live_tool/releases/latest)
- [蓝奏云(CN)](https://wwzt.lanzoul.com/b00zxtbjrg)  密码:chenxi

### 运行源码

```bash
# 克隆仓库
git clone https://github.com/chenxi-Eumenides/bilibili_live_tool.git
cd bilibili_live_tool

# 安装依赖
uv sync

# 运行
uv run -m src.main
```

## 开发

### 分支说明

- `master`: 主分支，与release保持一致。当前为tui。
- `tui`: TUI 开发分支，**请 PR 到该分支**。
- `cli`: 旧版 CLI 分支，不再进行开发，仅用于修复。
- `dev`: 彻底的重构版本，同时支持 TUI 与 CLI，乃至后续的更多前端界面。正在重构中。

### TUI 分支说明

#### 文件结构

```bash
src
├── main.py                       <- 入口文件，启动 Textual 应用
├── build.py                      <- PyInstaller 打包入口
├── static/
│   └── bili-icon.ico             <- 应用图标
│
├── core/                         <- 业务逻辑层
│   ├── auth.py                   <- 登录管理（二维码登录、状态检测、凭证刷新）
│   ├── config.py                 <- 配置管理（读写 config.json）
│   ├── danmaku_fetcher.py        <- 弹幕 WebSocket 客户端（自动重连、故障转移）
│   ├── danmaku_handler.py        <- 弹幕消息处理器
│   ├── danmaku_models.py         <- 弹幕数据模型
│   ├── danmaku_protocol.py       <- 弹幕 WebSocket 协议常量与工具
│   ├── danmaku_wbi.py            <- WBI 签名算法
│   └── live.py                   <- 直播操作（开播、下播、信息查询、标题/分区修改）
│
├── ui/                           <- 用户界面层 (Textual)
│   ├── app.py                    <- BiliLiveApp 主类及全局状态管理
│   ├── layout/                   <- 布局组件
│   ├── panels/                   <- 面板组件
│   ├── screen/                   <- 全屏模式
│   └── styles/                   <- Textual CSS 样式
│
└── utils/                        <- 工具层（无状态，纯函数）
    ├── constants.py              <- 全局常量（版本、API端点、快捷键、颜色）
    ├── crypto.py                 <- 加密/签名（API 请求签名）
    ├── cleanup.py                <- 资源清理
    └── lib.py                    <- 工具函数库（终端检测 is_modern_terminal）
```

## 致谢

1. bilibili_live_stream_code项目 [ChaceQC/bilibili_live_stream_code](https://github.com/ChaceQC/bilibili_live_stream_code)
2. bilibili-API-collect项目 [SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect/)
3. StartLive项目 [Radekyspec/StartLive](https://github.com/Radekyspec/StartLive)
4. blivedm项目 [xfgryujk/blivedm](https://github.com/xfgryujk/blivedm)

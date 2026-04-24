# bilibili_live_tool

一个基于 Textual 的 B 站直播终端工具（TUI），支持开播/下播、修改标题/分区、查看直播间弹幕等功能。

## 声明

本程序仅用于声明的功能，用户使用本程序产生的账号问题，与本程序无关。

## 安装/运行

### 二进制文件

[releases](https://github.com/chenxi-Eumenides/bilibili_live_tool/releases/latest)

[蓝奏云(CN)](https://wwzt.lanzoul.com/b00zxtbjrg)  密码:chenxi

双击程序运行。

### 源码运行

```bash
# 克隆仓库
git clone https://github.com/chenxi-Eumenides/bilibili_live_tool.git
cd bilibili_live_tool

# 安装依赖
uv sync

# 运行 TUI 程序
uv run -m src.main
```

## 致谢

1. bilibili_live_stream_code项目 [ChaceQC/bilibili_live_stream_code](https://github.com/ChaceQC/bilibili_live_stream_code)
2. bilibili-API-collect项目 [SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect/)
3. StartLive项目 [Radekyspec/StartLive](https://github.com/Radekyspec/StartLive)
4. blivedm项目 [xfgryujk/blivedm](https://github.com/xfgryujk/blivedm)

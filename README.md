# bilibili_live_tool (CLI)

命令行版 B 站直播工具，支持开播/下播、修改标题/分区等功能。

## 声明

本程序仅用于声明的功能，用户使用本程序产生的账号问题，与本程序无关。

## 安装/运行

### 源码运行

```bash
# 克隆仓库并切换到 cli 分支
git clone https://github.com/chenxi-Eumenides/bilibili_live_tool.git
cd bilibili_live_tool
git checkout cli

# 安装依赖
uv sync

# 运行 CLI 程序
uv run -m src.main
```

## 致谢

1. bilibili_live_stream_code项目 [ChaceQC/bilibili_live_stream_code](https://github.com/ChaceQC/bilibili_live_stream_code)
2. bilibili-API-collect项目 [SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect/)
3. StartLive项目 [Radekyspec/StartLive](https://github.com/Radekyspec/StartLive)
4. blivedm项目 [xfgryujk/blivedm](https://github.com/xfgryujk/blivedm)

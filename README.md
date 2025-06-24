# bilibili_live_tool
B站开播与下播工具

本程序用于快捷开启直播、结束直播、修改直播标题、修改直播分区
第一次双击exe，会生成使用说明，以及4个快捷方式。之后可以运行bat快捷方式快速启动。

近期B站网络抽风，可能不是软件问题。

## 声明

本程序仅用于获取推流地址以及推流码，不会封号等等，任何与账号有关的问题概不负责。

## 安装

### 二进制文件

[releases](https://github.com/chenxi-Eumenides/bilibili_live_tool/releases/latest)

[蓝奏云(CN)](https://wwzt.lanzoul.com/b00zxtbjrg)  密码:chenxi

双击运行。

### 源码

```bash
# 下载库
git clone https://github.com/chenxi-Eumenides/bilibili_live_tool.git
# 安装依赖
uv sync
# 运行脚本
uv run main.py
# alpha版本请手动修改脚本
# 扫码登录
```

## 使用方法

### 手动开播&下播
此选项手动选择分区、输入标题、确认开播&下播

### 自动开播&下播
此选项根据已保存的配置文件，自动开播&下播。需要手动启动一次后才能正常工作

### 修改直播标题
只修改直播标题

### 修改直播分区
只修改直播分区

## 命令行参数
```bash
bili-live.exe <ARGS>
ARGS:
         : 无参数则手动选择功能
  auto   : 自动选择上次的分区与标题，并开播/下播
  start  : 手动选择分区与标题，并开播/下播
  select : 更改分区
  title  : 更改标题
  info   : 获取直播间信息
  help   : 打印帮助信息
```

## 致谢

bilibili_live_stream_code项目 (https://github.com/ChaceQC/bilibili_live_stream_code)

bilibili-API-collect项目 (https://github.com/SocialSisterYi/bilibili-API-collect/)


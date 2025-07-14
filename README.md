# bilibili_live_tool

B站开播、下播、获取推流码工具

本程序用于开启直播、结束直播、获取推流码、修改直播标题、修改直播分区。


## 声明

本程序仅用于获取推流地址、推流码以及开播、下播，不会封号等等，任何与账号有关的问题概不负责。

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

双击exe文件或快捷方式，根据提示输入。

第一次双击exe，会生成使用说明，以及4个快捷方式。之后可以运行bat快捷方式快速启动。

请在出现 ***按回车结束程序 或 直接关闭窗口*** 后关闭程序。

如果bat快捷方式报错，请删除后重新运行exe文件。

如果报错“远程主机强迫关闭了一个现有的连接”，这是因为请求频繁，请稍等几分钟再试。

## 快捷方式

**手动开播&下播.bat**: 手动选择分区、输入标题、确认开播&下播。

**自动开播&下播.bat**: 根据已保存的配置文件，自动开播&下播。需要手动启动一次并保存配置文件后才能正常工作。

**修改直播标题.bat**: 只修改直播标题。

**修改直播分区.bat**: 只修改直播分区。

## 命令行参数

```bash
bili-live-tool.exe <ARGS>
ARGS:
         : 无config.json为manual，否则为auto
  auto   : 自动选择上次的分区与标题，并开播/下播
  manual : 手动选择分区与标题，并开播/下播
  area   : 更改分区
  title  : 更改标题
  info   : 仅打印直播间信息
  help   : 打印帮助信息
```

## 致谢

bilibili_live_stream_code项目 (https://github.com/ChaceQC/bilibili_live_stream_code)

bilibili-API-collect项目 (https://github.com/SocialSisterYi/bilibili-API-collect/)

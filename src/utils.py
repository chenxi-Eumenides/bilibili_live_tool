from os import path
from sys import argv, exit

import requests
import subprocess
import platform

# tuple[int, int, int, str, int]
# 0.0.1 (0, 0, 1)
# V0.0.1-alpha-1 (0, 0, 1, "alpha", 1)
version = (0, 3, 5)


def get_version() -> str:
    if len(version) == 3:
        return f"V{version[0]}.{version[1]}.{version[2]}"
    else:
        return f"V{version[0]}.{version[1]}.{version[2]}-{version[3]}-{version[4]}"


def get_help_content() -> list[str]:
    """
    获取帮助信息

    Returns:
        list[str] -- 帮助信息列表
    """
    return [
        "# 使用说明",
        "",
        "本程序用于快捷开启直播、结束直播、修改直播标题、修改直播分区",
        "第一次双击exe，会生成本说明，以及4个快捷方式。之后可以运行bat快捷方式快速启动。",
        "",
        "近期B站网络抽风，可能不是软件问题。",
        "",
        f"当前版本 {get_version()}",
        "",
        "## 使用方法",
        "",
        "### 手动开播&下播",
        "此选项手动选择分区、输入标题、确认开播&下播",
        "",
        "### 自动开播&下播",
        "此选项根据已保存的配置文件，自动开播&下播。需要手动启动一次后才能正常工作",
        "",
        "### 修改直播标题",
        "只修改直播标题",
        "",
        "### 修改直播分区",
        "只修改直播分区",
        "",
        "## 命令行参数",
        "         : 无参数，视为 manual",
        "  auto   : 自动选择上次的分区与标题，并开播/下播",
        "  manual : 手动选择分区与标题，并开播/下播",
        "  area   : 更改分区",
        "  title  : 更改标题",
        "  info   : 仅打印直播间信息",
        "  help   : 打印帮助信息",
        "",
        "## 致谢",
        "",
        "bilibili_live_stream_code项目 (https://github.com/ChaceQC/bilibili_live_stream_code)",
        "",
        "bilibili-API-collect项目 (https://github.com/SocialSisterYi/bilibili-API-collect/)",
        "",
        "## 作者",
        "",
        "chenxi_Eumenides (https://github.com/chenxi-Eumenides)",
    ]


def print_help():
    """
    打印帮助信息
    """
    for line in get_help_content():
        log(line)


def log(string: str, reason: int = -1, error_data: any = None, func=None):
    """
    打印输出

    :param string: 输出字符串
    :param reason: 报错id, defaults to -1
    :param error_data: 报错信息, defaults to None
    """
    if reason == -1:
        print(string)
    elif reason == 0:
        pass
    else:
        if error_data is None:
            s = f"{string}"
        else:
            s = f"{string}\n报错原因：{str(error_data)}"
        print(s)
        exit(reason)



def startfile(filepath):
    """
    跨平台打开文件

    :param filepath: 文件路径
    """
    if platform.system() == "Windows":
        os.startfile(filepath) 
    elif platform.system() == "Darwin":
        subprocess.call(('open', filepath))
    else:
        subprocess.call(('xdg-open', filepath))


def check_readme(config_file: str):
    if ".exe" not in argv[0]:
        return False
    if is_exist(config_file):
        return False
    content = "\n".join(get_help_content())
    with open("使用说明.txt", "w", encoding="utf-8") as f:
        f.writelines(content)
    startfile("使用说明.txt") 
    return True


def check_bat() -> bool:
    """
    检查快捷脚本是否已创建

    Returns:
        bool -- 是否已创建
    """
    if ".exe" not in argv[0]:
        return False

    def create_bat(bat: str, arg: str) -> bool:
        if not is_exist(bat):
            content = [
                "@echo off\n",
                f'if not exist "%~dp0{path.basename(argv[0])}" exit /b\n',
                f'"%~dp0{path.basename(argv[0])}" "{arg}"\n',
                "pause\n",
            ]
            with open(bat, "w", encoding="ansi") as f:
                f.writelines(content)
            return False
        else:
            return True

    return all(
        [
            create_bat("自动开播&下播.bat", "auto"),
            create_bat("手动开播&下播.bat", "manual"),
            create_bat("更改分区.bat", "area"),
            create_bat("更改标题.bat", "title"),
        ]
    )


def is_exist(file) -> bool:
    """
    文件是否存在

    Arguments:
        file {str} -- 文件路径

    Returns:
        bool -- 是否存在
    """
    return path.exists(file)


def post(url: str, params=None, cookies=None, headers=None, data=None):
    try:
        res = requests.post(
            url=url, params=params, cookies=cookies, headers=headers, data=data
        )
    except ConnectionResetError as e:
        log(f"请求api({url})过多，请稍后再尝试。", 1, str(e))
    except Exception as e:
        log(f"请求api({url})出错", 1, str(e))
    else:
        if res.status_code != 200:
            log(f"请求api({url})出错，状态码为{res.status_code}", 2)
    return res


def post_json(
    url: str, params=None, cookies=None, headers=None, data=None
) -> dict | list:
    res = post(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res.status_code == 200:
        return res.json()


def get(url: str, params=None, cookies=None, headers=None, data=None):
    try:
        res = requests.get(
            url=url, params=params, cookies=cookies, headers=headers, data=data
        )
    except Exception as e:
        log(f"请求api({url})出错", 1, str(e))
        return None
    else:
        if res.status_code != 200:
            log(f"请求api({url})出错，状态码为{res.status_code}", 2)
    return res


def get_json(
    url: str, params=None, cookies=None, headers=None, data=None
) -> dict | list:
    res = get(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res.status_code == 200:
        return res.json()


def get_cookies(url: str, params=None, cookies=None, headers=None, data=None) -> dict:
    res = get(url=url, params=params, cookies=cookies, headers=headers, data=data)
    return res.cookies.get_dict()

#!python
import json
from os import path
from sys import argv, exit
from time import sleep

from qrcode import QRCode
from requests import get, post

# 全局变量
self_file: str = argv[0]
config_file: str = "config.json"
log_file: str = "log.txt"
log_list: list[str] = []
log_flag: bool = False
# 配置文件中可读
room_id: int = -1
partition_id = -1
cookie_str: str = ""
cookie_new: str = ""
csrf: str = ""
# 每次重新获取
title = ""
rtmp_addr = ""
rtmp_code = ""
last_rtmp_code = ""
partition: dict = {}
room_data: dict = {}

# 配置数据

start_data = {
    "room_id": "",
    "platform": "android_link",
    "area_v2": "624",
    "backup_stream": "0",
    "csrf_token": "",  # 填csrf
    "csrf": "",  # 同 csrf_token
}

stop_data = {
    "room_id": "",
    "platform": "android_link",
    "csrf_token": "",  # 填csrf
    "csrf": "",  # 同 csrf_token
}

title_data = {
    "room_id": "",
    "platform": "android_link",
    "title": "",
    "csrf_token": "",  # 填csrf
    "csrf": "",  # 同 csrf_token
}

id_data = {
    "room_id": "",
    "area_id": 642,
    "activity_id": 0,
    "platform": "android_link",
    "csrf_token": "",  # 填csrf
    "csrf": "",  # 同 csrf_token
}

user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

header = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://link.bilibili.com",
    "referer": "https://link.bilibili.com/p/center/index",
    "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": user_agent,
}


def get_cookies() -> dict:
    """
    获取cookies
    """
    if path.exists(config_file):
        read_config()
    else:
        login()
    # cookies转换为json
    cookies = json.loads(cookie_str)
    return cookies


def read_config():
    global room_id
    global cookie_str
    global csrf
    global partition_id
    global title
    global rtmp_addr
    global last_rtmp_code
    global partition
    global room_data
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        log("读取config.json失败，重新登录")
        login()
    else:
        room_id = config.get("room_id", -1)
        partition_id = config.get("partition_id", -1)
        cookie_str = config.get("cookie", "")
        csrf = config.get("csrf", "")
        title = config.get("title", "")
        rtmp_addr = config.get("rtmp_addr", "")
        last_rtmp_code = config.get("rtmp_code", "")
        partition = config.get("partition", {})
        room_data = config.get("room_data", {})
    if room_id == -1 or cookie_str == "" or csrf == "":
        log("config.json内容不正确，重新登录")
        login()


def login():
    """
    获取cookies
    """
    global cookie_str
    global cookie_new

    cookies = login_new()

    if cookies:
        set_room_id_and_csrf(cookies)
        cookie_str = json.dumps(cookies, separators=(",", ":"), ensure_ascii=False)
    else:
        log("cookies获取失败，请重新尝试", 16)


def login_new():
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    data = get(url, headers={"User-Agent": user_agent}).json()["data"]
    qr_url = data["url"]
    qr_key = data["qrcode_key"]

    qr = QRCode(border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr.make_image().show()
    status = (False, {})
    while status[1] == {}:
        status = login_check(qr_key, status)
        sleep(1)
    return status[1]


def login_check(qr_key, status: tuple[bool, dict]) -> tuple[bool, dict]:
    try:
        login_requests = qr_login(qr_key)
        login_data = login_requests.json()
    except Exception:
        log("登录连接错误！", 17)
    else:
        code = login_data["data"]["code"]

        if code == 0:
            cookie = login_requests.cookies.get_dict()
            return (True, cookie)
        elif code == 86038:
            log("二维码已失效，请重新启动软件", 18)
        elif code == 86090:
            if not status[0]:
                log("二维码已扫描，等待确认")
                status = (True, {})
    return status


def set_room_id_and_csrf(cookies: dict):
    """
    获取room_id和csrf
    :param cookies: cookies
    :return: 一个元组，按顺序包含room_id和csrf
    """
    global room_id
    global csrf

    dede_user_id = cookies.get("DedeUserID")
    url = (
        f"https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid={dede_user_id}"
    )

    try:
        response = get(url, headers={"User-Agent": user_agent})
        data = response.json()
    except Exception as e:
        log("获取room_id失败！", 15, str(e))
    else:
        if data["code"] == 0:
            room_id = data["data"]["room_id"]
    csrf = cookies.get("bili_jct")


def qr_login(qrcode_key: str):
    """
    访问Bilibili服务器检查二维码扫描后的登录状态
    :param qrcode_key: 二维码秘钥
    :return: 返回查询响应
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    headers = {"User-Agent": user_agent}
    params = {"qrcode_key": qrcode_key}
    response = get(url, headers=headers, params=params)
    return response


def update_partition_list(cookies: dict):
    """
    更新直播分区列表
    :param cookies: 登录cookies
    :return: None
    """
    global partition
    try:
        resp = get(
            "https://api.live.bilibili.com/room/v1/Area/getList",
            cookies=cookies,
            headers=header,
        )
        pt_data = resp.json()
    except Exception as e:
        log("获取直播分区失败，错误如下\n", 14, str(e))

    results = []
    for root in pt_data.get("data"):
        part_results = []
        for part in root.get("list"):
            part_result = {"name": part.get("name"), "id": int(part.get("id"))}
            part_results.append(part_result)
        result = {
            "name": root.get("name"),
            "id": int(root.get("id")),
            "list": part_results,
        }
        results.append(result)

    """
    partition = [
        {
            "name":name,
            "id":id,
            "list":[
                {
                    "name":name,
                    "id":id,
                },
            ],
        },
    ]
    """
    partition = results


def get_root_partition() -> list[str]:
    """
    获取分区主题名字
    :return: 返回所有分区主题名字
    """
    results = []
    for data in partition:
        results.append(data.get("name"))
    return results


def get_partition(root_id: int) -> list[str]:
    """
    获取分区主题下的所有分区名字
    :param root_id: 分区主题id
    :return: 返回特定主题的所有分区的名字
    """
    results = []
    global partition
    for data in partition:
        if data.get("id") == root_id:
            for part in data.get("list"):
                results.append(part.get("name"))
            break
    return results


def get_partition_index(name: str = "", partition_id: int = 0) -> int:
    if name == "":
        log("搜索名称为空，请重新尝试！", 9)
    try:
        for part in partition:
            if partition_id == 0:
                if name in part.get("name"):
                    return part.get("id")
            else:
                if partition_id == part.get("id"):
                    for p in part.get("list"):
                        if name in p.get("name"):
                            return p.get("id")
    except Exception:
        pass
    if partition_id == 0:
        log("设置主分区失败，请重新尝试！", 10)
    else:
        log("设置子分区失败，请重新尝试！", 11)


def get_partition_name(id) -> tuple:
    if id <= 0 or id >= 1000:
        return ()
    for data in partition:
        for part in data.get("list"):
            if id == part.get("id"):
                return data.get("name"), part.get("name")
    return ()


def is_valid_id(id) -> bool:
    if id <= 0 or id >= 1000:
        return False
    for data in partition:
        for part in data.get("list"):
            if id == part.get("id"):
                return True
    return False


def set_partition_id(fast_id=0):
    global partition_id
    global start_data
    if is_valid_id(fast_id):
        start_data["area_v2"] = fast_id
        partition_id = fast_id
    else:
        print_max = 3
        id = 0
        while id <= 0:
            # 主分区
            print("请选择主分区：")
            root_partition = get_root_partition()
            for index, data in enumerate(root_partition):
                end = "\n" if index % 4 == print_max - 1 else " "
                print(f"{index + 1:2}: {data:<8}", end=end)
            print("\n请输入要选择的主分区 序号 或 名称：")
            select = input()
            while select == "":
                print("输入为空，重新输入主分区 序号 或 名称：")
                select = input()
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                select = get_partition_index(select)
            else:
                # 输入了序号
                select = get_partition_index(root_partition[select - 1])
            root_id = select

            # 子分区
            print("\n子分区：")
            child_partition = get_partition(root_id)
            for index, data in enumerate(child_partition):
                end = "\n" if index % 4 == print_max - 1 else " "
                print(f"{index + 1:>2}: {data:<6}", end=end)
            print("\n请输入要选择的子分区 序号 或 名称（回车重新选择主分区）：")
            select = input()
            if select == "":
                log("重新选择主分区")
                continue
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                select = get_partition_index(select, root_id)
            else:
                # 输入了序号
                select = get_partition_index(child_partition[select - 1], root_id)
            id = select
        start_data["area_v2"] = id
        partition_id = id
    name = get_partition_name(partition_id)
    log(f"当前选择分区为：{name[0]} {name[1]}")
    return partition_id


def set_live_title(cookies: dict, new_title=None):
    """
    设置直播间标题
    :param cookies: cookies
    """
    global title
    global title_data
    if new_title is None:
        log(f"\n当前标题为： {room_data.get('title')}")
        log("请输入标题，标题不得超过20字（直接回车为原标题）：")
        new_title = input()
        while len(new_title) > 20:
            log("标题不得超过20字，请重新输入（直接回车为原标题）：")
            new_title = input()
    else:
        if len(new_title) > 20:
            log("直播间标题太长", 18)
        elif new_title == "":
            return
    if len(new_title) != 0:
        url = "https://api.live.bilibili.com/room/v1/Room/update"
        title_data["title"] = new_title
        try:
            post(url, headers=header, cookies=cookies, data=title_data)
        except Exception as e:
            log("设置直播间标题失败", 13, str(e))
        title = new_title


def save_config():
    config = {
        "cookie": cookie_str,
        "csrf": csrf,
        "rtmp_addr": rtmp_addr,
        "rtmp_code": rtmp_code,
        "room_id": room_id,
        "partition_id": partition_id,
        "title": title,
        "room_data": room_data,
        "partition": partition,
    }
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log("保存config.json失败", 12, str(e))


def check_bat() -> bool:
    return all(
        [
            create_bat("自动开播&下播.bat", "auto"),
            create_bat("手动开播&下播.bat", "start"),
            create_bat("更改分区.bat", "select"),
            create_bat("更改标题.bat", "title"),
        ]
    )


def create_bat(file: str, arg: str) -> bool:
    if not path.exists(file):
        content = [
            "@echo off\n",
            f'if not exist "%~dp0{path.basename(self_file)}" exit /b\n',
            f'"%~dp0{path.basename(self_file)}" "{arg}"\n',
            "pause\n",
        ]
        with open(file, "w", encoding="ansi") as f:
            f.writelines(content)
        return False
    else:
        return True


def save_log():
    if log_flag and log_list:
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                for line in log_list:
                    f.write(line + "\n")
        except Exception:
            log("保存log文件失败")


def log(string: str, reason: int = 0, error: any = None):
    global log_list
    if reason == 0:
        print(string)
        log_list.append(f"{string}")
    else:
        if error is None:
            s = f"{string}"
        else:
            s = f"{string}\n报错原因：{str(error)}"
        print(s)
        if log_flag:
            log_list.append(s)
        save_config()
        save_log()
        input("输入回车关闭程序")
        exit(reason)


def get_live_data(cookies) -> int:
    global room_id
    global room_data
    if room_id > 0:
        try:
            response = post(
                "https://api.live.bilibili.com/room/v1/Room/get_info",
                cookies=cookies,
                headers=header,
                data={"room_id": room_id},
            )
        except Exception as e:
            log("获取直播间状态出错", 1, str(e))
        else:
            if response.status_code != 200 and response.json()["code"] != 0:
                log("获取直播间状态出错，不存在该直播间", 2)
            else:
                room_data = response.json().get("data")
                return room_data.get("live_status")
    log("获取直播间状态出错", 3)


def start_live(cookies):
    global rtmp_addr
    global rtmp_code
    # 获取直播推流码并开启直播
    try:
        response = post(
            "https://api.live.bilibili.com/room/v1/Room/startLive",
            cookies=cookies,
            headers=header,
            data=start_data,
        )
    except Exception as e:
        log("请求直播推流码时出错", 4, str(e))
    else:
        if response.status_code != 200 or response.json()["code"] != 0:
            log("获取推流码失败，cookie可能失效，请重新获取！", 5, response.json())
        else:
            rtmp = response.json()["data"]["rtmp"]
            rtmp_addr = rtmp["addr"]
            rtmp_code = rtmp["code"]


def stop_live(cookies):
    # 关闭直播
    try:
        post(
            "https://api.live.bilibili.com/room/v1/Room/stopLive",
            cookies=cookies,
            headers=header,
            data=stop_data,
        )
    except Exception as e:
        log("关闭直播时出错，请手动下播", 6, str(e))


def prepare(cookies) -> dict:
    global start_data
    global stop_data
    global title_data
    global id_data

    # 获取直播分区
    update_partition_list(cookies)

    # 设置信息
    start_data["room_id"] = room_id
    start_data["csrf_token"] = start_data["csrf"] = csrf
    stop_data["room_id"] = room_id
    stop_data["csrf_token"] = stop_data["csrf"] = csrf
    title_data["room_id"] = room_id
    title_data["csrf_token"] = title_data["csrf"] = csrf
    id_data["room_id"] = room_id
    id_data["csrf_token"] = id_data["csrf"] = csrf


def print_help():
    log("说明:")
    log("双击启用程序，可用于 开播/下播/选择分区/修改标题。")
    log("第一次使用会创建几个快捷脚本，之后可以使用快捷脚本。")
    log("近期B站网络抽风，可能不是软件问题。如果报错了，请联系我，嘻嘻")
    log("\n参数：")
    log("         : 无参数则手动选择功能")
    log("  auto   : 自动选择上次的分区与标题，并开播/下播")
    log("  start  : 手动选择分区与标题，并开播/下播")
    log("  select : 更改分区")
    log("  title  : 更改标题")
    log("  help   : 打印帮助信息")
    log("\n原作者：Chace (https://github.com/ChaceQC)")
    log("二改作者：chenxi (https://github.com/chenxi-Eumenides)")


def set_partition():
    cookies = get_cookies()
    prepare(cookies)
    set_partition_id()
    global id_data
    id_data["area_v2"] = partition_id
    try:
        response = post(
            "https://api.live.bilibili.com/room/v1/Room/update",
            cookies=cookies,
            headers=header,
            data=id_data,
        )
    except Exception as e:
        log("网络请求出错", 19, str(e))
    else:
        data = response.json()
        if data.get("code") == 0:
            log("更改分区成功！")
            save_config()
        else:
            log(f"更改分区({partition_id})失败,", 20, data.get("msg"))


def set_title():
    cookies = get_cookies()
    prepare(cookies)
    set_live_title(cookies)
    log("修改标题成功")
    save_config()


def reflesh():
    cookies = get_cookies()
    prepare(cookies)
    get_live_data(cookies)
    save_config()


def auto_main():
    log("自动选择\n")
    # 获取 cookies
    cookies = get_cookies()
    status = get_live_data(cookies)
    if status != 1:
        # 不在直播
        log("正在轮播" if status == 2 else "不在直播")
        prepare(cookies)
        set_partition_id(partition_id)
        set_live_title(cookies, "")
        start_live(cookies)
        if last_rtmp_code != rtmp_code:
            log("已开启直播间，推流码：\n")
            log(rtmp_code)
            log("\n复制以上内容，粘贴到 obs 的直播推流码中")
        else:
            log("已开启直播间，推流码无变化，请直接开播。")
            log(rtmp_code)
        save_config()
    elif status == 1:
        # 正在直播
        log("正在直播")
        prepare(cookies)
        stop_live(cookies)
        log("已结束直播")


def manual_main():
    # 获取 cookies
    cookies = get_cookies()
    status = get_live_data(cookies)
    if status != 1:
        # 不在直播
        log("正在轮播" if status == 2 else "不在直播")
        log("\n输入 y 或 Y 开启直播：")
        select = input()
        if select.upper() == "Y":
            prepare(cookies)
            set_partition_id()
            set_live_title(cookies)
            start_live(cookies)
            if last_rtmp_code != rtmp_code:
                log("\n已开启直播间，推流码：\n")
                log(rtmp_code)
                log("\n复制以上内容，粘贴到 obs 的直播推流码中")
            else:
                log("\n已开启直播间，推流码无变化，请直接开播。")
                log(rtmp_code)
        save_config()
    elif status == 1:
        # 正在直播
        log("正在直播\n")
        log("输入 y 或 Y 结束直播：")
        select = input()
        if select.upper() == "Y":
            prepare(cookies)
            stop_live(cookies)
            log("已结束直播")


def main():
    log("1 : 自动使用上次的设置开播/下播")
    log("2 : 手动输入分区和标题开播/下播")
    log("3 : 更改分区")
    log("4 : 更改标题")
    log("0 : 查看帮助信息")
    log("输入序号进入功能：")
    select = input()
    if select == "1":
        auto_main()
    elif select == "2":
        manual_main()
    elif select == "3":
        set_partition()
    elif select == "4":
        set_title()
    elif select == "0":
        print_help()
    else:
        log("未选择")


if __name__ == "__main__":
    if not check_bat():
        print_help()
    log("任何时候 按Ctrl+C 或 关闭窗口 退出程序\n")

    if len(argv) > 1:
        if argv[1] == "auto":
            auto_main()
        elif argv[1] == "start":
            manual_main()
        elif argv[1] == "select":
            set_partition()
        elif argv[1] == "title":
            set_title()
        elif argv[1] == "reflesh":
            reflesh()
        else:
            print_help()
            exit(0)
    else:
        main()

    log("\n按 回车 结束程序，或直接关闭窗口")
    input()

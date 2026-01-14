from sys import argv, exit

from src.bili_cli import Bili_Live
from src.bili_lib import wait_print


def help(live: Bili_Live):
    print(live.get_help_info())


def title(live: Bili_Live):
    live.set_live_title()
    pass


def area(live: Bili_Live):
    live.set_live_area()
    pass


def manual(live: Bili_Live):
    status = live.get_live_status()
    if status == 0 or status == 2:
        live.set_live_area()
        print("")
        live.set_live_title()
        print("")
        live.start_live()
        print("")
        live.get_rtmp()
    elif status == 1:
        live.stop_live()
    else:
        return False


def auto(live: Bili_Live):
    status = live.get_live_status()
    if status == 0 or status == 2:
        live.start_live()
        print("")
        live.get_rtmp()
    elif status == 1:
        live.stop_live()
    else:
        return False


def choose(options: list[callable]) -> callable:
    print("输入以下选项，手动选择：")
    print("0 自动开播")
    print("1 手动选择开播")
    print("2 更改分区")
    print("3 更改标题")
    print("4 获取帮助信息")
    try:
        i = int(input(" ："))
        if 0 <= i < len(options):
            return options[i]
    except KeyboardInterrupt:
        exit()
    except:
        return None


def nothing(live: Bili_Live):
    pass


if __name__ == "__main__":
    options = [auto, manual, area, title, help, nothing]
    option = None
    live = Bili_Live()
    try:
        live.login()
        print("")
        live.print_room_info()
        print("")
    except KeyboardInterrupt:
        exit()

    if len(argv) > 1:
        option = argv[1]
    elif wait_print(time=3, postfix="秒后自动开播，按 Enter 进入手动选择："):
        print("")
        option = choose(options)

    try:
        if option is not None:
            option(live)
        else:
            if not live.check_config():
                manual(live)
            else:
                auto(live)
    except KeyboardInterrupt:
        exit()
    except BaseException as e:
        print(f"出错了，报错信息：{e}")

from sys import argv
from time import sleep

from src.bili_cli import Bili_Live


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


def need_user_choose():
    try:
        print("3秒后，自动开播，按 Ctrl + C 进入手动选择：")
        sleep(3)
    except KeyboardInterrupt:
        return True
    return False


if __name__ == "__main__":
    options = ["auto", "manual", "area", "title", "help", "info"]
    option = None
    live = Bili_Live(config_file="config.json")
    live.login()

    print("")
    print(live.get_room_info())
    print("")

    if len(argv) > 1:
        option = argv[1]
    elif need_user_choose():
        print("输入以下选项，手动选择：")
        print("0 自动开播")
        print("1 手动选择开播")
        print("2 更改分区")
        print("3 更改标题")
        print("4 获取帮助信息")
        try:
            i = int(input(" ："))
            if 0 <= i < len(options):
                option = options[i]
        except:
            pass

    try:
        if option == "auto":
            auto(live)
        elif option == "manual":
            manual(live)
        elif option == "title":
            title(live)
        elif option == "area":
            area(live)
        elif option == "help":
            help(live)
        elif option == "info":
            pass
        else:
            if not live._config_.check_config():
                manual(live)
            else:
                auto(live)
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        print(f"出错了，报错信息：{e}")
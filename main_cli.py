from sys import argv

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


if __name__ == "__main__":
    live = Bili_Live(config_file="config.json")
    live.login()

    print("")
    print(live.get_room_info())
    print("")

    option = argv[1] if len(argv) > 1 else None
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
        if live._config_.check_config():
            auto(live)
        else:
            manual(live)

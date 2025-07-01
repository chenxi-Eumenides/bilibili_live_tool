from sys import argv

from src.bili import Bili_Live
from src.utils import log


def help(live: Bili_Live):
    log(live.get_help_info())


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
        live.set_live_title()
        live.start_live()
    elif status == 1:
        live.stop_live()
    else:
        return False


def auto(live: Bili_Live):
    status = live.get_live_status()
    if status == 0 or status == 2:
        live.start_live()
    elif status == 1:
        live.stop_live()
    else:
        return False


if __name__ == "__main__":
    live = Bili_Live(config_file="config.json")
    live.login()

    print("")
    log(live.get_room_info())
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
        manual(live)

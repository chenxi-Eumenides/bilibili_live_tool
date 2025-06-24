from bili import Bili_Live

if __name__ == "__main__":
    live = Bili_Live(config_file="config.json")

    live.login()
    if live.get_live_status() == 0:
        live.set_area("王者荣耀")
        live.set_live_title()
        live.start_live()
    elif live.get_live_status() == 1:
        live.stop_live()
    elif live.get_live_status() == 2:
        print("正在轮播")

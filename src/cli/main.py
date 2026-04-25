"""命令行入口

用法:
  bili --login                          扫码登录
  bili --live start [-a 分区ID]         开播
  bili --live stop                      下播
  bili --live status                    查看直播状态
  bili --title "新标题" [--area 分区ID]  改标题
  bili --area 分区ID [--title "新标题"]  改分区
  bili --danmaku                        弹幕监听
  bili --cli                            login + 自动开/下播
  bili --tui                            启动 TUI
  bili --set-default tui|cli|help       设置默认模式（占位）
  bili --help                           帮助
"""

from argparse import ArgumentParser, Namespace
from asyncio import run as asyncio_run
from rich import print
from sys import argv

from ..logic import (
    Session,
    _listen_loop,
    auth_generate_qrcode,
    auth_logout,
    auth_poll_login,
    auth_validate_login,
    live_get_area_list,
    live_refresh_room_info,
    live_start,
    live_stop,
    live_update_room,
    danmaku_start,
    danmaku_stop,
)
from ..utils.api import api_get_room_id
from ..utils.config import CONFIG
from ..utils.constant import CONFIG_FILE
from ..utils.data import FuncType
from ..utils.lib import generate_qr_text

CLI_FLAGS = frozenset({"--login", "--logout", "--live", "--title", "--area", "--danmaku", "--cli"})


def help_lines():
    return [
        "CLI 模式:",
        "  --cli                          login + 自动开/下播",
        "  --login                        扫码登录",
        "  --logout                       清除登录态",
        "  --live start [--area 分区ID] [--title 标题]  开播",
        "  --live stop                    下播",
        "  --live status                  查看状态",
        '  --title "标题" [--area 分区ID]   改标题',
        "  --area 分区ID [--title \"标题\"]  改分区",
        "  --area list                    列出主分区",
        "  --area list 主分区ID             列出子分区",
        "  --danmaku [直播间号]            弹幕监听 (默认: 自己的直播间)",
    ]


def _load_session() -> Session:
    config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
    session = Session(config)
    if session.config.cookies:
        result = auth_validate_login(session)
        if result.type == FuncType.SUCCESS:
            print(f"从 {CONFIG_FILE} 恢复登录 (uid={session.user_id})")
    return session


def _print_qr(qr_url: str) -> None:
    for line in generate_qr_text(qr_url):
        print(line)


def handle_login(session: Session) -> bool:
    if session.is_logged_in:
        print(f"已登录 (uid={session.user_id})，跳过登录")
        return True

    result = auth_generate_qrcode(session)
    if result.type != FuncType.SUCCESS:
        print(f"获取二维码失败: {result.result}")
        return False

    qr_url = result.result["qr_url"]
    qr_key = result.result["qr_key"]
    print("请使用B站App扫描以下二维码登录:\n")
    _print_qr(qr_url)

    print("\n等待扫码...")
    poll = auth_poll_login(session, qr_key)
    if poll.type == FuncType.SUCCESS:
        session.config.save_config()
        print(f"登录成功! uid={session.user_id}")
        return True

    print(f"登录失败: {poll.result}")
    return False


def handle_live_start(session: Session, args) -> None:
    area = int(args.area[0]) if args.area else session.config.area_id
    if area == 0:
        print("请使用 --area 指定分区ID，或先用 --area 保存到配置。")
        print("可用 --area list 查看分区列表。")
        return
    result = live_start(session, area_id=area)
    if result.type != FuncType.SUCCESS:
        print(f"开播失败: {result.result}")
        return
    data = result.result
    print(f"开播成功 (房间:{session.room_id})")
    if data.get("rtmp_addr"):
        print(f"推流地址: {data['rtmp_addr']}")
        print(f"推流码:   {data.get('rtmp_code','')}")
    if args.title:
        handle_update(session, args)
    elif args.area:
        handle_update(session, args)


def handle_live_stop(session: Session) -> None:
    result = live_stop(session)
    if result.type == FuncType.SUCCESS:
        print("下播成功")
    else:
        print(f"下播失败: {result.result}")


def handle_live_status(session: Session) -> None:
    refresh = live_refresh_room_info(session)
    if refresh.type != FuncType.SUCCESS:
        print(f"刷新失败: {refresh.result}")
        return
    data = session.config.room_data
    is_live = data.get("live_status")
    print(f"房间号: {data.get('room_id','?')}")
    print(f"标题:   {data.get('title','?')}")
    print(f"分区:   {data.get('area_name','?')} (id={data.get('area_id','?')})")
    print(f"状态:   {'直播中' if is_live else '未开播'}")
    if is_live:
        live_time = data.get("live_time", "00:00:00")
        if live_time and live_time != "0000-00-00 00:00:00":
            print(f"直播时长: {live_time}")
    online = data.get("online", 0)
    if online:
        print(f"当前观众: {online}")


def handle_update(session: Session, args) -> None:
    title = args.title
    area = args.area

    if area and area[0] == "list":
        result = live_get_area_list(session)
        if result.type != FuncType.SUCCESS:
            print(f"获取分区列表失败: {result.result}")
            return
        parent_id = int(area[1]) if len(area) > 1 else None
        for main in result.result:
            if parent_id is None:
                print(f"  [{main.id}] {main.name}")
            elif main.id == parent_id:
                print(f"  [{main.id}] {main.name}")
                for sub in main.list:
                    print(f"    [{sub.id}] {sub.name}")
        return

    area_id = int(area[0]) if area else None

    if title or area_id:
        r = live_update_room(session, title=title, area_id=area_id)
        if r.type == FuncType.SUCCESS:
            if title:
                print(f"标题已更新: {title}")
            if area_id:
                print(f"分区已更新: {area_id}")
        else:
            print(f"修改失败: {r.result}")


def handle_danmaku(session: Session, room_id: str | None = None) -> None:
    if room_id:
        session.danmaku_room_id = int(room_id)
        print(f"监听直播间: {session.danmaku_room_id}")
    else:
        print(f"监听自己的直播间: {session.room_id}")

    result = danmaku_start(session)
    if result.type != FuncType.SUCCESS:
        print(f"启动失败: {result.result}")
        return

    def on_received(msg):
        if hasattr(msg, "format_rich"):
            print(msg.format_rich())
        else:
            print(msg)

    session.on("danmaku:received", on_received)
    print("按两次 Ctrl+C 停止")
    try:
        asyncio_run(_listen_loop(session))
    except KeyboardInterrupt:
        pass
    finally:
        danmaku_stop(session)
        print("已停止")


def handle_cli(session: Session) -> None:
    if not handle_login(session):
        return
    if session.room_id == 0:
        print("正在获取房间号...")
        result = api_get_room_id(session.cookies, session.user_id)
        if result.type == FuncType.SUCCESS:
            session.config.room_id = result.result
            print(f"房间号: {session.room_id}")

    refresh = live_refresh_room_info(session)
    if refresh.type != FuncType.SUCCESS:
        print(f"获取房间状态失败: {refresh.result}")
        return
    rd = session.config.room_data
    if rd.get("area_id"):
        session.config.area_id = rd["area_id"]
    if rd.get("title"):
        session.config.title = rd["title"]
    is_live = rd.get("live_status")
    if is_live:
        print("当前正在直播")
    else:
        print("正在开播...")
        handle_live_start(session, Namespace(area=None, title=None))


def handle_logout(session: Session) -> None:
    result = auth_logout(session)
    print(result.result if result.type == FuncType.SUCCESS else f"登出失败: {result.result}")


def main():
    session = None
    try:
        session = _run()
    except KeyboardInterrupt:
        print()
    finally:
        if session and session.is_logged_in:
            session.config.save_config()


def _run():
    p = ArgumentParser(prog="bili", add_help=False)
    p.add_argument("--login", action="store_true")
    p.add_argument("--logout", action="store_true")
    p.add_argument("--live", choices=["start", "stop", "status"])
    p.add_argument("--area", nargs="*", default=None)
    p.add_argument("--title", type=str, default=None)
    p.add_argument("--danmaku", nargs="?", const="", default=None)
    p.add_argument("--cli", action="store_true")

    args = p.parse_args()

    if len(argv) == 1:
        p.print_help()
        return None

    session = None

    if args.login:
        session = _load_session()
        handle_login(session)
        return session

    if args.logout:
        session = _load_session()
        handle_logout(session)
        return session

    if args.live:
        session = _load_session()
        if args.live == "start":
            handle_live_start(session, args)
        elif args.live == "stop":
            handle_live_stop(session)
        elif args.live == "status":
            handle_live_status(session)
        return session

    if args.title or args.area:
        session = _load_session()
        handle_update(session, args)
        return session

    if args.danmaku is not None:
        session = _load_session()
        handle_danmaku(session, args.danmaku)
        return session

    if args.cli:
        session = _load_session()
        handle_cli(session)
        return session


if __name__ == "__main__":
    main()

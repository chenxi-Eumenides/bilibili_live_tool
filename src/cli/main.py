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

import argparse
import asyncio
import sys

from ..logic import (
    Session,
    _listen_loop,
    auth_generate_qrcode,
    auth_poll_login,
    auth_validate_login,
    live_refresh_room_info,
    live_start,
    live_stop,
    live_update_area,
    live_update_title,
    danmaku_start,
    danmaku_stop,
)
from ..utils.config import CONFIG
from ..utils.constant import CONFIG_FILE
from ..utils.data import FuncType
from ..utils.lib import generate_qr_text

CLI_FLAGS = frozenset({"--login", "--live", "--title", "--area", "--danmaku", "--cli"})


def help_lines():
    return [
        "CLI 模式:",
        "  --cli                          login + 自动开/下播",
        "  --login                        扫码登录",
        "  --live start [-a AREA] [--title TITLE]  开播",
        "  --live stop                    下播",
        "  --live status                  查看状态",
        '  --title "标题" [--area AREA]   改标题',
        "  --area AREA [--title \"标题\"]  改分区",
        "  --danmaku                      弹幕监听",
    ]


def cli_help():
    print("\n".join(help_lines()))


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
    result = live_start(session, area_id=args.area or 0)
    if result.type != FuncType.SUCCESS:
        print(f"开播失败: {result.result}")
        return
    data = result.result
    print(f"开播成功 (房间:{session.room_id})")
    if data.get("rtmp_addr"):
        print(f"推流地址: {data['rtmp_addr']}{data.get('rtmp_code','')}")
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
    if not session.config.room_data:
        refresh = live_refresh_room_info(session)
        if refresh.type != FuncType.SUCCESS:
            print(f"刷新失败: {refresh.result}")
            return
    data = session.config.room_data
    print(f"房间号: {data.get('room_id','?')}")
    print(f"标题:   {data.get('title','?')}")
    print(f"状态:   {'直播中' if data.get('live_status') else '未开播'}")
    print(f"分区:   {data.get('area_name','?')} (id={data.get('area_id','?')})")


def handle_update(session: Session, args) -> None:
    title = args.title
    area_id = args.area
    if title:
        r = live_update_title(session, title)
        if r.type == FuncType.SUCCESS:
            print(f"标题已更新: {title}")
        else:
            print(f"标题修改失败: {r.result}")
            return
    if area_id:
        r = live_update_area(session, area_id)
        if r.type == FuncType.SUCCESS:
            print(f"分区已更新: {area_id}")
        else:
            print(f"分区修改失败: {r.result}")


def handle_danmaku(session: Session) -> None:
    result = danmaku_start(session)
    if result.type != FuncType.SUCCESS:
        print(f"启动失败: {result.result}")
        return

    def on_received(msg):
        name = getattr(msg, "username", "?")
        content = getattr(msg, "content", str(msg))
        print(f"[{name}]: {content}")

    session.on("danmaku:received", on_received)
    print("弹幕监听中... 按 Ctrl+C 停止")
    try:
        asyncio.run(_listen_loop(session))
    except KeyboardInterrupt:
        pass
    finally:
        danmaku_stop(session)
        print("已停止")


def handle_cli(session: Session) -> None:
    if not handle_login(session):
        return
    refresh = live_refresh_room_info(session)
    if refresh.type != FuncType.SUCCESS:
        print(f"获取房间状态失败: {refresh.result}")
        return
    is_live = session.config.room_data.get("live_status")
    if is_live:
        print("当前正在直播")
    else:
        print("正在开播...")
        handle_live_start(session, argparse.Namespace(area=0))


def main():
    p = argparse.ArgumentParser(prog="bili", add_help=False)
    p.add_argument("--login", action="store_true")
    p.add_argument("--live", choices=["start", "stop", "status"])
    p.add_argument("-a", "--area", type=int, default=None)
    p.add_argument("--title", type=str, default=None)
    p.add_argument("--danmaku", action="store_true")
    p.add_argument("--cli", action="store_true")

    args = p.parse_args()

    if len(sys.argv) == 1:
        p.print_help()
        return

    session = None

    if args.login:
        session = _load_session()
        handle_login(session)
        return

    if args.live:
        session = _load_session()
        if args.live == "start":
            handle_live_start(session, args)
        elif args.live == "stop":
            handle_live_stop(session)
        elif args.live == "status":
            handle_live_status(session)
        return

    if args.title or args.area:
        session = _load_session()
        handle_update(session, args)
        return

    if args.danmaku:
        session = _load_session()
        handle_danmaku(session)
        return

    if args.cli:
        session = _load_session()
        handle_cli(session)
        return


if __name__ == "__main__":
    main()

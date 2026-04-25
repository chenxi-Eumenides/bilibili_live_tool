"""命令行入口

使用 argparse 定义子命令，转发到 logic 层函数。
"""

import argparse
import asyncio
import sys

from src.logic import (
    Session,
    BiliCode,
    auth_generate_qrcode,
    auth_poll_login,
    auth_validate_login,
    auth_logout,
    live_start,
    live_stop,
    live_update_title,
    live_refresh_room_info,
    live_get_room_info,
    danmaku_start,
    danmaku_stop,
    _listen_loop,
)
from src.utils.lib import generate_qr_text
from src.utils.data import FuncType


def cmd_login(session, args):
    result = auth_generate_qrcode(session)
    if result.type != FuncType.SUCCESS:
        print(f"获取二维码失败: {result.result}")
        return
    qr_url, qr_key = result.result["qr_url"], result.result["qr_key"]
    print("请使用B站App扫描以下二维码登录:\n")
    for line in generate_qr_text(qr_url):
        print(line)

    import time
    for attempt in range(90):
        poll = auth_poll_login(session, qr_key, timeout=2)
        if poll.type == FuncType.SUCCESS:
            print("\n登录成功!")
            return
        code = poll.result.get("code", -1)
        if code == BiliCode.LOGIN_QR_EXPIRED:
            print("\n二维码已过期")
            return
        time.sleep(2)


def cmd_live_start(session, args):
    result = live_start(session, area_id=getattr(args, "area_id", 0))
    if result.type == FuncType.SUCCESS:
        print(f"开播成功 (房间:{session.room_id})")
        data = result.result
        if data.get("rtmp_addr"):
            print(f"推流: {data['rtmp_addr']}{data.get('rtmp_code','')}")
    else:
        print(f"开播失败: {result.result}")


def cmd_live_stop(session, args):
    result = live_stop(session)
    if result.type == FuncType.SUCCESS:
        print("下播成功")
    else:
        print(f"下播失败: {result.result}")


def cmd_live_title(session, args):
    result = live_update_title(session, args.title)
    if result.type == FuncType.SUCCESS:
        print(f"标题已更新: {args.title}")
    else:
        print(f"修改失败: {result.result}")


def cmd_live_info(session, args):
    result = live_get_room_info(session)
    if result.type == FuncType.SUCCESS:
        data = result.result
        print(f"房间号: {data.get('room_id','?')}")
        print(f"标题:   {data.get('title','?')}")
        print(f"状态:   {'直播中' if data.get('live_status') else '未开播'}")
    else:
        print(f"获取失败: {result.result}")


def cmd_danmaku_listen(session, args):
    result = danmaku_start(session)
    if result.type != FuncType.SUCCESS:
        print(f"启动弹幕失败: {result.result}")
        return
    print("弹幕监听中... 按 Ctrl+C 停止")
    try:
        asyncio.run(_listen_loop(session))
    except KeyboardInterrupt:
        danmaku_stop(session)
        print("已停止")


def main():
    parser = argparse.ArgumentParser(prog="bili", description="B站直播管理工具")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("login", help="扫码登录")

    live_parser = sub.add_parser("live", help="直播操作")
    live_sub = live_parser.add_subparsers(dest="live_cmd")
    live_sub.add_parser("start", help="开播")
    live_sub.add_parser("stop", help="下播")
    title_parser = live_sub.add_parser("title", help="修改标题")
    title_parser.add_argument("title", help="新标题")
    live_sub.add_parser("info", help="查看房间信息")

    sub.add_parser("danmaku", help="弹幕监听")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    session = Session()

    if args.command == "login":
        cmd_login(session, args)
    elif args.command == "live":
        if args.live_cmd == "start":
            cmd_live_start(session, args)
        elif args.live_cmd == "stop":
            cmd_live_stop(session, args)
        elif args.live_cmd == "title":
            cmd_live_title(session, args)
        elif args.live_cmd == "info":
            cmd_live_info(session, args)
        else:
            live_parser.print_help()
    elif args.command == "danmaku":
        cmd_danmaku_listen(session, args)


if __name__ == "__main__":
    main()

"""命令行入口 — argparse 子命令 → logic 层函数"""

import argparse
import asyncio

from src.logic import (
    Session,
    _listen_loop,
    auth_generate_qrcode,
    auth_poll_login,
    auth_validate_login,
    live_get_area_list,
    live_refresh_room_info,
    live_start,
    live_stop,
    live_update_area,
    live_update_title,
    danmaku_start,
    danmaku_stop,
)
from src.utils.config import CONFIG
from src.utils.constant import CONFIG_FILE
from src.utils.data import FuncType
from src.utils.lib import generate_qr_text


def load_session() -> Session:
    """加载配置创建 Session，自动验证已保存的 cookies。"""
    config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
    session = Session(config)
    if session.config.cookies:
        result = auth_validate_login(session)
        if result.type == FuncType.SUCCESS:
            print(f"从 config.json 恢复登录 (uid={session.user_id})")
    return session


def cmd_login(session: Session) -> None:
    result = auth_generate_qrcode(session)
    if result.type != FuncType.SUCCESS:
        print(f"获取二维码失败: {result.result}")
        return

    qr_url = result.result["qr_url"]
    qr_key = result.result["qr_key"]
    print("请使用B站App扫描以下二维码登录:\n")
    for line in generate_qr_text(qr_url):
        print(line)

    print("\n等待扫码...")
    poll = auth_poll_login(session, qr_key)
    if poll.type == FuncType.SUCCESS:
        session.config.save_config()
        print(f"登录成功! uid={session.user_id}")
    else:
        print(f"登录失败: {poll.result}")


def cmd_live_start(session: Session, args) -> None:
    if session.room_id == 0:
        print(f"房间号未知，将自动获取 (uid={session.user_id})")

    result = live_start(session, area_id=args.area)
    if result.type == FuncType.SUCCESS:
        print(f"开播成功 (房间:{session.room_id})")
        data = result.result
        if data.get("rtmp_addr"):
            print(f"推流地址: {data['rtmp_addr']}{data.get('rtmp_code','')}")
    elif "face_auth" in str(result.result):
        print(f"需要人脸认证: {result.result}")
    else:
        print(f"开播失败: {result.result}")


def cmd_live_stop(session: Session) -> None:
    result = live_stop(session)
    if result.type == FuncType.SUCCESS:
        print("下播成功")
    else:
        print(f"下播失败: {result.result}")


def cmd_live_title(session: Session, args) -> None:
    result = live_update_title(session, args.title)
    if result.type == FuncType.SUCCESS:
        print(f"标题已更新: {args.title}")
    else:
        print(f"修改失败: {result.result}")


def cmd_live_area(session: Session, args) -> None:
    if args.list:
        result = live_get_area_list(session)
        if result.type == FuncType.SUCCESS:
            for area in result.result:
                print(f"  [{area.id}] {area.name}")
                for sub in area.list:
                    print(f"    [{sub.parent_id}/{sub.id}] {sub.name}")
        else:
            print(f"获取分区列表失败: {result.result}")
        return

    if args.area_id is None:
        print("用法: bili live area <分区ID> | bili live area --list")
        return

    result = live_update_area(session, args.area_id)
    if result.type == FuncType.SUCCESS:
        print(f"分区已更新: {args.area_id}")
    else:
        print(f"修改失败: {result.result}")


def cmd_live_info(session: Session) -> None:
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


def cmd_danmaku(session: Session) -> None:
    result = danmaku_start(session)
    if result.type != FuncType.SUCCESS:
        print(f"启动失败: {result.result}")
        return

    def on_received(msg):
        print(f"[{getattr(msg, 'username', '?')}]: {getattr(msg, 'content', msg)}")

    session.on("danmaku:received", on_received)

    print("弹幕监听中... 按 Ctrl+C 停止")
    try:
        asyncio.run(_listen_loop(session))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        danmaku_stop(session)
        print("已停止")


def main():
    parser = argparse.ArgumentParser(prog="bili", description="B站直播管理工具")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("login", help="扫码登录")

    live_parser = sub.add_parser("live", help="直播操作")
    live_sub = live_parser.add_subparsers(dest="live_cmd")

    start_parser = live_sub.add_parser("start", help="开播")
    start_parser.add_argument("-a", "--area", type=int, default=0, help="分区 ID")

    live_sub.add_parser("stop", help="下播")

    title_parser = live_sub.add_parser("title", help="修改标题")
    title_parser.add_argument("title", help="新标题")

    area_parser = live_sub.add_parser("area", help="修改分区 / 查看分区列表")
    area_parser.add_argument("area_id", nargs="?", type=int, default=None, help="新分区 ID")
    area_parser.add_argument("-l", "--list", action="store_true", help="列出所有分区")

    live_sub.add_parser("info", help="查看房间信息")

    sub.add_parser("danmaku", help="弹幕监听")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    session = load_session()

    if args.command == "login":
        cmd_login(session)
    elif args.command == "live":
        if args.live_cmd == "start":
            cmd_live_start(session, args)
        elif args.live_cmd == "stop":
            cmd_live_stop(session)
        elif args.live_cmd == "title":
            cmd_live_title(session, args)
        elif args.live_cmd == "area":
            cmd_live_area(session, args)
        elif args.live_cmd == "info":
            cmd_live_info(session)
        else:
            live_parser.print_help()
    elif args.command == "danmaku":
        cmd_danmaku(session)


if __name__ == "__main__":
    main()

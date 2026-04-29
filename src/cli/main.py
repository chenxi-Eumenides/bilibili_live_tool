"""CLI 入口：参数解析、异步分派"""

from argparse import ArgumentParser
from asyncio import run as asyncio_run
from sys import argv

from ..logic import (
    Session,
    auth_validate_login,
    auth_update_safety,
    live_init,
)
from ..utils.config import CONFIG
from ..utils.constant import CONFIG_FILE
from ..utils.data import FuncType
from .auth import handle_login
from .live import (
    handle_live_start,
    handle_live_stop,
    handle_live_status,
    handle_update,
    handle_area,
    handle_cli,
)
from .danmaku import handle_danmaku

CLI_FLAGS = frozenset(
    {
        "--cli",
        "--login",
        "--status",
        "--start",
        "--stop",
        "--update",
        "--area",
        "--danmaku",
    }
)


def help_lines():
    return [
        "CLI 模式:",
        "  --cli                          login + 自动开/下播",
        "  --login                        扫码登录",
        "  --status                       查看状态",
        "  --start [-a 分区ID] [-t 标题]  开播",
        "  --stop                         下播",
        "  --update [-a 分区ID] [-t 标题] 改分区/标题",
        "  --area                         列出主分区",
        "  --area 主分区ID                列出子分区",
        "  --danmaku [直播间号]           弹幕监听 (默认: 自己的直播间)",
    ]


def _build_parser():
    p = ArgumentParser(prog="BiliLiveTool", add_help=False, usage="\n".join(help_lines()))
    p.add_argument("--cli", action="store_true", help="")
    p.add_argument("--login", action="store_true", help="扫码登录")
    p.add_argument("--status", action="store_true", help="直播间状态")
    p.add_argument("--start", action="store_true", help="开播")
    p.add_argument("--stop", action="store_true", help="下播")
    p.add_argument("--update", action="store_true", help="更新直播间状态")
    p.add_argument("-a", type=int, nargs=1, default=None, metavar='分区id')
    p.add_argument("-t", type=str, nargs=1, default=None, metavar='标题')
    p.add_argument("--area", type=int, nargs="?", const=0, default=None, metavar='分区id', help="列出直播间分区")
    p.add_argument("--danmaku", type=int, nargs="?", const=0, default=None, metavar='直播间号', help="监听直播间弹幕")
    return p


def _load_session() -> Session:
    config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
    session = Session(config)
    if session.config.has_cookies:
        res = auth_validate_login(session)
        if res.type == FuncType.SUCCESS:
            auth_update_safety(session)
            live_init(session)
        elif result.type == FuncType.FAIL:
            print("登录已过期，请使用 --login 重新登录")
    return session


def run():
    p = _build_parser()
    args = p.parse_args()

    if len(argv) == 1:
        print("\n".join(help_lines()))
        return

    asyncio_run(_async_main(args))


async def _async_main(args):
    session = None
    try:
        session = _load_session()
        if args.cli:
            await handle_cli(session)
        elif args.login:
            await handle_login(session)
        elif args.status:
            await handle_live_status(session)
        elif args.start:
            await handle_live_start(session, args.a, args.t)
        elif args.stop:
            await handle_live_stop(session)
        elif args.update:
            await handle_update(session, args.a, args.t)
        elif args.area is not None:
            await handle_area(session, args.area)
        elif args.danmaku is not None:
            await handle_danmaku(session, args.danmaku)
    except KeyboardInterrupt:
        print()
    finally:
        if session and session.is_login:
            session.config.save_config()

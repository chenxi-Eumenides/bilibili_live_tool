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
        "--login",
        "--start",
        "--stop",
        "--status",
        "--update",
        "--title",
        "--area",
        "--danmaku",
        "--cli",
    }
)


def help_lines():
    return [
        "CLI 模式:",
        "  --cli                          login + 自动开/下播",
        "  --login                        扫码登录",
        "  --status                       查看状态",
        "  --start [-a 分区ID] [-t 标题]  开播",
        "  --stop                    下播",
        "  --update [-a 分区ID] [-t 标题] 改分区/标题",
        "  --area                    列出主分区",
        "  --area 主分区ID             列出子分区",
        "  --danmaku [直播间号]            弹幕监听 (默认: 自己的直播间)",
    ]


def _build_parser():
    p = ArgumentParser(prog="bili", add_help=False)
    p.add_argument("--login", action="store_true")
    p.add_argument("--start", action="store_true")
    p.add_argument("--stop", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--update", action="store_true")
    p.add_argument("--area", nargs="*", default=None)
    p.add_argument("--title", type=str, default=None)
    p.add_argument("--danmaku", nargs="?", const="", default=None)
    p.add_argument("--cli", action="store_true")
    return p


def _load_session(*, with_live_init: bool = False) -> Session:
    config = CONFIG.from_file() if CONFIG_FILE.exists() else CONFIG()
    session = Session(config)
    if session.config.cookies:
        result = auth_validate_login(session)
        if result.type == FuncType.SUCCESS and with_live_init:
            auth_update_safety(session)
            live_init(session)
        elif result.type == FuncType.FAIL:
            print("登录已过期，请使用 --login 重新登录")
    return session


def run():
    p = _build_parser()
    args = p.parse_args()

    if len(argv) == 1:
        p.print_help()
        return

    asyncio_run(_async_main(args))


async def _async_main(args):
    session = None
    try:
        if args.login:
            session = _load_session()
            await handle_login(session)
            return
        if args.danmaku is not None:
            session = _load_session()
            await handle_danmaku(session, args.danmaku)
            return

        session = _load_session(with_live_init=True)

        if args.start:
            await handle_live_start(session, args)
        elif args.stop:
            await handle_live_stop(session)
        elif args.status:
            await handle_live_status(session)
        elif args.update:
            await handle_update(session, args)
        elif args.area is not None:
            await handle_area(session, args.area)
        elif args.cli:
            await handle_cli(session)
    except KeyboardInterrupt:
        print()
    finally:
        if session and session.is_login:
            session.config.save_config()

"""弹幕处理编排"""

from asyncio import CancelledError, create_task, Event, sleep as asyncio_sleep

from ..utils.api import (
    get_danmaku_info,
    get_danmaku_websocket,
    ws_send_auth,
    ws_send_heart,
    ws_listen_danmaku,
    get_wbi_key,
)
from ..utils.data import FuncResult, FuncType
from ..utils.constant import SessionEvent, Tuning
from .session import Session


def danmaku_start(session: Session) -> FuncResult:
    """准备弹幕监听（同步，立即返回）。

    只做前置校验和标记运行状态，实际的异步监听由 _listen_loop 执行。

    Args:
        session: Session 实例

    Returns:
        FuncResult(SUCCESS) 或 FAIL（重复启动/未登录/无房间号）
    """
    if session._danmaku_running:
        session._emit(SessionEvent.DANMAKU_START_FAIL, "弹幕监听已在运行")
        return FuncResult(type=FuncType.FAIL, result="弹幕监听已在运行")
    if not session.is_login:
        session._emit(SessionEvent.DANMAKU_START_FAIL, "未登录，无法监听弹幕")
        return FuncResult(type=FuncType.FAIL, result="未登录，无法监听弹幕")
    if not (session.danmaku_room_id or session.config.room_id):
        session._emit(SessionEvent.DANMAKU_START_FAIL, "未设置房间号")
        return FuncResult(type=FuncType.FAIL, result="未设置房间号")
    session._danmaku_stop_event = Event()
    session._danmaku_running = True
    session._emit(
        SessionEvent.DANMAKU_STARTED,
        {"danmaku_room_id": session.danmaku_room_id or session.config.room_id},
    )
    return FuncResult(type=FuncType.SUCCESS, result="弹幕监听已就绪")


def danmaku_stop(session: Session) -> FuncResult:
    """停止弹幕监听（同步）。

    设置停止信号，_listen_loop 检测后优雅退出。

    Args:
        session: Session 实例

    Returns:
        FuncResult(SUCCESS) 或 FAIL（未在运行）
    """
    if not session._danmaku_running:
        session._emit(SessionEvent.DANMAKU_STOP_FAIL, "弹幕监听未在运行")
        return FuncResult(type=FuncType.FAIL, result="弹幕监听未在运行")
    session._danmaku_stop_event.set()
    session.cache_danmaku_key = ""
    session.cache_danmaku_ws_urls = []
    session._emit(SessionEvent.DANMAKU_STOPPED, {"reason": "主动停止"})
    return FuncResult(type=FuncType.SUCCESS, result="已发送停止信号")


async def _listen_loop(session: Session) -> None:
    """弹幕监听主循环（异步）。

    完整生命周期：取 wbi 密钥 → 取 WS 信息 → 连接 WS → 认证 →
    启动心跳 → 循环接收 → finally 清理资源。

    Events:
        DANMAKU_RECEIVED: 每收到一条弹幕触发
        DANMAKU_STOPPED:  监听停止时触发
        ERROR:            各阶段失败时触发
    """
    ws = None
    heartbeat_task = None
    room_id = session.danmaku_room_id or session.config.room_id
    try:
        if session.cache_danmaku_key and session.cache_danmaku_ws_urls:
            danmaku_key, ws_url_list = session.cache_danmaku_key, session.cache_danmaku_ws_urls
        else:
            wbi_result = get_wbi_key(session.config.cookies)
            if wbi_result.type != FuncType.SUCCESS:
                session._emit(SessionEvent.ERROR, f"获取 wbi 密钥失败: {wbi_result.result}")
                return
            img_key, sub_key = wbi_result.result["img_key"], wbi_result.result["sub_key"]

            info_result = get_danmaku_info(
                cookies=session.config.cookies,
                room_id=room_id,
                img_key=img_key,
                sub_key=sub_key,
            )
            if info_result.type != FuncType.SUCCESS or not info_result.result.get(
                "danmaku_ws_url_list"
            ):
                session._emit(
                    SessionEvent.ERROR, f"获取弹幕 WS 信息失败: {info_result.result}"
                )
                return
            danmaku_key = info_result.result["danmaku_key"]
            ws_url_list = info_result.result["danmaku_ws_url_list"]
            session.cache_danmaku_key = danmaku_key
            session.cache_danmaku_ws_urls = ws_url_list

        ws_url = ws_url_list[0]

        ws_result = await get_danmaku_websocket(ws_url)
        if ws_result.type != FuncType.SUCCESS:
            session._emit(SessionEvent.ERROR, f"弹幕 WS 连接失败: {ws_result.result}")
            return
        ws = ws_result.result

        auth_result = await ws_send_auth(
            ws,
            session.config.uid,
            session.danmaku_room_id or session.config.room_id,
            danmaku_key,
        )
        if auth_result.type != FuncType.SUCCESS:
            was_cached = bool(session.cache_danmaku_key)
            if was_cached:
                session._emit(
                    SessionEvent.DANMAKU_KEY_INVALID,
                    {"room_id": room_id, "reason": "缓存 key 认证失败，重新获取"},
                )
                session.cache_danmaku_key = ""
                session.cache_danmaku_ws_urls = []
                await ws.close()

                wbi_result = get_wbi_key(session.config.cookies)
                if wbi_result.type != FuncType.SUCCESS:
                    session._emit(SessionEvent.ERROR, f"获取 wbi 密钥失败: {wbi_result.result}")
                    return
                img_key, sub_key = wbi_result.result["img_key"], wbi_result.result["sub_key"]
                info_result = get_danmaku_info(
                    cookies=session.config.cookies,
                    room_id=room_id,
                    img_key=img_key, sub_key=sub_key,
                )
                if info_result.type != FuncType.SUCCESS or not info_result.result.get("danmaku_ws_url_list"):
                    session._emit(SessionEvent.ERROR, f"获取弹幕 WS 信息失败: {info_result.result}")
                    return
                danmaku_key = info_result.result["danmaku_key"]
                ws_url_list = info_result.result["danmaku_ws_url_list"]
                session.cache_danmaku_key = danmaku_key
                session.cache_danmaku_ws_urls = ws_url_list

                ws_url = ws_url_list[0]
                ws_result = await get_danmaku_websocket(ws_url)
                if ws_result.type != FuncType.SUCCESS:
                    session._emit(SessionEvent.ERROR, f"弹幕 WS 重连失败: {ws_result.result}")
                    return
                ws = ws_result.result
                auth_result = await ws_send_auth(
                    ws,
                    session.config.uid,
                    session.danmaku_room_id or session.config.room_id,
                    danmaku_key,
                )
            if auth_result.type != FuncType.SUCCESS:
                session._emit(SessionEvent.ERROR, f"弹幕 WS 认证失败: {auth_result.result}")
                return

        heartbeat_task = create_task(_heartbeat_loop(ws, session))

        async for result in ws_listen_danmaku(ws):
            if session._danmaku_stop_event and session._danmaku_stop_event.is_set():
                break
            if result.type == FuncType.SUCCESS:
                messages = result.result
                if isinstance(messages, list):
                    room = session.danmaku_room_id or session.config.room_id
                    for msg in messages:
                        if hasattr(msg, "live_room_id"):
                            msg.live_room_id = room
                        session._emit(SessionEvent.DANMAKU_RECEIVED, msg)
            else:
                session._emit(SessionEvent.ERROR, f"弹幕接收异常: {result.result}")
    except CancelledError:
        pass
    except Exception as e:
        session._emit(SessionEvent.ERROR, f"弹幕监听异常: {e}")
    finally:
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except CancelledError:
                pass
        if ws:
            try:
                await ws.close()
            except Exception:
                pass
        session._danmaku_running = False
        session._danmaku_stop_event = None
        session.cache_danmaku_key = ""
        session.cache_danmaku_ws_urls = []
        session._emit(SessionEvent.DANMAKU_STOPPED, {"reason": "监听循环结束"})


async def _heartbeat_loop(ws, session: Session) -> None:
    """后台心跳：每 30 秒发一次心跳包，检测停止信号后退出。"""
    stop_event = session._danmaku_stop_event
    try:
        while not (stop_event and stop_event.is_set()):
            await asyncio_sleep(Tuning.DANMAKU_HEARTBEAT)
            if stop_event and stop_event.is_set():
                break
            await ws_send_heart(ws)
    except CancelledError:
        pass
    except Exception as e:
        if session._danmaku_stop_event:
            session._danmaku_stop_event.set()
        session._emit(SessionEvent.ERROR, f"弹幕心跳异常: {e}")

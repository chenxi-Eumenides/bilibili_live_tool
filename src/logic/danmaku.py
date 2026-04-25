"""弹幕处理编排

管理 B 站弹幕 WebSocket 的完整生命周期：获取信息 → 连接 → 认证 →
后台心跳 → 持续接收弹幕 → 清理资源。

asyncio 使用局限在本模块内部。用户层（CLI/TUI）无需 import asyncio：
- CLI：asyncio.run(_listen_loop(session))
- TUI：self.run_worker(_listen_loop(session))
"""

from __future__ import annotations

import asyncio

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

    初始化停止信号、标记运行状态。实际的异步监听由 _listen_loop 执行。
    防止重复启动：如果已有监听在运行，返回 FAIL。

    Returns:
        FuncResult(SUCCESS) 或 FAIL
    """
    if session._danmaku_running:
        return FuncResult(type=FuncType.FAIL, result="弹幕监听已在运行")

    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法监听弹幕")

    if session.room_id == 0:
        return FuncResult(type=FuncType.FAIL, result="未设置房间号")

    session._danmaku_stop_event = asyncio.Event()
    session._danmaku_running = True
    return FuncResult(type=FuncType.SUCCESS, result="弹幕监听已就绪")


def danmaku_stop(session: Session) -> FuncResult:
    """停止弹幕监听（同步）。

    设置停止信号，由 _listen_loop 内部检测后优雅退出。

    Returns:
        FuncResult(SUCCESS) 或 FAIL
    """
    if not session._danmaku_running:
        return FuncResult(type=FuncType.FAIL, result="弹幕监听未在运行")

    session._danmaku_stop_event.set()
    return FuncResult(type=FuncType.SUCCESS, result="已发送停止信号")


async def _listen_loop(session: Session) -> None:
    """弹幕监听主循环（异步协程）。

    完整生命周期：
    1. 获取 wbi 签名密钥
    2. 获取弹幕 WebSocket 信息
    3. 建立 WebSocket 连接
    4. 发送认证包
    5. 启动后台心跳任务
    6. 循环接收弹幕消息 → emit DANMAKU_RECEIVED
    7. cleanup（finally）：取消心跳、关闭 ws、emit DANMAKU_STOPPED、重置状态

    用户层通过 danmaku_stop() 设置 _danmaku_stop_event 来优雅退出。
    """
    ws = None
    heartbeat_task = None

    try:
        # 1. 获取 wbi 签名密钥
        wbi_result = get_wbi_key(session.cookies)
        if wbi_result.type != FuncType.SUCCESS:
            session._emit(SessionEvent.ERROR, f"获取 wbi 密钥失败: {wbi_result.result}")
            return
        img_key = wbi_result.result["img_key"]
        sub_key = wbi_result.result["sub_key"]

        # 2. 获取弹幕 WebSocket 信息
        info_result = get_danmaku_info(
            cookies=session.cookies,
            room_id=session.room_id,
            img_key=img_key,
            sub_key=sub_key,
        )
        if info_result.type != FuncType.SUCCESS or not info_result.result.get("danmaku_ws_url_list"):
            session._emit(SessionEvent.ERROR, f"获取弹幕 WS 信息失败: {info_result.result}")
            return

        ws_url = info_result.result["danmaku_ws_url_list"][0]
        danmaku_key = info_result.result["danmaku_key"]

        # 3. 连接 WebSocket
        ws_result = await get_danmaku_websocket(ws_url)
        if ws_result.type != FuncType.SUCCESS:
            session._emit(SessionEvent.ERROR, f"弹幕 WS 连接失败: {ws_result.result}")
            return
        ws = ws_result.result

        # 4. 发送认证
        auth_result = await ws_send_auth(
            ws, session.user_id, session.room_id, danmaku_key
        )
        if auth_result.type != FuncType.SUCCESS:
            session._emit(SessionEvent.ERROR, f"弹幕 WS 认证失败: {auth_result.result}")
            return

        # 5. 启动后台心跳
        heartbeat_task = asyncio.create_task(_heartbeat_loop(ws, session))

        # 6. 持续接收弹幕
        async for result in ws_listen_danmaku(ws):
            if session._danmaku_stop_event and session._danmaku_stop_event.is_set():
                break

            if result.type == FuncType.SUCCESS:
                messages = result.result
                if isinstance(messages, list):
                    for msg in messages:
                        session._emit(SessionEvent.DANMAKU_RECEIVED, msg)
            else:
                session._emit(SessionEvent.ERROR, f"弹幕接收异常: {result.result}")

    except asyncio.CancelledError:
        pass
    except Exception as e:
        session._emit(SessionEvent.ERROR, f"弹幕监听异常: {e}")
    finally:
        # 取消心跳任务
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        # 关闭 WebSocket
        if ws:
            try:
                await ws.close()
            except Exception:
                pass

        session._danmaku_running = False
        session._danmaku_stop_event = None
        session._emit(SessionEvent.DANMAKU_STOPPED)


async def _heartbeat_loop(ws, session: Session) -> None:
    """后台心跳任务：每 30 秒发送一次心跳包。

    检测到 _danmaku_stop_event 或连接异常时退出。
    """
    stop_event = session._danmaku_stop_event

    try:
        while not (stop_event and stop_event.is_set()):
            await asyncio.sleep(Tuning.DANMAKU_HEARTBEAT)
            if stop_event and stop_event.is_set():
                break
            await ws_send_heart(ws)
    except asyncio.CancelledError:
        pass
    except Exception:
        # 心跳失败（如 ws 断开）静默退出，
        # 由 _listen_loop 的 async for 循环检测到断连并处理
        pass

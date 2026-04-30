"""CLI 弹幕命令处理"""

from rich import print

from ..logic import danmaku_start, danmaku_stop, _listen_loop
from ..utils.constant import SessionEvent


async def handle_danmaku(session, room_id: int | None = None) -> None:
    if room_id:
        session.danmaku_room_id = room_id
        print(f"监听直播间: {session.danmaku_room_id}")
    else:
        print(f"监听自己的直播间: {session.config.room_id}")

    start_captured = {}

    def on_started(data):
        start_captured["event"] = "started"

    def on_fail(msg):
        start_captured["event"] = "fail"
        start_captured["msg"] = str(msg) if msg else "启动失败"

    session.once(SessionEvent.DANMAKU_STARTED, on_started)
    session.once(SessionEvent.DANMAKU_START_FAIL, on_fail)
    danmaku_start(session)

    if start_captured.get("event") == "fail":
        print(start_captured["msg"])
        return

    print("按两次 Ctrl+C 停止")

    def on_received(msg):
        if hasattr(msg, "format_rich"):
            print(msg.format_rich())
        else:
            print(msg)

    def on_error(msg):
        print(f"[错误] {msg}")

    def on_key_invalid(data):
        room = (data or {}).get("room_id", "?")
        reason = (data or {}).get("reason", "key 失效")
        print(f"[重试] {reason} (房间 {room})")

    session.on(SessionEvent.DANMAKU_RECEIVED, on_received)
    session.once(SessionEvent.ERROR, on_error)
    session.once(SessionEvent.DANMAKU_KEY_INVALID, on_key_invalid)
    try:
        await _listen_loop(session)
    except KeyboardInterrupt:
        pass
    finally:
        session.off(SessionEvent.DANMAKU_RECEIVED, on_received)
        if session._danmaku_running:
            danmaku_stop(session)
        print("已停止")

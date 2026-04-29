"""CLI 弹幕命令处理"""

from rich import print

from ..logic import danmaku_start, danmaku_stop, _listen_loop
from ..utils.constant import SessionEvent


async def handle_danmaku(session, room_id: str | None = None) -> None:
    if room_id:
        session.danmaku_room_id = int(room_id)
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

    session.on(SessionEvent.DANMAKU_RECEIVED, on_received)
    try:
        await _listen_loop(session)
    except KeyboardInterrupt:
        pass
    finally:
        session.off(SessionEvent.DANMAKU_RECEIVED, on_received)
        stop_captured = {}

        def on_stopped(data):
            stop_captured["event"] = "stopped"

        def on_stop_fail(msg):
            stop_captured["event"] = "fail"
            stop_captured["msg"] = str(msg) if msg else "停止失败"

        session.once(SessionEvent.DANMAKU_STOPPED, on_stopped)
        session.once(SessionEvent.DANMAKU_STOP_FAIL, on_stop_fail)
        danmaku_stop(session)

        if stop_captured.get("event") == "fail":
            print(stop_captured["msg"])
        else:
            print("已停止")

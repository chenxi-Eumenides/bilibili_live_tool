"""CLI 认证命令处理"""

from asyncio import CancelledError, to_thread
from threading import Event
from rich import print

from ..logic import auth_get_qr, auth_poll_qr, auth_validate_login
from ..utils.constant import SessionEvent
from ..utils.lib import generate_qr_text


async def handle_login(session) -> bool:
    auth_validate_login(session)
    if session.is_login:
        print(f"已登录 (uid={session.config.uid})")
        return True

    qr_data = {}

    def on_ready(data):
        qr_data["event"] = "ready"
        if data:
            qr_data["url"] = data.get("qr_url", "")
            qr_data["key"] = data.get("qr_key", "")

    def on_fail(msg):
        qr_data["event"] = "fail"
        qr_data["msg"] = str(msg) if msg else "获取二维码失败"

    session.once(SessionEvent.AUTH_QR_READY, on_ready)
    session.once(SessionEvent.AUTH_QR_FAIL, on_fail)
    auth_get_qr(session)

    if qr_data.get("event") == "fail":
        print(f"获取二维码失败: {qr_data.get('msg')}")
        return False

    print("请使用B站App扫描以下二维码登录:\n")
    print("\n".join(generate_qr_text(qr_data["url"])))
    print("\n等待扫码...")

    poll_result = {}

    def on_success(data):
        poll_result["event"] = "success"

    def on_failed(msg):
        poll_result["event"] = "fail"
        poll_result["msg"] = str(msg) if msg else "登录失败"

    session.once(SessionEvent.AUTH_LOGIN_SUCCESS, on_success)
    session.once(SessionEvent.AUTH_LOGIN_FAILED, on_failed)
    stop = Event()
    try:
        await to_thread(auth_poll_qr, session, qr_data["key"], stop_event=stop)
    except (KeyboardInterrupt, CancelledError):
        stop.set()
        print("\n已取消")
        return False

    if poll_result.get("event") == "fail":
        print(f"登录失败: {poll_result.get('msg')}")
        return False

    session.config.save_config()
    print(f"登录成功! uid={session.config.uid}")
    return True


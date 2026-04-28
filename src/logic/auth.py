"""登录认证编排"""

from threading import Event
from time import monotonic, sleep
from typing import Optional

from ..utils.api import api_get_login_qr, api_check_login, api_get_room_id, api_get_user_nav, get_bili_ticket
from ..utils.data import FuncResult, FuncType
from ..utils.constant import BiliCode, SessionEvent, Tuning
from .session import Session


def auth_generate_qrcode(session: Session) -> FuncResult:
    """生成登录二维码。

    Args:
        session: Session 实例

    Returns:
        FuncResult(SUCCESS, {qr_url, qr_key}) 或 FAIL

    返回: FuncResult(SUCCESS, {qr_url, qr_key}) 或 FAIL
    Events: AUTH_QRCODE_READY，携带 {'qr_url', 'qr_key'}"""

    result = api_get_login_qr()
    if result.type != FuncType.SUCCESS:
        return result
    qr_url = result.result["qr_url"]
    qr_key = result.result["qr_key"]
    session._emit(SessionEvent.AUTH_QRCODE_READY, {"qr_url": qr_url, "qr_key": qr_key})
    return FuncResult(type=FuncType.SUCCESS, result={"qr_url": qr_url, "qr_key": qr_key})


def auth_poll_login(
    session: Session,
    qr_key: str,
    timeout_sec: int = Tuning.LOGIN_POLL_TIMEOUT,
    stop_event: Event | None = None,
) -> FuncResult:
    """轮询二维码登录状态，直到登录成功、过期或超时。

    Args:
        session: Session 实例
        qr_key: 从 auth_generate_qrcode 得到的 key
        timeout_sec: 总超时秒数

    Returns:
        FuncResult(SUCCESS, {cookies, refresh_token}) 或 FAIL

    返回: FuncResult(SUCCESS, {cookies, refresh_token}) 或 FAIL
    Events: 等待扫码发 AUTH_QR_WAITING；已扫码发 AUTH_QR_SCANNED；成功时发 AUTH_LOGIN_SUCCESS 并写入 cookies/uid/bili_ticket；失败发 AUTH_LOGIN_FAILED"""

    deadline = monotonic() + timeout_sec
    while monotonic() < deadline:
        if stop_event and stop_event.is_set():
            return FuncResult(type=FuncType.FAIL, result="已取消")
        remaining = int(deadline - monotonic())
        result = api_check_login(qr_key)
        if result.type == FuncType.SUCCESS:
            cookies = result.result["cookies"]
            refresh_token = result.result["refresh_token"]
            session.config.cookies = cookies
            session.config.refresh_token = refresh_token or ""
            session.config.csrf = cookies.get("bili_jct", "")
            session.config.uid = int(cookies.get("DedeUserID", 0))
            session._login_verified = True
            try:
                ticket_result = get_bili_ticket(cookies)
                if ticket_result.type == FuncType.SUCCESS:
                    session.bili_ticket = ticket_result.result.get("bili_ticket", "")
            except Exception:
                pass
            auth_post_login(session)
            session._emit(SessionEvent.AUTH_LOGIN_SUCCESS)
            return FuncResult(type=FuncType.SUCCESS, result={"cookies": cookies, "refresh_token": refresh_token})
        code = result.result if isinstance(result.result, int) else None
        if code == BiliCode.LOGIN_QR_WAITING:
            session._emit(SessionEvent.AUTH_QR_WAITING, remaining)
        elif code == BiliCode.LOGIN_QR_SCANNED:
            session._emit(SessionEvent.AUTH_QR_SCANNED, remaining)
        else:
            reason = _poll_code_reason(code)
            session._emit(SessionEvent.AUTH_LOGIN_FAILED, reason)
            return FuncResult(type=FuncType.FAIL, result=reason)
        if stop_event:
            if stop_event.wait(timeout=Tuning.POLL_INTERVAL):
                return FuncResult(type=FuncType.FAIL, result="已取消")
        else:
            sleep(Tuning.POLL_INTERVAL)
    session._emit(SessionEvent.AUTH_LOGIN_FAILED, "登录超时")
    return FuncResult(type=FuncType.FAIL, result="登录超时")


def auth_post_login(session: Session) -> None:
    """登录完成后的初始化：获取 room_id、分区列表、房间信息。

    应在 auth_poll_login 成功后调用。
    """
    from .live import live_get_area_list, live_refresh_room_info

    if session.config.room_id == 0 and session.config.uid:
        id_result = api_get_room_id(cookies=session.cookies, user_id=session.config.uid)
        if id_result.type == FuncType.SUCCESS:
            session.config.room_id = id_result.result
    live_refresh_room_info(session)
    live_get_area_list(session)
    session.config.save_config()
    session._emit(SessionEvent.LIVE_INFO_UPDATED, session.config.room_data)


def auth_validate_login(session: Session) -> FuncResult:
    """验证当前 cookies 是否有效（通过 API 请求判断）。

    Args:
        session: Session 实例

    Returns:
        FuncResult(SUCCESS, {uname, mid, ...}) 或 FAIL

    返回: FuncResult(SUCCESS, 用户数据) 或 FAIL
    Events: 成功发 AUTH_LOGIN_SUCCESS，失败发 AUTH_LOGIN_FAILED"""

    if not session.config.cookies:
        session._login_verified = False
        session._emit(SessionEvent.AUTH_LOGIN_FAILED, "无 cookies, 未登录")
        return FuncResult(type=FuncType.FAIL, result="无 cookies, 未登录")
    res = api_get_user_nav(session.cookies)
    if res.type != FuncType.SUCCESS:
        session._login_verified = False
        session._emit(SessionEvent.AUTH_LOGIN_FAILED, "登录已过期")
        return FuncResult(type=FuncType.FAIL, result="登录已过期")
    session._login_verified = True
    session._emit(SessionEvent.AUTH_LOGIN_SUCCESS)
    return FuncResult(type=FuncType.SUCCESS, result=res.result)


def auth_logout(session: Session) -> FuncResult:
    """登出，清除所有登录态。

    Args:
        session: Session 实例

    Returns:
        FuncResult(SUCCESS, "登出成功")

    返回: FuncResult(SUCCESS, "登出成功")
    Events: AUTH_LOGOUT_DONE；清空 cookies/csrf/refresh_token/uid"""

    session.config.cookies = {}
    session.config.csrf = ""
    session.config.refresh_token = ""
    session.config.uid = 0
    session._login_verified = False
    session._emit(SessionEvent.AUTH_LOGOUT_DONE)
    return FuncResult(type=FuncType.SUCCESS, result="登出成功")


def _poll_code_reason(code: Optional[int]) -> str:
    code_map = {
        BiliCode.LOGIN_QR_EXPIRED: "二维码已过期",
        86039: "二维码无效",
    }
    return code_map.get(code or 0, f"登录失败（code={code}）")

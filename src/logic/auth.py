"""登录认证编排"""

from threading import Event
from time import monotonic, sleep

from .session import Session
from ..utils.api import (
    api_get_login_qr,
    api_check_login,
    api_get_user_nav,
    api_get_bili_ticket,
)
from ..utils.data import FuncResult, FuncType
from ..utils.constant import BiliCode, SessionEvent, Tuning


def auth_get_qr(session: Session) -> FuncResult:
    """生成登录二维码信息。

    Args:
        session: Session 实例
    Events:
        AUTH_QRCODE_READY: 已生成登录二维码信息
        AUTH_QRCODE_FAIL
    Returns:
        FuncResult(SUCCESS) 或 FAIL
    """

    res = api_get_login_qr()
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.AUTH_QR_FAIL, str(res.result))
        return res
    session.cache_qr_url = res.result["qr_url"]
    session.cache_qr_key = res.result["qr_key"]
    session._emit(SessionEvent.AUTH_QR_READY, res.result)
    return res


def auth_poll_qr(
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
        stop_event: 停止事件
    Events:
        AUTH_LOGIN_SUCCESS: 登录成功
        AUTH_QR_WAITING, int: 等待扫码
        AUTH_QR_SCANNED, int: 已扫码，等待确认
        AUTH_LOGIN_FAILED, str: 登录失败
    Returns:
        FuncResult(SUCCESS, {cookies, refresh_token}) 或 FAIL
    """

    deadline = monotonic() + timeout_sec
    while True:
        # 取消或超时
        if monotonic() > deadline:
            session._emit(SessionEvent.AUTH_LOGIN_FAILED, "登录超时")
            return FuncResult(type=FuncType.FAIL, result="登录超时")
        if stop_event and stop_event.is_set():
            session._emit(SessionEvent.AUTH_LOGIN_FAILED, "已取消")
            return FuncResult(type=FuncType.FAIL, result="已取消")
        # 请求
        res = api_check_login(qr_key)
        if res.type == FuncType.SUCCESS:
            break
        code = res.result if isinstance(res.result, int) else None
        if code == BiliCode.LOGIN_QR_WAITING:
            # 等待扫码
            session._emit(SessionEvent.AUTH_QR_WAITING, int(deadline - monotonic()))
        elif code == BiliCode.LOGIN_QR_SCANNED:
            # 已扫码，等待确认
            session._emit(SessionEvent.AUTH_QR_SCANNED, int(deadline - monotonic()))
        elif code == BiliCode.LOGIN_QR_EXPIRED:
            # 二维码过期
            session._emit(SessionEvent.AUTH_LOGIN_FAILED, "二维码过期")
            return FuncResult(type=FuncType.FAIL, result="二维码过期")
        elif code == BiliCode.LOGIN_QR_INVALID:
            # 二维码无效
            session._emit(SessionEvent.AUTH_LOGIN_FAILED, "二维码无效")
            return FuncResult(type=FuncType.FAIL, result="二维码无效")
        else:
            session._emit(SessionEvent.AUTH_LOGIN_FAILED, f"登录失败（code={code}）")
            return FuncResult(type=FuncType.FAIL, result=f"登录失败（code={code}）")
        # 等待
        if stop_event:
            if stop_event.wait(timeout=Tuning.POLL_INTERVAL):
                session._emit(SessionEvent.AUTH_LOGIN_FAILED, "已取消")
                return FuncResult(type=FuncType.FAIL, result="已取消")
        else:
            sleep(Tuning.POLL_INTERVAL)

    # 登录成功
    data = res.result
    cookies = data["cookies"]
    refresh_token = res.result["refresh_token"]
    session.config.cookies = cookies
    session.config.set_refresh_token(refresh_token)
    session.login_verified = True
    session.config.save_config()
    session._emit(SessionEvent.AUTH_LOGIN_SUCCESS, {"uid": session.config.uid})
    return FuncResult(type=FuncType.SUCCESS)


def auth_update_safety(session: Session) -> FuncResult:
    """更新鉴权信息

    更新 bili_ticket 和 wbi_key

    Args:
        session: Session 实例
    Events:
        AUTH_UPDATE_SAFETY: 鉴权信息更新成功
    Returns:
        FuncResult(SUCCESS, {uname, mid, ...}) 或 FAIL
    """

    if not (session.config.need_update_refresh_token or session.config.need_update_wbi):
        session._emit(SessionEvent.AUTH_SAFETY_SKIPPED, "无需更新")
        return FuncResult(type=FuncType.FAIL, result="无需更新")
    res = api_get_bili_ticket(session.config.cookies)
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.AUTH_UPDATE_SAFETY_FAIL, "更新失败")
        return FuncResult(type=FuncType.FAIL, result="更新失败")
    data = res.result
    session.config.bili_ticket = data.get("bili_ticket", "")
    session.config.bili_ticket_timestamp = data.get("created_at", 0)
    session.config.bili_ticket_ttl = data.get("ttl", 0)
    session.config.set_wbi(data.get("img_key", ""), data.get("sub_key", ""))
    session.config.save_config()
    session._emit(
        SessionEvent.AUTH_UPDATE_SAFETY,
        {
            "bili_ticket": session.config.bili_ticket,
            "wbi_img_key": session.config.wbi_img_key,
            "wbi_sub_key": session.config.wbi_sub_key,
        },
    )
    return FuncResult(type=FuncType.SUCCESS, result="更新成功")


def auth_validate_login(session: Session) -> FuncResult:
    """验证当前 cookies 是否有效（通过 API 请求判断）。

    Args:
        session: Session 实例
    Events:
        AUTH_LOGIN_SUCCESS
        AUTH_LOGIN_FAILED
    Returns:
        FuncResult(SUCCESS, {uname, mid, ...}) 或 FAIL
    """

    session.login_verified = False
    if not session.config.has_cookies:
        session._emit(SessionEvent.AUTH_LOGIN_FAILED, "无 cookies, 未登录")
        return FuncResult(type=FuncType.FAIL, result="无 cookies, 未登录")
    res = api_get_user_nav(session.config.cookies)
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.AUTH_LOGIN_FAILED, "登录已过期")
        return FuncResult(type=FuncType.FAIL, result="登录已过期")
    session.login_verified = True
    session._emit(SessionEvent.AUTH_LOGIN_SUCCESS, {"uid": session.config.uid})
    return FuncResult(type=FuncType.SUCCESS, result=res.result)


def auth_logout(session: Session) -> FuncResult:
    """登出，清除所有登录态。

    Args:
        session: Session 实例

    Events:
        AUTH_LOGOUT: 清空 cookies/uid

    Returns:
        FuncResult(SUCCESS, "登出成功")
    """

    session.config = None
    session.app_state = None
    session.login_verified = False
    session.room_data = {}
    session.cache_qr_url = ""
    session.cache_qr_key = ""
    session.cache_face_qr_url = ""
    session._emit(SessionEvent.AUTH_LOGOUT, {"reason": "登出成功"})
    return FuncResult(type=FuncType.SUCCESS, result="登出成功")

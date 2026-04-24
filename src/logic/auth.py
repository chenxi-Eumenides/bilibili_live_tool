"""登录认证编排

组合基础层 API（qr 生成、轮询、登出），管理登录中间状态（qrcode_key），
通过 session._emit 推送事件给用户层。
"""

from __future__ import annotations

import time
from typing import Optional

from ..utils.api import api_get_login_qr, api_check_login, api
from ..utils.data import FuncResult, FuncType, ApiType
from ..utils.lib import generate_qr_text
from ..utils.error import API_BILI_CODE_ERROR
from ..utils.constant import ApiUrl
from .session import (
    Session,
    AUTH_QRCODE_READY,
    AUTH_LOGIN_POLLING,
    AUTH_LOGIN_SUCCESS,
    AUTH_LOGIN_FAILED,
    AUTH_LOGOUT_DONE,
)


POLL_STATUS_WAITING = 86101
POLL_STATUS_SCANNED = 86090
POLL_STATUS_EXPIRED = 86038
DEFAULT_TIMEOUT = 180
POLL_INTERVAL = 2


def auth_generate_qrcode(session: Session) -> FuncResult:
    """生成登录二维码，返回 {qr_url, qr_key}。

    副作用：emit auth:qrcode_ready(qr_text_lines)
    """
    result = api_get_login_qr()
    if result.type != FuncType.SUCCESS:
        return result

    qr_url = result.result["qr_url"]
    qr_key = result.result["qr_key"]

    qr_text = generate_qr_text(qr_url)
    session._emit(AUTH_QRCODE_READY, qr_text)

    return FuncResult(
        type=FuncType.SUCCESS,
        result={"qr_url": qr_url, "qr_key": qr_key},
    )


def auth_poll_login(
    session: Session,
    qr_key: str,
    timeout_sec: int = DEFAULT_TIMEOUT,
) -> FuncResult:
    """轮询二维码登录状态，直到成功/超时/过期。

    Args:
        qr_key: 从 auth_generate_qrcode 返回的 key
        timeout_sec: 超时秒数，默认 180

    返回值：FuncResult(SUCCESS, {cookies, refresh_token}) 或 FAIL/ERROR
    副作用：emit auth:login_polling / auth:login_success / auth:login_failed
    """
    deadline = time.monotonic() + timeout_sec

    while time.monotonic() < deadline:
        remaining = int(deadline - time.monotonic())

        result = api_check_login(qr_key)

        if result.type == FuncType.SUCCESS:
            cookies = result.result["cookies"]
            refresh_token = result.result["refresh_token"]

            session.config.cookies = cookies
            session.config.refresh_token = refresh_token or ""
            session.config.csrf = cookies.get("bili_jct", "")
            session._emit(AUTH_LOGIN_SUCCESS)
            return FuncResult(
                type=FuncType.SUCCESS,
                result={"cookies": cookies, "refresh_token": refresh_token},
            )

        code = result.result if isinstance(result.result, int) else None
        if code in (POLL_STATUS_WAITING, POLL_STATUS_SCANNED):
            session._emit(AUTH_LOGIN_POLLING, remaining)
        else:
            reason = _poll_code_reason(code)
            session._emit(AUTH_LOGIN_FAILED, reason)
            return FuncResult(type=FuncType.FAIL, result=reason)

        time.sleep(POLL_INTERVAL)

    reason = "登录超时"
    session._emit(AUTH_LOGIN_FAILED, reason)
    return FuncResult(type=FuncType.FAIL, result=reason)


def auth_validate_login(session: Session) -> FuncResult:
    """验证当前 cookies 是否有效。

    通过调用一个需要登录态的 API 来验证。
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录（无 cookies）")

    try:
        res = api(
            type=ApiType.GET,
            url=ApiUrl.GET_WBI_KEY,
            cookies=session.cookies,
        )
    except API_BILI_CODE_ERROR:
        return FuncResult(type=FuncType.FAIL, result="登录已过期")

    if not res.cookies:
        return FuncResult(type=FuncType.FAIL, result="登录状态无效")
    return FuncResult(type=FuncType.SUCCESS, result=res.data)


def auth_logout(session: Session) -> FuncResult:
    """登出，清除 cookies 和相关状态。

    副作用：emit auth:logout_done
    """
    session.config.cookies = {}
    session.config.csrf = ""
    session.config.refresh_token = ""
    session.config.uid = 0
    session._emit(AUTH_LOGOUT_DONE)
    return FuncResult(type=FuncType.SUCCESS, result="登出成功")


def _poll_code_reason(code: Optional[int]) -> str:
    code_map = {
        86038: "二维码已过期",
        86039: "二维码无效",
    }
    return code_map.get(code or 0, f"登录失败（code={code}）")

"""直播管理编排

组合基础层直播 API（开播、下播、改标题、刷新信息），
通过 session._emit 推送事件给用户层，同时返回 FuncResult 供 CLI 同步获取。
"""

from __future__ import annotations

from ..utils.api import (
    api_get_area_list,
    api_get_room_data,
    api_get_room_id,
    api_start_live,
    api_stop_live,
    api_update_room,
)
from ..utils.data import FuncResult, FuncType, AppState
from ..utils.constant import SessionEvent
from .session import Session


def live_start(session: Session, area_id: int) -> FuncResult:
    """开播。

    Args:
        session: 会话实例
        area_id: 开播分区 ID（0 表示使用 config 中已有的 area_id）

    如果 session.room_id 为 0，会先通过 api_get_room_id 自动获取。
    遇到人脸认证错误时 emit LIVE_FACE_AUTH_REQUIRED 事件。

    Returns:
        FuncResult(SUCCESS, {rtmp_addr, rtmp_code, ...}) 或 FAIL/ERROR

    副作用：emit live:state_changed / live:face_auth_required
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法开播")

    # 自动获取 room_id
    if session.room_id == 0 and session.user_id:
        id_result = api_get_room_id(
            cookies=session.cookies, user_id=session.user_id
        )
        if id_result.type == FuncType.SUCCESS:
            session.config.room_id = id_result.result

    if session.room_id == 0:
        return FuncResult(type=FuncType.FAIL, result="未设置房间号，且无法自动获取")

    result = api_start_live(
        cookies=session.cookies,
        user_id=session.user_id,
        room_id=session.room_id,
        area_id=area_id,
    )
    if result.type != FuncType.SUCCESS:
        data = result.result
        if isinstance(data, dict) and data.get("face_auth"):
            session._emit(
                SessionEvent.LIVE_FACE_AUTH_REQUIRED,
                data.get("qr_url", ""),
            )
        return result

    data = result.result
    session.config.rtmp_addr = data.get("rtmp_addr", "")
    session.config.rtmp_code = data.get("rtmp_code", "")
    session.app_state = AppState.LIVE

    room_info = {
        "room_id": session.room_id,
        "area_id": area_id,
        "rtmp_addr": session.config.rtmp_addr,
        "rtmp_code": session.config.rtmp_code,
    }
    session._emit(SessionEvent.LIVE_STATE_CHANGED, True, room_info)
    return result


def live_stop(session: Session) -> FuncResult:
    """下播。

    Returns:
        FuncResult(SUCCESS) 或 FAIL/ERROR

    副作用：emit live:state_changed(False, room_info)
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法下播")

    result = api_stop_live(cookies=session.cookies, room_id=session.room_id)
    if result.type != FuncType.SUCCESS:
        return result

    session.app_state = AppState.IDLE
    session._emit(SessionEvent.LIVE_STATE_CHANGED, False, {"room_id": session.room_id})
    return result


def live_update_title(session: Session, new_title: str) -> FuncResult:
    """修改直播标题。

    Args:
        session: 会话
        new_title: 新标题

    Returns:
        FuncResult(SUCCESS) 或 FAIL/ERROR

    副作用：emit live:info_updated(room_info)
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法修改标题")

    result = api_update_room(
        cookies=session.cookies,
        room_id=session.room_id,
        title=new_title,
    )
    if result.type != FuncType.SUCCESS:
        return result

    session.config.title = new_title
    room_info = {"room_id": session.room_id, "title": new_title}
    session._emit(SessionEvent.LIVE_INFO_UPDATED, room_info)
    return result


def live_update_area(session: Session, area_id: int) -> FuncResult:
    """修改直播分区。

    Returns:
        FuncResult(SUCCESS) 或 FAIL/ERROR

    副作用：emit live:info_updated(room_info)
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法修改分区")

    result = api_update_room(
        cookies=session.cookies,
        room_id=session.room_id,
        area_id=area_id,
    )
    if result.type != FuncType.SUCCESS:
        return result

    session.config.area_id = area_id
    room_info = {"room_id": session.room_id, "area_id": area_id}
    session._emit(SessionEvent.LIVE_INFO_UPDATED, room_info)
    return result


def live_refresh_room_info(session: Session) -> FuncResult:
    """刷新房间信息。

    Returns:
        FuncResult(SUCCESS, {room_data}) 或 FAIL/ERROR

    副作用：emit live:info_updated(room_info)
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法获取房间信息")

    result = api_get_room_data(
        cookies=session.cookies,
        room_id=session.room_id,
    )
    if result.type != FuncType.SUCCESS:
        return result

    session.config.room_data = result.result or {}
    session._emit(SessionEvent.LIVE_INFO_UPDATED, session.config.room_data)
    return result


def live_get_room_info_cache(session: Session) -> FuncResult:
    """获取当前缓存的房间信息（不发起网络请求）。

    Returns:
        FuncResult(SUCCESS, room_data) 或 FAIL
    """
    if not session.config.room_data:
        return FuncResult(type=FuncType.FAIL, result="尚无房间数据，请先调用 live_refresh_room_info")
    return FuncResult(type=FuncType.SUCCESS, result=session.config.room_data)


def live_get_area_list(session: Session) -> FuncResult:
    """获取直播分区列表。

    Returns:
        FuncResult(SUCCESS, LiveAreaList) 或 FAIL
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法获取分区列表")
    return api_get_area_list(cookies=session.cookies)

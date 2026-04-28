"""直播管理编排"""

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

    session.room_id 为 0 时会自动通过 uid 获取房间号。
    遇到人脸认证时发送 LIVE_FACE_AUTH_REQUIRED 事件并返回 FAIL。

    Args:
        session: Session 实例
        area_id: 分区 ID

    返回: FuncResult(SUCCESS, {rtmp_addr, rtmp_code}) 或 FAIL
    触发: 成功发 LIVE_STATE_CHANGED；人脸认证发 LIVE_FACE_AUTH_REQUIRED(qr_url)
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法开播")
    if session.room_id == 0 and session.user_id:
        id_result = api_get_room_id(cookies=session.cookies, user_id=session.user_id)
        if id_result.type == FuncType.SUCCESS:
            session.config.room_id = id_result.result
    if session.room_id == 0:
        return FuncResult(type=FuncType.FAIL, result="未设置房间号，且无法自动获取")
    result = api_start_live(cookies=session.cookies, user_id=session.user_id, room_id=session.room_id, area_id=area_id)
    if result.type != FuncType.SUCCESS:
        data = result.result
        if isinstance(data, dict) and data.get("face_auth"):
            session._emit(SessionEvent.LIVE_FACE_AUTH_REQUIRED, data.get("qr_url", ""))
        return result
    data = result.result
    session.config.rtmp_addr = data.get("rtmp_addr", "")
    session.config.rtmp_code = data.get("rtmp_code", "")
    session.app_state = AppState.LIVE
    session._emit(SessionEvent.LIVE_STATE_CHANGED, True, {"room_id": session.room_id, "area_id": area_id})
    return result


def live_stop(session: Session) -> FuncResult:
    """下播。

    Args:
        session: Session 实例

    返回: FuncResult(SUCCESS) 或 FAIL
    触发: 发送 LIVE_STATE_CHANGED(False)
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法下播")
    result = api_stop_live(cookies=session.cookies, room_id=session.room_id)
    if result.type != FuncType.SUCCESS:
        return result
    session.app_state = AppState.IDLE
    session._emit(SessionEvent.LIVE_STATE_CHANGED, False, {"room_id": session.room_id})
    return result


def live_update_room(session: Session, title: str | None = None, area_id: int | None = None) -> FuncResult:
    """修改直播间标题和/或分区，一次 API 调用完成。

    两个参数均为 None 时不发请求直接返回 FAIL。

    Args:
        session: Session 实例
        title: 新标题，可选
        area_id: 新分区 ID，可选

    返回: FuncResult(SUCCESS) 或 FAIL
    触发: 发送 LIVE_INFO_UPDATED
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法修改")
    if not title and not area_id:
        return FuncResult(type=FuncType.FAIL, result="未提供标题或分区ID")
    result = api_update_room(cookies=session.cookies, room_id=session.room_id, title=title, area_id=area_id)
    if result.type != FuncType.SUCCESS:
        return result
    if title:
        session.config.title = title
    if area_id:
        session.config.area_id = area_id
    session._emit(SessionEvent.LIVE_INFO_UPDATED, {"title": title, "area_id": area_id})
    return result


def live_refresh_room_info(session: Session) -> FuncResult:
    """从 B站 API 拉取最新房间数据，写入 session.config.room_data。

    Args:
        session: Session 实例

    返回: FuncResult(SUCCESS, room_data) 或 FAIL
    触发: 发送 LIVE_INFO_UPDATED
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法获取房间信息")
    result = api_get_room_data(cookies=session.cookies, room_id=session.room_id)
    if result.type != FuncType.SUCCESS:
        return result
    session.config.room_data = result.result or {}
    session._emit(SessionEvent.LIVE_INFO_UPDATED, session.config.room_data)
    return result


def live_get_room_info_cache(session: Session) -> FuncResult:
    """读取缓存的房间数据，不发起网络请求。

    Args:
        session: Session 实例

    返回: FuncResult(SUCCESS, room_data)，无缓存时返回 FAIL
    """
    if not session.config.room_data:
        return FuncResult(type=FuncType.FAIL, result="尚无房间数据，请先调用 live_refresh_room_info")
    return FuncResult(type=FuncType.SUCCESS, result=session.config.room_data)


def live_get_area_list(session: Session) -> FuncResult:
    """获取直播分区列表。

    Args:
        session: Session 实例

    返回: FuncResult(SUCCESS, LiveAreaList) 或 FAIL
    """
    if not session.is_logged_in:
        return FuncResult(type=FuncType.FAIL, result="未登录，无法获取分区列表")
    return api_get_area_list(cookies=session.cookies)

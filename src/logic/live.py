"""直播管理编排"""

from ..utils.api import (
    api_get_room_id,
    api_get_area_list,
    api_get_room_data,
    api_start_live,
    api_stop_live,
    api_update_room,
)
from ..utils.data import FuncResult, FuncType, AppState
from ..utils.constant import SessionEvent
from .session import Session


def live_init(session: Session) -> FuncResult:
    """开播准备

    准备开播所需要的信息，需要已登录

    Args:
        session: Session 实例
    Events:
        LIVE_AREA_UPDATED: 分区列表更新
        LIVE_INFO_UPDATED: 直播间数据更新
        LIVE_AREA_UPDATED_FAIL
        LIVE_INFO_UPDATED_FAIL
    Returns:
        FuncResult(SUCCESS) 或 FAIL
    """
    if not session.is_login:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, "未登录")
        session._emit(SessionEvent.LIVE_AREA_UPDATED_FAIL, "未登录")
        return FuncResult(type=FuncType.FAIL, result="未登录")
    # 获取分区列表
    res = api_get_area_list(cookies=session.config.cookies)
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.LIVE_AREA_UPDATED_FAIL, "获取分区列表失败")
        return FuncResult(type=FuncType.FAIL, result="获取分区列表失败")
    session.area_list = res.result
    session._emit(SessionEvent.LIVE_AREA_UPDATED)
    # 获取直播间号
    res = api_get_room_id(cookies=session.config.cookies, user_id=session.config.uid)
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, "获取直播间号失败")
        return FuncResult(type=FuncType.FAIL, result="获取直播间号失败")
    session.config.room_id = res.result
    # 获取直播间信息
    res = api_get_room_data(
        cookies=session.config.cookies, room_id=session.config.room_id
    )
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, "获取直播间信息失败")
        return FuncResult(type=FuncType.FAIL, result="获取直播间信息失败")
    session.room_data = res.result
    session.config.room_id = res.result.get("room_id", 0)
    session.config
    session._emit(SessionEvent.LIVE_INFO_UPDATED, {"room_data": session.room_data})
    return FuncResult(type=FuncType.SUCCESS)


def live_start(session: Session, area_id: int = 0) -> FuncResult:
    """开播。

    遇到人脸认证时发送 LIVE_FACE_AUTH_REQUIRED 事件并返回 FAIL。

    Args:
        session: Session 实例
        area_id: 分区 ID
    Events:
        LIVE_STATE_CHANGED
        LIVE_FACE_AUTH_REQUIRED: 需要人脸识别
        LIVE_START_FAIL
    Returns:
        FuncResult(SUCCESS, {rtmp_addr, rtmp_code}) 或 FAIL
    """
    if not session.can_live:
        session._emit(SessionEvent.LIVE_START_FAIL, "开播信息不全，无法开播")
        return FuncResult(type=FuncType.FAIL, result="开播信息不全，无法开播")
    area_id = area_id if area_id else session.config.area_id
    if not area_id:
        session._emit(SessionEvent.LIVE_START_FAIL, "没有分区id，无法开播")
        return FuncResult(type=FuncType.FAIL, result="没有分区id，无法开播")
    res = api_start_live(
        cookies=session.config.cookies,
        user_id=session.config.uid,
        room_id=session.config.room_id,
        area_id=area_id,
    )
    data = res.result
    if res.type != FuncType.SUCCESS:
        if isinstance(data, dict) and data.get("face_auth"):
            session.cache_face_qr_url = data.get("qr_url", "")
            session._emit(
                SessionEvent.LIVE_FACE_AUTH_REQUIRED, {"qr_url": data.get("qr_url", "")}
            )
        else:
            session._emit(SessionEvent.LIVE_START_FAIL, str(res.result))
        return res
    session.config.rtmp_addr = data.get("rtmp_addr", "")
    session.config.rtmp_code = data.get("rtmp_code", "")
    session.app_state = AppState.LIVE
    session._emit(
        SessionEvent.LIVE_STATE_CHANGED,
        {
            "app_state": AppState.LIVE.value,
            "rtmp_addr": session.config.rtmp_addr,
            "rtmp_code": session.config.rtmp_code,
        },
    )
    return res


def live_stop(session: Session) -> FuncResult:
    """下播。

    Args:
        session: Session 实例
    Events:
        LIVE_STATE_CHANGED
        LIVE_STOP_FAIL
    Returns:
        FuncResult(SUCCESS) 或 FAIL
    """
    if not session.is_login:
        session._emit(SessionEvent.LIVE_STOP_FAIL, "未登录，无法下播")
        return FuncResult(type=FuncType.FAIL, result="未登录，无法下播")
    if not session.is_live and not session.is_replay:
        session._emit(SessionEvent.LIVE_STOP_FAIL, "未开播，无法下播")
        return FuncResult(type=FuncType.FAIL, result="未开播，无法下播")
    res = api_stop_live(cookies=session.config.cookies, room_id=session.config.room_id)
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.LIVE_STOP_FAIL, str(res.result))
        return res
    session.app_state = AppState.IDLE
    session._emit(SessionEvent.LIVE_STATE_CHANGED, {"app_state": AppState.IDLE.value})
    return res


def live_update_room(
    session: Session, title: str | None = None, area_id: int | None = None
) -> FuncResult:
    """修改直播间标题或分区，一次 API 调用完成。

    两个参数均为 None 时不发请求直接返回 FAIL。

    Args:
        session: Session 实例
        title: 新标题，可选
        area_id: 新分区 ID，可选
    Events:
        LIVE_INFO_UPDATED
        LIVE_INFO_UPDATED_FAIL
    Returns:
        FuncResult(SUCCESS) 或 FAIL
    """
    if not session.is_login:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, "未登录，无法修改直播间信息")
        return FuncResult(type=FuncType.FAIL, result="未登录，无法修改直播间信息")
    if not title and not area_id:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, "未提供标题或分区ID")
        return FuncResult(type=FuncType.FAIL, result="未提供标题或分区ID")
    res = api_update_room(
        cookies=session.config.cookies,
        room_id=session.config.room_id,
        title=title,
        area_id=area_id,
    )
    if res.type != FuncType.SUCCESS:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, str(res.result))
        return res
    if title:
        session.config.title = title
    if area_id:
        session.config.area_id = area_id
    session._emit(SessionEvent.LIVE_INFO_UPDATED, {"title": title, "area_id": area_id})
    return res


def live_refresh_room_data(session: Session) -> FuncResult:
    """从 B站 API 拉取最新房间数据，写入 session.room_data。

    Args:
        session: Session 实例
    Events:
        LIVE_INFO_UPDATED
        LIVE_INFO_UPDATED_FAIL
    Returns:
        FuncResult(SUCCESS, room_data) 或 FAIL
    """
    if not session.is_login:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, "未登录，无法获取直播间信息")
        return FuncResult(type=FuncType.FAIL, result="未登录，无法获取直播间信息")
    result = api_get_room_data(
        cookies=session.config.cookies, room_id=session.config.room_id
    )
    if result.type != FuncType.SUCCESS:
        session._emit(SessionEvent.LIVE_INFO_UPDATED_FAIL, str(result.result))
        return result
    session.room_data = result.result or {}
    session._emit(SessionEvent.LIVE_INFO_UPDATED, {"room_data": session.room_data})
    return result

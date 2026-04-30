"""CLI 直播命令处理"""

from rich import print

from ..logic import (
    live_start,
    live_stop,
    live_refresh_room_data,
    live_update_room,
    auth_update_safety,
    live_init,
)
from ..utils.constant import SessionEvent
from ..utils.lib import generate_qr_text

async def handle_live_start(session, area, title) -> None:
    area = area if area else session.config.area_id
    if area == 0:
        print("请使用 -a 指定分区ID，或先用 --update -a 保存分区ID。")
        print("可用 --area 查看分区列表。")
        return

    captured = {}

    def on_state_changed(data):
        captured["event"] = "state_changed"
        captured["data"] = data or {}

    def on_face_auth(data):
        captured["event"] = "face_auth"
        captured["data"] = data or {}

    def on_info_updated(data):
        captured["event"] = "info_updated"

    def on_fail(msg):
        captured["event"] = "fail"
        captured["msg"] = str(msg) if msg else "开播失败"

    session.once(SessionEvent.LIVE_STATE_CHANGED, on_state_changed)
    session.once(SessionEvent.LIVE_FACE_AUTH_REQUIRED, on_face_auth)
    session.once(SessionEvent.LIVE_START_FAIL, on_fail)
    live_start(session, area_id=area)

    if captured.get("event") == "state_changed":
        data = captured["data"]
        print("开播成功")
        rtmp = data.get("rtmp_addr", "")
        code = data.get("rtmp_code", "")
        if rtmp:
            print(f"推流地址: {rtmp}")
            print(f"推流码:   {code}")
        if title:
            session.once(SessionEvent.LIVE_INFO_UPDATED, on_info_updated)
            session.once(SessionEvent.LIVE_INFO_UPDATED_FAIL, on_fail)
            live_update_room(session, title=title)

            if captured.get("event") == "info_updated":
                print("更新标题成功")
    elif captured.get("event") == "face_auth":
        qr = captured["data"].get("qr_url", "")
        print("需要人脸认证:")
        print("\n".join(generate_qr_text(qr)))
        print("完成人脸验证后，重新尝试开播")
    else:
        print(captured.get("msg", "开播失败"))


async def handle_live_stop(session) -> None:
    captured = {}

    def on_state_changed(data):
        captured["event"] = "state_changed"

    def on_fail(msg):
        captured["event"] = "fail"
        captured["msg"] = str(msg) if msg else "下播失败"

    session.once(SessionEvent.LIVE_STATE_CHANGED, on_state_changed)
    session.once(SessionEvent.LIVE_STOP_FAIL, on_fail)
    live_stop(session)

    if captured.get("event") == "state_changed":
        print("下播成功")
    else:
        print(captured.get("msg", "下播失败"))


async def handle_live_status(session) -> None:
    captured = {}

    def on_updated(data):
        captured["event"] = "updated"

    def on_fail(msg):
        captured["event"] = "fail"
        captured["msg"] = str(msg) if msg else "获取状态失败"

    session.once(SessionEvent.LIVE_INFO_UPDATED, on_updated)
    session.once(SessionEvent.LIVE_INFO_UPDATED_FAIL, on_fail)
    live_refresh_room_data(session)

    if captured.get("event") == "fail":
        print(captured["msg"])
        return

    data = session.room_data
    is_live = data.get("live_status")
    print(f"房间号: {data.get('room_id', '?')}")
    print(f"标题:   {data.get('title', '?')}")
    print(f"分区:   {data.get('area_name', '?')} (id={data.get('area_id', '?')})")
    status_map = {0: "未开播", 1: "直播中", 2: "轮播中"}
    print(f"状态:   {status_map.get(is_live, f'未知({is_live})')}")
    if is_live:
        live_time = data.get("live_time", "00:00:00")
        if live_time and live_time != "0000-00-00 00:00:00":
            print(f"直播时长: {live_time}")
    online = data.get("online", 0)
    if online:
        print(f"当前观众: {online}")


async def handle_update(session, area_id, title) -> None:
    if not title and not area_id:
        print("请指定 -a 和/或 -t")
        return

    captured = {}

    def on_updated(data):
        captured["event"] = "updated"

    def on_fail(msg):
        captured["event"] = "fail"
        captured["msg"] = str(msg) if msg else "修改失败"

    session.once(SessionEvent.LIVE_INFO_UPDATED, on_updated)
    session.once(SessionEvent.LIVE_INFO_UPDATED_FAIL, on_fail)
    live_update_room(session, title=title, area_id=area_id)

    if captured.get("event") == "fail":
        print(captured["msg"])
        return

    if title:
        print(f"标题已更新: {title}")
    if area_id:
        print(f"分区已更新: {area_id}")


async def handle_area(session, parent_id: int) -> None:
    area_list = session.area_list
    if not area_list:
        print("分区列表为空，请先登录")
        return

    for main in area_list:
        if parent_id == 0:
            print(f"  [{main.id}] {main.name}")
        elif main.id == parent_id:
            print(f"  [{main.id}] {main.name}")
            for sub in main.list:
                print(f"    [{sub.id}] {sub.name}")


async def handle_cli(session) -> None:
    if not session.is_login:
        from .auth import handle_login as _do_login

        if not await _do_login(session):
            return
        auth_update_safety(session)
        live_init(session)

    if session.config.room_id == 0:
        print("房间号未知，开播时将自动获取")

    status_captured = {}

    def on_status_updated(data):
        status_captured["event"] = "updated"

    def on_status_fail(msg):
        status_captured["event"] = "fail"
        status_captured["msg"] = str(msg) if msg else "获取状态失败"

    session.once(SessionEvent.LIVE_INFO_UPDATED, on_status_updated)
    session.once(SessionEvent.LIVE_INFO_UPDATED_FAIL, on_status_fail)
    live_refresh_room_data(session)

    if status_captured.get("event") == "fail":
        print(status_captured["msg"])
        return

    rd = session.room_data
    if rd.get("area_id"):
        session.config.area_id = rd["area_id"]
    if rd.get("title"):
        session.config.title = rd["title"]
    is_live = rd.get("live_status")

    if is_live:
        print("当前正在直播")
    else:
        print("正在开播...")
        await handle_live_start(session, None, None)

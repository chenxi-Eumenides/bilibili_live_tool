from time import time
from typing import AsyncGenerator, Optional

from requests import HTTPError, Response, get, post
from websockets import ClientConnection, ConnectionClosedError, State, connect

from .constant import BILI_TICKET_KEY, ApiData, ApiUrl, BiliCode, Tuning
from .data import (
    ApiResult,
    ApiType,
    FuncResult,
    FuncType,
    LiveAreaList,
    WebSocketMessage,
    WebSocketOperation,
    WebSocketProtoVer,
)
from .error import (
    API_ARG_ERROR,
    API_BILI_CODE_ERROR,
    API_DATA_ERROR,
    API_STATUS_CODE_ERROR,
    FAIL_BILI_CODE,
    FUNC_DATA_ERROR,
)
from .lib import (
    encWbi,
    hmac_sha256,
    pack_ws_body,
    random_cooldown,
    sign_data,
    unpack_ws_message,
)


@random_cooldown()
def api(
    type: ApiType,
    url: str,
    cookies: Optional[dict] = None,
    headers: dict = ApiData.HEADERS,
    params: Optional[dict] = None,
    data: Optional[dict] = None,
) -> ApiResult:
    """
    请求api

    Args:
        type: 请求方式
        url: 请求url路径
        cookies: Cookies字典
        headers: 请求头
        params: 请求参数
        data: 请求数据
    Raises:
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        ApiResult: api返回数据
    """
    try:
        if type == ApiType.POST:
            res = post(
                url=url,
                params=params,
                cookies=cookies,
                headers=headers,
                data=data,
                timeout=Tuning.API_TIMEOUT,
            )
        elif type == ApiType.GET:
            res = get(
                url=url,
                params=params,
                cookies=cookies,
                headers=headers,
                data=data,
                timeout=Tuning.API_TIMEOUT,
            )
        res.raise_for_status()
    except HTTPError as e:
        raise API_STATUS_CODE_ERROR(
            e.response.status_code, f"请求API失败，状态码: {e.response.status_code}"
        )
    if not res.ok:
        raise API_STATUS_CODE_ERROR(
            res.status_code, f"请求API失败，状态码: {res.status_code}"
        )
    raise_for_bili_code(res)
    return ApiResult.from_response(res)


def raise_for_bili_code(response: Response):
    """raise `API_BILI_CODE_ERROR`"""
    result = response.json()
    code = result.get("code")
    if isinstance(code, int):
        code = abs(code)
    msg = result.get("msg")
    data = result.get("data")
    if code in FAIL_BILI_CODE.keys():
        mapped = FAIL_BILI_CODE[code]
        display = f"{mapped}" if not msg or mapped == msg else f"{msg} (code={code}: {mapped})"
        raise API_BILI_CODE_ERROR(
            code=code,
            api_msg=msg,
            msg=f"api请求错误({code}): {display}",
            data=data,
        )
    elif code == 0 and isinstance(data, dict) and data.get("code"):
        code = data["code"]
        msg = data.get("message", "")
        raise API_BILI_CODE_ERROR(
            code=code,
            api_msg=msg,
            msg=f"api请求错误({code}): {msg}{' (' + FAIL_BILI_CODE.get(code, '') + ')' if FAIL_BILI_CODE.get(code) else ''}",
            data=data,
        )
    elif int(code) != 0:
        raise API_BILI_CODE_ERROR(
            code=int(code),
            api_msg=msg,
            msg=f"api请求错误({code}){': api信息: ' + msg if msg else ''}",
            data=data,
        )


def api_start_live(
    cookies: dict, user_id: int, room_id: int, area_id: int
) -> FuncResult:
    """
    开播api

    Args:
        cookies: cookies字典
        room_id: 房间号
        area_id: 开播分区
    Raises:
        API_ARG_ERROR: 参数不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult:
            SUCCESS: {
                face_auth: bool,
                rtmp_addr: str,
                rtmp_code: str,
                live_build: str,
                live_version: str,
            }
            FAIL: {
                face_auth: bool,
                qr_url: str,
                v_voucher: str,
            }
    """
    if not (csrf := cookies.get("bili_jct")):
        raise API_ARG_ERROR("cookies错误，不存在 bili_jct 项")
    # 获取直播姬信息
    res = api(
        type=ApiType.GET,
        url=ApiUrl.GET_LIVE_VERSION,
        cookies=cookies,
        params=sign_data({"system_version": 2}),
    )
    if res.data:
        live_build = res.data.get("build", ApiData.LIVEHIME_BUILD)
        live_version = res.data.get("curr_version", ApiData.LIVEHIME_VERSION)
    else:
        live_build = ApiData.LIVEHIME_BUILD
        live_version = ApiData.LIVEHIME_VERSION
    # 请求开播api
    data = {
        "room_id": room_id,
        "platform": ApiData.PLATFORM,
        "area_v2": area_id,
        "csrf_token": csrf,
        "csrf": csrf,
        "type": 2,
        "build": live_build,
        "version": live_version,
    }
    try:
        res = api(
            type=ApiType.POST,
            url=ApiUrl.START_LIVE,
            cookies=cookies,
            data=sign_data(data),
        )
    except API_BILI_CODE_ERROR as e:
        if e.code == BiliCode.FACE_AUTH_REQUIRED:
            qr_url = e.data.get("qr")
        elif e.code == BiliCode.FACE_AUTH_VERIFY:
            qr_url = f"https://www.bilibili.com/blackboard/live/face-auth-middle.html?source_event=400&mid={user_id}"
        else:
            raise e
        if "v_voucher" in e.data.keys():
            v_voucher = e.data["v_voucher"]
        elif "v_voucher" in e.data.get("risk_extra", {}).keys():
            v_voucher = e.data["risk_extra"]["v_voucher"]
        else:
            v_voucher = None
        if qr_url:
            return FuncResult(
                type=FuncType.FAIL,
                result={
                    "face_auth": True,
                    "qr_url": qr_url,
                    "v_voucher": v_voucher,
                },
            )
        else:
            raise API_DATA_ERROR("获取人脸识别地址为空，可能是因为风控")
    if (
        not res.data
        or not (rtmp := res.data.get("rtmp"))
        or not (rtmp_addr := rtmp.get("addr"))
        or not (rtmp_code := rtmp.get("code"))
    ):
        raise API_DATA_ERROR("请求结果错误，未获取到rtmp地址和推流码")
    return FuncResult(
        type=FuncType.SUCCESS,
        result={
            "face_auth": False,
            "rtmp_addr": rtmp_addr,
            "rtmp_code": rtmp_code,
            "live_build": live_build,
            "live_version": live_version,
        },
    )


def api_stop_live(cookies: dict, room_id: int) -> FuncResult:
    """
    下播api

    Args:
        cookies: cookies字典
        room_id: 房间号
    Raises:
        API_ARG_ERROR: 参数不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: api返回数据
    """
    if not (csrf := cookies.get("bili_jct")):
        raise API_ARG_ERROR("cookies错误，不存在 bili_jct 项")
    data = {
        "room_id": room_id,
        "platform": ApiData.PLATFORM,
        "csrf_token": csrf,
        "csrf": csrf,
    }
    res = api(
        type=ApiType.POST,
        url=ApiUrl.STOP_LIVE,
        cookies=cookies,
        data=data,
    )
    return FuncResult(type=FuncType.SUCCESS, result=res.data)


def api_update_room(
    cookies: dict,
    room_id: int,
    title: Optional[str] = None,
    area_id: Optional[int] = None,
) -> FuncResult:
    """
    更新标题api

    Args:
        cookies: cookies字典
        room_id: 房间号
        title: 标题
        area_id: 分区ID
    Raises:
        API_ARG_ERROR: 参数不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: api返回数据
    """
    if not (csrf := cookies.get("bili_jct")):
        raise API_ARG_ERROR("cookies错误，不存在 bili_jct 项")
    if not title and not area_id:
        raise API_ARG_ERROR(f"未提供标题({title})或分区ID({area_id})")
    data = {
        "room_id": room_id,
        "platform": ApiData.PLATFORM,
        "activity_id": 0,
        "csrf_token": csrf,
        "csrf": csrf,
    }
    if title:
        data.update({"title": title})
    if area_id:
        data.update({"room_id": room_id})
    res = api(
        type=ApiType.POST,
        url=ApiUrl.UPDATE_ROOM,
        cookies=cookies,
        data=data,
    )
    return FuncResult(type=FuncType.SUCCESS, result=res.data)


def api_get_room_data(cookies: dict, room_id: int) -> FuncResult:
    """
    获取直播间数据api

    Args:
        cookies: cookies字典
        room_id: 房间号
    Raises:
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: api返回数据
    """
    data = {"room_id": room_id}
    res = api(
        type=ApiType.POST,
        url=ApiUrl.GET_ROOM_DATA,
        cookies=cookies,
        data=data,
    )
    if not res.data:
        raise API_DATA_ERROR("未获取到直播间数据")
    result = {
        "user_id": res.data.get("uid"),
        "room_id": res.data.get("room_id"),
        "attention": res.data.get("attention"),
        "online": res.data.get("online"),
        "description": res.data.get("description"),
        "live_status": res.data.get("live_status"),
        "area_id": res.data.get("area_id"),
        "parent_area_id": res.data.get("parent_area_id"),
        "title": res.data.get("title"),
        "live_time": res.data.get("live_time"),
        "tags": res.data.get("tags"),
        "pk_status": res.data.get("pk_status"),
        "pk_id": res.data.get("pk_id"),
        "allow_change_area_time": res.data.get("allow_change_area_time"),
        "area_name": res.data.get("area_name"),
        "parent_area_name": res.data.get("parent_area_name"),
    }
    return FuncResult(type=FuncType.SUCCESS, result=result)


def api_get_area_list(cookies: dict) -> FuncResult:
    """
    获取直播分区api

    Args:
        cookies: cookies字典
    Raises:
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: LiveAreaList
    """
    res = api(
        type=ApiType.GET,
        url=ApiUrl.GET_AREA_LIST,
        cookies=cookies,
    )
    if not res.data:
        raise API_DATA_ERROR("未获取到直播分区数据")

    return FuncResult(type=FuncType.SUCCESS, result=LiveAreaList.from_api(res.data))


def api_get_room_id(cookies: dict, user_id: int) -> FuncResult:
    """
    获取直播间IDapi

    Args:
        cookies: cookies字典
        user_id: 用户ID
    Raises:
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: room_id
    """
    data = {"uid": user_id}
    res = api(
        type=ApiType.GET,
        url=ApiUrl.GET_ROOM_ID,
        cookies=cookies,
        params=data,
    )
    if not res.data or not (room_id := res.data.get("room_id")):
        raise API_DATA_ERROR("未获取到直播间ID")
    return FuncResult(type=FuncType.SUCCESS, result=room_id)


def api_get_login_qr() -> FuncResult:
    """
    获取登录二维码api

    Raises:
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: {
            qr_url: str
            qr_key: str
        }
    """
    res = api(
        type=ApiType.GET,
        url=ApiUrl.GENERATE_QR,
    )
    if (
        not res.data
        or not (qr_url := res.data.get("url"))
        or not (qr_key := res.data.get("qrcode_key"))
    ):
        raise API_DATA_ERROR("未获取到登录二维码数据")
    return FuncResult(
        type=FuncType.SUCCESS,
        result={
            "qr_url": qr_url,
            "qr_key": qr_key,
        },
    )


def api_check_login(qr_key: str) -> FuncResult:
    """
    检查登录二维码api

    Args:
        qr_key: 二维码key
    Raises:
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: {
            cookies: dict
            refresh_token: str
        }
    """
    params = {"qrcode_key": qr_key}
    try:
        res = api(
            type=ApiType.GET,
            url=ApiUrl.GET_QR_RES,
            params=params,
        )
    except API_BILI_CODE_ERROR as e:
        if e.code not in [BiliCode.LOGIN_QR_SCANNED, BiliCode.LOGIN_QR_WAITING]:
            raise e
        return FuncResult(type=FuncType.FAIL, result=e.code)
    if not res.cookies or not res.data:
        raise API_DATA_ERROR("未获取到cookie，登录失败")
    return FuncResult(
        type=FuncType.SUCCESS,
        result={
            "cookies": res.cookies,
            "refresh_token": res.data.get("refresh_token"),
        },
    )


def api_check_face_auth(cookies: dict, room_id: int) -> FuncResult:
    """
    检查人脸认证api

    Args:
        cookies: cookies字典
        room_id: 房间号
    Raises:
        API_ARG_ERROR: 参数不正确
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: api返回数据
    """
    if not (csrf := cookies.get("bili_jct")):
        raise API_ARG_ERROR("cookies错误，不存在 bili_jct 项")
    data = {
        "room_id": room_id,
        "face_auth_code": "60024",
        "csrf_token": csrf,
        "csrf": csrf,
        "visit_id": "",
    }
    res = api(
        type=ApiType.POST,
        url=ApiUrl.FACE_AUTH,
        cookies=cookies,
        data=data,
    )
    if not res.data:
        raise API_DATA_ERROR(f"无法获得人脸认证结果 {res.data}")
    return FuncResult(
        type=FuncType.SUCCESS if res.data.get("is_identified") else FuncType.FAIL,
        result=res.data,
    )


def get_bili_ticket(cookies: dict) -> FuncResult:
    if not (csrf := cookies.get("bili_jct")):
        raise API_ARG_ERROR("cookies错误，不存在 bili_jct 项")
    now_time = int(time())
    params = {
        "key_id": "ec02",
        "hexsign": hmac_sha256(
            BILI_TICKET_KEY,
            f"ts{now_time}",
        ),
        "context[ts]": now_time,
        "csrf": csrf,
    }
    res = api(
        type=ApiType.POST,
        url=ApiUrl.GET_BILI_TICKET,
        cookies=cookies,
        params=params,
    )
    if not res.data:
        raise API_DATA_ERROR(f"无法获得bili_ticket数据 {res.data}")
    return FuncResult(
        type=FuncType.SUCCESS,
        result={
            "bili_ticket": res.data.get("ticket"),
            "created_at": res.data.get("created_at"),
            "ttl": res.data.get("ttl"),
            "img_key": res.data.get("nav", {}).get("img"),
            "sub_key": res.data.get("nav", {}).get("sub"),
        },
    )


def api_get_user_nav(cookies: dict) -> FuncResult:
    """获取用户导航信息，用于验证 cookies 是否有效。

    Args:
        cookies: cookies字典
    Returns:
        FuncResult: {
            following: 关注数
            follower: 粉丝数
            dynamic_count: 动态数
        }
    """
    try:
        res = api(
            type=ApiType.GET,
            url=ApiUrl.GET_USER_STATUS,
            cookies=cookies,
        )
    except API_BILI_CODE_ERROR as e:
        return FuncResult(type=FuncType.FAIL, result={})
    if not res.data:
        raise API_DATA_ERROR("无法获取登录状态")
    return FuncResult(type=FuncType.SUCCESS, result=res.data)


def get_wbi_key(cookies: dict) -> FuncResult:
    """
    获取B站wbi签名密钥

    Args:
        cookies: cookies字典
        real_room_id: 真实房间号
    Raises:
        API_ARG_ERROR: 参数不正确
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: {
            img_key: str
            sub_key: str
        }
    """
    res = api(
        type=ApiType.GET,
        url=ApiUrl.GET_WBI_KEY,
        cookies=cookies,
    )
    if not res.data or res.data.get("wbi_img") is None:
        raise API_DATA_ERROR("获取wbi签名密钥失败")
    wbi_img = res.data["wbi_img"]
    img_key = wbi_img["img_url"].rpartition("/")[2].partition(".")[0]
    sub_key = wbi_img["sub_url"].rpartition("/")[2].partition(".")[0]
    return FuncResult(
        type=FuncType.SUCCESS,
        result={
            "img_key": img_key,
            "sub_key": sub_key,
        },
    )


def get_danmaku_info(
    cookies: dict, room_id: int, img_key: str, sub_key: str
) -> FuncResult:
    """
    获取直播间弹幕信息api

    Args:
        cookies: cookies字典
        real_room_id: 真实房间号
    Raises:
        API_ARG_ERROR: 参数不正确
        API_DATA_ERROR: api结果不正确
        API_BILI_CODE_ERROR: B站请求错误
        API_STATUS_CODE_ERROR: 请求状态码错误
    Return:
        FuncResult: {
            danmaku_key: str
            danmaku_ws_url_list: list[str]
        }
    """
    param = {
        "id": room_id,
        "type": 0,
    }
    res = api(
        type=ApiType.GET,
        url=ApiUrl.GET_DANMAKU_INFO,
        cookies=cookies,
        params=encWbi(param, img_key, sub_key),
    )
    if not res.data:
        raise API_DATA_ERROR("获取直播间弹幕信息失败")

    danmaku_key = res.data["token"]
    host_list = res.data["host_list"]
    ws_url_list = []
    for host in host_list:
        if host.get("host") and host.get("wss_port"):
            ws_url_list.append(f"wss://{host['host']}:{host['wss_port']}/sub")
    return FuncResult(
        type=FuncType.SUCCESS,
        result={
            "danmaku_key": danmaku_key,
            "danmaku_ws_url_list": ws_url_list,
        },
    )


async def get_danmaku_websocket(danmaku_ws_url: str) -> FuncResult:
    """
    获取直播间弹幕websocket

    Args:
        danmaku_ws_url: 弹幕websocket地址
    Raises:
        InvalidURI: 无效WebSocket地址
        InvalidProxy: 无效Proxy
        OSError: 连接失败
        InvalidHandshake: 握手失败
        TimeoutError: 握手超时
    Return:
        FuncResult: danmaku_websocket
    """
    ws = await connect(
        uri=danmaku_ws_url,
        user_agent_header=";".join([f"{k}={v}" for k, v in ApiData.HEADERS.items()]),
    )
    return FuncResult(
        type=FuncType.SUCCESS,
        result=ws,
    )


async def ws_send_auth(
    ws: ClientConnection, user_id: int, room_id: int, danmaku_key: str
) -> FuncResult:
    """
    通过websocket发送认证

    Args:
        ws: websocket连接
        user_id: 用户id
        real_room_id: 真实房间号
        danmaku_key: 弹幕认证密钥
    Raises:
        ConnectionClosed: 连接关闭
        TypeError: 消息不支持
    Return:
        FuncResult:
            FAIL: ws.state
            SUCCESS: None
    """
    if ws.state != State.OPEN:
        return FuncResult(type=FuncType.FAIL, result=ws.state)
    auth_body = {
        "uid": user_id,
        "roomid": room_id,
        "protover": 3,
        "platform": "web",
        "type": 2,
        "key": danmaku_key,
    }
    data = pack_ws_body(
        auth_body,
        WebSocketProtoVer.DEFLATE,
        WebSocketOperation.AUTH,
    )
    await ws.send(data)
    try:
        await ws.recv()
    except ConnectionClosedError as e:
        return FuncResult(
            type=FuncType.ERROR,
            result={
                "reason": "认证时 WebSocket 连接关闭",
                "code": e.rcvd.code if e.rcvd else None,
                "ws_reason": e.rcvd.reason if e.rcvd else None,
            },
        )

    return FuncResult(type=FuncType.SUCCESS)


async def ws_send_heart(ws: ClientConnection) -> FuncResult:
    """
    通过websocket发送心跳

    Args:
        ws: websocket连接
    Raises:
        ConnectionClosed: 连接关闭
        TypeError: 消息不支持
    Return:
        FuncResult:
            FAIL: ws.state
            SUCCESS: None
    """
    if ws.state != State.OPEN:
        return FuncResult(type=FuncType.FAIL, result=ws.state)
    data = pack_ws_body(
        {},
        WebSocketProtoVer.DEFLATE,
        WebSocketOperation.HEARTBEAT,
    )
    await ws.send(data)
    return FuncResult(type=FuncType.SUCCESS)


async def ws_listen_danmaku(
    ws: ClientConnection,
) -> AsyncGenerator[FuncResult]:
    """
    通过websocket接收消息

    Args:
        ws: websocket连接
    Raises:
        ConnectionClosed: 连接关闭
        TypeError: 消息不支持
    Return:
        FuncResult:
            FAIL: ws.state
            SUCCESS: list[WebSocketMessage]
    """
    if ws.state != State.OPEN:
        yield FuncResult(
            type=FuncType.FAIL,
            result={"reason": "WebSocket 未连接", "state": ws.state.name},
        )
        return
    try:
        async for raw_message in ws:
            try:
                message_list: list[WebSocketMessage] = unpack_ws_message(raw_message)
                yield FuncResult(
                    type=FuncType.SUCCESS,
                    result=message_list,
                )
            except FUNC_DATA_ERROR:
                continue
    except ConnectionClosedError:
        yield FuncResult(
            type=FuncType.ERROR,
            result={"reason": "WebSocket 连接被服务端关闭"},
        )
        return

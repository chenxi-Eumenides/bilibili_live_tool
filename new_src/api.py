from dataclasses import dataclass
from enum import Enum, auto
from pprint import pformat
from time import time

import requests

from .constant import (
    BILI_URLS,
    HEADERS,
    PLATFORM,
    TICKET_KEY,
    TICKET_KEY_ID,
    USER_AGENT,
)
from .error import (
    API_ARG_ERROR,
    API_BILI_CODE_ERROR,
    API_DATA_ERROR,
    API_ERROR,
    API_STATUS_CODE_ERROR,
    API_TOO_MUCH_ERROR,
    Fail,
    Fail_Bili_Code,
    Fail_STATUS_Code,
)


class API_ASK_TYPE(Enum):
    POST = auto()
    GET = auto()


class API_STATUS(Enum):
    OK = auto()
    FAIL = auto()


@dataclass
class API_RES:
    """
    VALUE:
        STATUS: 请求状态
        CODE: B站请求状态
        MSG: 请求提示信息
        DATA: 请求返回数据
        COOKIE: 请求cookies
        REASON: 报错原因
        RAW_RESPONSE: 原始响应
    """

    STATUS: API_STATUS = API_STATUS.FAIL
    CODE: int = 0
    MSG: str = ""
    DATA: dict = None
    COOKIE: dict = None
    REASON: Fail = Fail.NotFail
    RAW_RESPONSE: dict = None

    def __str__(self):
        lines = [
            f"STATUS : {self.STATUS}",
            f"CODE : {self.CODE}",
            f"MSG : {self.MSG}",
            "DATA :",
            f"{pformat(self.DATA, indent=1)}",
            f"COOKIE : {self.COOKIE}",
            f"REASON : {self.REASON}",
        ]
        return "\n".join(lines)


def api(
    ask_type: API_ASK_TYPE,
    url: str,
    params=None,
    cookies=None,
    headers=None,
    data=None,
) -> API_RES:
    """
    请求api

    :param ask_type: 请求方式
    :param url: 请求url网络路径
    :param params: 请求参数, defaults to None
    :param cookies: Cookies, defaults to None
    :param headers: 请求头, defaults to None
    :param data: 请求数据, defaults to None
    :raises API_ARG_ERROR: 函数参数错误
    :raises API_TOO_MUCH_ERROR: 请求次数过多
    :raises API_ERROR: api错误
    :raises API_STATUS_CODE_ERROR: 请求状态码错误
    :return: api返回数据
    """
    try:
        if ask_type == API_ASK_TYPE.POST:
            res = requests.post(
                url=url, params=params, cookies=cookies, headers=headers, data=data
            )
        elif ask_type == API_ASK_TYPE.GET:
            res = requests.get(
                url=url, params=params, cookies=cookies, headers=headers, data=data
            )
        else:
            raise API_ARG_ERROR(f"api函数参数错误({ask_type=})")
    except ConnectionResetError as e:
        raise API_TOO_MUCH_ERROR(
            f"请求api({url})过多，请稍后再尝试\n报错原因：{str(e)}"
        )
    except Exception as e:
        raise API_ERROR(f"请求api({url})出错\n报错原因：{str(e)}")
    else:
        if res.status_code != 200:
            if reason := Fail_STATUS_Code.get(0 - res.status_code):
                pass
            else:
                reason = f"状态码为{res.status_code}"
            raise API_STATUS_CODE_ERROR(f"请求api({url})出错\n报错原因：{reason}")
    res_json: dict = res.json()
    status = API_STATUS.OK
    code = res_json.get("code", 0)
    msg = res_json.get("msg", "")
    data = res_json.get("data", [])
    cookie = res.cookies.get_dict()
    reason = Fail.NotFail
    if type(data) is list:
        data = {}
    if fail := Fail_Bili_Code.get(code):
        status = API_STATUS.FAIL
        reason = fail
    return API_RES(
        STATUS=status,
        CODE=code,
        MSG=msg,
        DATA=data,
        COOKIE=cookie,
        REASON=reason,
        RAW_RESPONSE=res,
    )


def api_start_live(
    cookies: dict = {}, csrf: str = "", room_id: int = 0, area_id: int = 0
) -> API_RES:
    from .lib import appsign

    data = appsign(
        {
            "room_id": room_id,
            "platform": PLATFORM,
            "area_v2": area_id,
            "csrf_token": csrf,
            "csrf": csrf,
            "type": 2,
        }
    )
    res = api(
        API_ASK_TYPE.POST,
        url=BILI_URLS["start_live"],
        headers=HEADERS,
        cookies=cookies,
        data=data,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(f"开播失败\n报错原因：{res.MSG} ({res.CODE})")
    return res


def api_stop_live(cookies: dict = {}, csrf: str = "", room_id: int = 0) -> API_RES:
    data = {
        "room_id": room_id,
        "platform": PLATFORM,
        "csrf_token": csrf,
        "csrf": csrf,
    }
    res: API_RES = api(
        API_ASK_TYPE.POST,
        url=BILI_URLS["stop_live"],
        headers=HEADERS,
        cookies=cookies,
        data=data,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(f"下播失败\n报错原因：{res.MSG} ({res.CODE})")
    return res


def api_room_update(
    cookies: dict = {},
    csrf: str = "",
    room_id: int = 0,
    area_id: int = 0,
    title: str = "",
) -> API_RES:
    if title and not area_id:
        data = {
            "room_id": room_id,
            "platform": PLATFORM,
            "title": title,
            "csrf_token": csrf,
            "csrf": csrf,
        }
    elif area_id and not title:
        data = {
            "room_id": room_id,
            "area_id": area_id,
            "activity_id": 0,
            "platform": PLATFORM,
            "csrf_token": csrf,
            "csrf": csrf,
        }
    else:
        raise API_ARG_ERROR(f"area_id和title同时只能传入一个。{area_id=} {title=}")
    res = api(
        API_ASK_TYPE.POST,
        url=BILI_URLS["room_update"],
        headers=HEADERS,
        cookies=cookies,
        data=data,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"更新直播间信息失败\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_update_area() -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["update_area"],
        headers=HEADERS,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取分区错误\n报错原因：{res.DATA} ({res.CODE})"
            )
    return res


def api_get_room_id(user_id: int = 0) -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["room_data"] + f"{user_id}",
        headers=HEADERS,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取房间号错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_user_status(cookies: dict = {}) -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["user_status"],
        headers=HEADERS,
        cookies=cookies,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取用户状态错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_get_room_data(cookies: dict = {}, room_id: int = 0) -> API_RES:
    data = {
        "room_id": room_id,
    }
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["room_data"],
        headers=HEADERS,
        cookies=cookies,
        data=data,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取直播间数据错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_qr_login() -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["qr_login"],
        headers=HEADERS,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取登陆二维码错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_qr_face(cookies: dict = {}, csrf: str = "", room_id: int = 0) -> API_RES:
    data = {
        "room_id": room_id,
        "face_auth_code": "60024",
        "csrf_token": csrf,
        "csrf": csrf,
        "visit_id": "",
    }
    res: API_RES = api(
        API_ASK_TYPE.POST,
        url=BILI_URLS["qr_face"],
        headers=HEADERS,
        cookies=cookies,
        data=data,
    )
    if res.STATUS == API_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = API_STATUS.FAIL
            res.REASON = Fail.NeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取登陆二维码错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_get_bili_ticket() -> API_RES:
    from .lib import hmac_sha256

    url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
    ts = int(time())
    params = {
        "key_id": TICKET_KEY_ID,
        "hexsign": hmac_sha256(TICKET_KEY, f"ts{ts}"),
        "context[ts]": f"{ts}",
        "csrf": "",
    }
    header = {"user-agent": USER_AGENT}
    res: API_RES = api(url, params=params, headers=header)
    if res.STATUS == API_STATUS.OK:
        if res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取bili_ticket错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_get_wbi_keys() -> API_RES:
    "获取最新的 img_key 和 sub_key"
    url = "https://api.bilibili.com/x/web-interface/nav"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Referer": "https://www.bilibili.com/",
    }
    res = api(API_ASK_TYPE.GET, url=url, headers=headers)
    if res.STATUS == API_STATUS.OK and (wbi := res.DATA.get("wbi_img")):
        img_url: str = wbi.get("img_url")
        sub_url: str = wbi.get("sub_url")
        if img_url and sub_url:
            res.DATA = {
                "img_key": img_url.rsplit("/", 1)[1].split(".")[0],
                "sub_key": sub_url.rsplit("/", 1)[1].split(".")[0],
            }
            return res
    raise API_DATA_ERROR(f"wbi请求无效，数据不完整\n报错原因：{res.DATA}")

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pprint import pformat
from time import mktime, time

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
from .lib import RES, RES_STATUS, get_pinyin


class API_ASK_TYPE(Enum):
    POST = auto()
    GET = auto()


@dataclass
class API_RES(RES):
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

    CODE: int = 0
    MSG: str = ""
    COOKIE: dict = None
    RAW_RESPONSE: dict = None

    def __str__(self):
        lines = [
            f"STATUS : {self.STATUS.name}",
            f"CODE : {self.CODE}",
            f"MSG : {self.MSG}",
            "DATA :",
            f"{pformat(self.DATA, indent=1)}",
            f"COOKIE : {self.COOKIE}",
            f"REASON : {self.REASON.name}",
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
    :param params: 请求参数
    :param cookies: Cookies
    :param headers: 请求头
    :param data: 请求数据
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
    status = RES_STATUS.OK
    code = res_json.get("code", 0)
    msg = res_json.get("msg", "")
    data = res_json.get("data", [])
    cookie = res.cookies.get_dict()
    reason = Fail.NotFail
    if fail := Fail_Bili_Code.get(code):
        status = RES_STATUS.FAIL
        reason = fail
    elif code in Fail_STATUS_Code:
        status = RES_STATUS.FAIL
        reason = Fail_STATUS_Code[code]
    if not cookie:
        cookie = None
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
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
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
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(f"下播失败\n报错原因：{res.MSG} ({res.CODE})")
    return res


def api_update_room(
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
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"更新直播间信息失败\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_get_area() -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["update_area"],
        headers=HEADERS,
    )
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取分区错误\n报错原因：{res.DATA} ({res.CODE})"
            )
        if len(res.DATA) > 0:
            data = {"root": {}, "area": {}}
            for main_area in res.DATA:
                data["root"].update(
                    {
                        str(main_area.get("id")): {
                            "id": main_area.get("id"),
                            "name": main_area.get("name"),
                            "pinyin": get_pinyin(main_area.get("name")),
                            "py": get_pinyin(main_area.get("name"), first=True),
                            "child_id": [],
                            "child_name": [],
                            "child_pinyin": [],
                            "child_py": [],
                        },
                    }
                )
                for area in main_area.get("list"):
                    id = area.get("id")
                    name = area.get("name")
                    pinyin = get_pinyin(name)
                    py = get_pinyin(name, first=True)
                    parent_id = area.get("parent_id")
                    new_area = {
                        "id": id,
                        "name": name,
                        "pinyin": pinyin,
                        "py": py,
                        "parent_id": parent_id,
                        "parent_name": area.get("parent_name"),
                    }
                    data["area"].update({str(id): new_area})
                    data["root"][str(parent_id)]["child_id"].append(id)
                    data["root"][str(parent_id)]["child_name"].append(name)
                    data["root"][str(parent_id)]["child_pinyin"].append(pinyin)
                    data["root"][str(parent_id)]["child_py"].append(py)
            res.DATA = data
    return res


def api_get_room_id(user_id: int = 0) -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["room_data"] + f"{user_id}",
        headers=HEADERS,
    )
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取房间号错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_get_user_status(cookies: dict = {}) -> API_RES:
    res: API_RES = api(
        API_ASK_TYPE.GET,
        url=BILI_URLS["user_status"],
        headers=HEADERS,
        cookies=cookies,
    )
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
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
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
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
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
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
    if res.STATUS == RES_STATUS.OK:
        if "qr" in res.DATA:
            res.STATUS = RES_STATUS.FAIL
            res.REASON = Fail.ApiNeedFaceAuth
        elif res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取登陆二维码错误\n报错原因：{res.MSG} ({res.CODE})"
            )
    return res


def api_get_ticket_and_wbi() -> API_RES:
    """
    获取ticket和wbi_key

    :raises API_BILI_CODE_ERROR: 请求错误
    :return: API_RES
    """
    from .lib import hmac_sha256

    ts = int(time())
    params = {
        "key_id": TICKET_KEY_ID,
        "hexsign": hmac_sha256(TICKET_KEY, f"ts{ts}"),
        "context[ts]": f"{ts}",
        "csrf": "",
    }
    header = {"user-agent": USER_AGENT}
    res: API_RES = api(
        API_ASK_TYPE.POST, url=BILI_URLS["bili_ticket"], params=params, headers=header
    )
    if res.STATUS == RES_STATUS.OK:
        if res.CODE != 0:
            raise API_BILI_CODE_ERROR(
                f"获取ticket及wbi_key错误\n报错原因：{res.MSG} ({res.CODE})"
            )
        else:
            img: str = res.DATA["nav"]["img"]
            sub: str = res.DATA["nav"]["sub"]
            res.DATA = {
                "wbi": {
                    "img_key": img.rsplit("/", 1)[1].split(".")[0],
                    "sub_key": sub.rsplit("/", 1)[1].split(".")[0],
                    "end_time": datetime.fromtimestamp(
                        mktime(datetime.now().date().timetuple()) + 86400
                    ),
                },
                "ticket": {
                    "ticket": res.DATA["ticket"],
                    "end_time": res.DATA["created_at"] + res.DATA["ttl"],
                },
            }
    return res

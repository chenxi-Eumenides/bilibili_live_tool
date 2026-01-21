from dataclasses import dataclass
from pprint import pformat
from enum import auto, StrEnum

import requests

from .lib import RES, RES_STATUS, sign_data, update_data, CONFIG
from .error import FAIL, FAIL_STATUS_CODE, FAIL_BILI_CODE
from .constant import BILI_URLS, HEADERS, DATA


class API_TYPE(StrEnum):
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

    CODE: int = -1
    COOKIE: dict = None
    RAW_RESPONSE: dict = None

    def __str__(self):
        lines = [
            f"STATUS : {self.STATUS.name}",
            f"CODE : {self.CODE}",
            f"MSG : {self.MSG}",
            f"DATA :",
            f"{pformat(self.DATA, indent=2)}",
            f"COOKIE : {self.COOKIE}",
            f"REASON : {self.FAIL_REASON.name}",
        ]
        return "\n".join(lines)


def api(
    type: API_TYPE,
    url: str,
    params: dict = None,
    cookies: dict = None,
    headers: dict = HEADERS,
    data: dict = None,
) -> API_RES:
    """
    请求api

    :param type: 请求方式
    :param url: 请求url路径
    :param params: 请求参数
    :param cookies: Cookies
    :param headers: 请求头
    :param data: 请求数据
    :raises API_ARG_ERROR: 函数参数错误
    :raises API_TOO_MUCH_ERROR: 请求次数过多
    :raises API_ERROR: api错误
    :raises API_STATUS_CODE_ERROR: 请求状态码错误
    :return: API_RES: api返回数据
    """
    if url in BILI_URLS.keys():
        url = BILI_URLS.get(url)
    elif url in BILI_URLS.values():
        pass
    else:
        return API_RES(
            STATUS=RES_STATUS.FAIL,
            FAIL_REASON=FAIL.ARG_ERROR,
            MSG=f"url({url})不在已定义的URL路径中，请检查是否正确",
        )
    try:
        if type == API_TYPE.POST:
            res = requests.post(
                url=url, params=params, cookies=cookies, headers=headers, data=data
            )
        elif type == API_TYPE.GET:
            res = requests.get(
                url=url, params=params, cookies=cookies, headers=headers, data=data
            )
    except Exception as e:
        return API_RES(
            STATUS=RES_STATUS.FAIL,
            FAIL_REASON=FAIL.API_ERROR,
            MSG=f"请求api({url})出错，报错原因：{str(e)}",
            RAW_RESPONSE=res,
        )
    cookie = res.cookies.get_dict()
    if res.status_code != 200:
        return API_RES(
            STATUS=RES_STATUS.FAIL,
            CODE=res.status_code,
            MSG=(
                FAIL_STATUS_CODE.get(0 - res.status_code)
                if (0 - res.status_code) in FAIL_STATUS_CODE.keys()
                else f"api请求状态码为{res.status_code}"
            ),
            FAIL_REASON=FAIL.API_ERROR,
            COOKIE=cookie,
        )
    res_json: dict = res.json()
    if (
        res_json.get("code") in FAIL_BILI_CODE.keys()
        or res_json.get("code") in FAIL_STATUS_CODE.keys()
    ):
        return API_RES(
            STATUS=RES_STATUS.FAIL,
            CODE=res_json.get("code", 0),
            MSG=(
                res_json.get("msg", "")
                if res_json.get("msg")
                else (
                    FAIL_STATUS_CODE.get(res_json.get("code"))
                    if res_json.get("code") in FAIL_STATUS_CODE.keys()
                    else f"B站api请求状态码为({res_json.get("code")})"
                )
            ),
            FAIL_REASON=FAIL.API_ERROR,
            COOKIE=cookie,
            RAW_RESPONSE=res,
        )
    else:
        return API_RES(
            STATUS=RES_STATUS.OK,
            CODE=res_json.get("code", 0),
            MSG=res_json.get("msg", ""),
            DATA=res_json.get("data", []),
            FAIL_REASON=FAIL.NOT_FAIL,
            COOKIE=cookie,
            RAW_RESPONSE=res,
        )


def api_start_live(config: CONFIG) -> API_RES:
    url_name = "start_live"
    data_name = "start_live"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        data=sign_data(update_data(DATA.get(data_name), config.__dict__)),
    )
    return res


def api_stop_live(config: CONFIG) -> API_RES:
    url_name = "stop_live"
    data_name = "stop_live"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        data=update_data(DATA.get(data_name), config.__dict__),
    )
    return res


def api_update_title(config: CONFIG) -> API_RES:
    url_name = "update_room_info"
    data_name = "update_title"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        data=update_data(DATA.get(data_name), config.__dict__),
    )
    return res


def api_update_area(config: CONFIG) -> API_RES:
    url_name = "update_room_info"
    data_name = "update_area"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        data=update_data(DATA.get(data_name), config.__dict__),
    )
    return res


def api_get_room_data(config: CONFIG) -> API_RES:
    url_name = "get_room_data"
    data_name = "get_room_data"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        data=update_data(DATA.get(data_name), config.__dict__),
    )
    return res


def api_get_area_list(config: CONFIG) -> API_RES:
    url_name = "get_area_list"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
    )
    return res


def api_get_bili_live_info(config: CONFIG) -> API_RES:
    url_name = "get_room_id"
    data_name = "get_room_id"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        params=update_data(DATA.get(data_name), config.__dict__),
    )
    return res


def api_get_bili_live_info(config: CONFIG) -> API_RES:
    url_name = "get_bili_live_info"
    data_name = "get_bili_live_info"
    res = api(
        API_TYPE.POST,
        url=BILI_URLS[url_name],
        cookies=config.cookies,
        params=update_data(DATA.get(data_name), config.__dict__),
    )
    return res

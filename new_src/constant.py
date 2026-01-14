# 常量

# tuple[int, int, int, str, int]
# 0.0.1 (0, 0, 1)
# V0.0.1-alpha-1 (0, 0, 1, "alpha", 1)
VERSION: tuple[int, int, int, str, int] = (0, 3, 8)

README_FILE: str = "使用说明.txt"
CONFIG_FILE: str = "config.json"
QR_IMG: str = "qr.jpg"
QR_FACE_IMG: str = "qr_face.jpg"

TITLE_MAX_CHAR: int = 40
AREA_OUTPUT_LINE_NUM: int = 4

APP_KEY: str = "aae92bc66f3edfab"
APP_SECRET: str = "af125a0d5279fd576c1b4418a3e8276d"

LIVEHIME_BUILD: str = "10082"
LIVEHIME_VERSION: str = "7.40.0.10082"

TICKET_KEY_ID: str = "ec02"
TICKET_KEY: str = "XgwSnGZ1p"

PLATFORM: str = "pc_link"
BILI_URLS: dict[str, str] = {
    "start_live": "https://api.live.bilibili.com/room/v1/Room/startLive",
    "stop_live": "https://api.live.bilibili.com/room/v1/Room/stopLive",
    "update_room_info": "https://api.live.bilibili.com/room/v1/Room/update",
    "get_area_list": "https://api.live.bilibili.com/room/v1/Area/getList",
    "get_room_id": "https://api.live.bilibili.com/room/v2/Room/room_id_by_uid",
    "get_user_status": "https://api.bilibili.com/x/web-interface/nav/stat",
    "get_room_data": "https://api.live.bilibili.com/room/v1/Room/get_info",
    "get_qr_res": "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
    "get_qr_login": "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
    "check_qr_face": "https://api.live.bilibili.com/xlive/app-blink/v1/preLive/IsUserIdentifiedByFaceAuth",
    "get_bili_ticket": "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket",
    "get_wbi_keys": "https://api.bilibili.com/x/web-interface/nav",
    "get_bili_live_info": "https://api.live.bilibili.com/xlive/app-blink/v1/liveVersionInfo/getHomePageLiveVersion",
    "set_live_timeshift": "https://api.live.bilibili.com/xlive/app-blink/v1/upStreamConfig/SetAnchorSelfStreamTimeShift",
}

EMPTY_DATA_LOGIN: dict = {
    "user_id": 0,
    "cookies_str": "",
    "csrf": "",
    "refresh_token": "",
}
EMPTY_DATA_LIVE: dict = {
    "room_id": 0,
    "title": "",
    "area_id": 0,
    "rtmp_addr": "",
    "rtmp_code": "",
}

DATA: dict[str, dict] = {
    "start_live": {
        "room_id": None,
        "platform": None,
        "area_v2": None,
        "csrf_token": None,
        "csrf": None,
        "type": 2,
        "build": None,
        "version": None,
    },
    "stop_live": {
        "room_id": None,
        "platform": None,
        "csrf_token": None,
        "csrf": None,
    },
    "update_title": {
        "room_id": None,
        "platform": None,
        "title": None,
        "csrf_token": None,
        "csrf": None,
    },
    "update_area": {
        "room_id": None,
        "area_id": None,
        "activity_id": 0,
        "platform": None,
        "csrf_token": None,
        "csrf": None,
    },
    "check_qr_face": {
        "room_id": None,
        "face_auth_code": "60024",
        "csrf_token": None,
        "csrf": None,
        "visit_id": "",
    },
    "get_room_data": {
        "room_id": None,
    },
    "get_room_id": {
        "uid": None,
    },
    "get_bili_live_info": {
        "system_version": 2,
    },
}

USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
)
HEADERS: dict = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://link.bilibili.com",
    "referer": "https://link.bilibili.com/p/center/index",
    "sec-ch-ua": '"Microsoft Edge";v="137", "Not=A?Brand";v="8", "Chromium";v="137"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": USER_AGENT,
}

MIXIN_KEY_ENC_TAB: list[int] = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]

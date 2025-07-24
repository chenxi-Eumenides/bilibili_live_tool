# 常量

# tuple[int, int, int, str, int]
# 0.0.1 (0, 0, 1)
# V0.0.1-alpha-1 (0, 0, 1, "alpha", 1)
VERSION = (0, 3, 8)

README_FILE = "使用说明.txt"
CONFIG_FILE = "config.json"
QR_IMG = "qr.jpg"
QR_FACE_IMG = "qr_face.jpg"

APP_KEY: str = "aae92bc66f3edfab"
APP_SECRET: str = "af125a0d5279fd576c1b4418a3e8276d"
LIVEHIME_BUILD: str = "9343"
LIVEHIME_VERSION: str = "7.17.0.9343"
TICKET_KEY_ID: str = "ec02"
TICKET_KEY: str = "XgwSnGZ1p"

TITLE_MAX_CHAR: int = 40
AREA_OUTPUT_LINE_NUM: int = 4
PLATFORM: str = "pc_link"
BILI_URLS = {
    "start_live": "https://api.live.bilibili.com/room/v1/Room/startLive",
    "stop_live": "https://api.live.bilibili.com/room/v1/Room/stopLive",
    "room_update": "https://api.live.bilibili.com/room/v1/Room/update",
    "update_area": "https://api.live.bilibili.com/room/v1/Area/getList",
    "room_id": "https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid=",
    "user_status": "https://api.bilibili.com/x/web-interface/nav/stat",
    "room_data": "https://api.live.bilibili.com/room/v1/Room/get_info",
    "qr_login": "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
    "qr_face": "https://api.live.bilibili.com/xlive/app-blink/v1/preLive/IsUserIdentifiedByFaceAuth",
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

USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
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

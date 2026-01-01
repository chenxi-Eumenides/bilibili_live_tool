# 常量

# tuple[int, int, int, str, int]
# 0.0.1 (0, 0, 1)
# V0.0.1-alpha-1 (0, 0, 1, "alpha", 1)
VERSION = (0, 3, 11)

# 文件名
README_FILE = "使用说明.txt"
CONFIG_FILE = "config.json"
QR_IMG = "qr.jpg"
QR_FACE_IMG = "qr_face.jpg"

# B站api必须值
APP_KEY: str = "aae92bc66f3edfab"
APP_SECRET: str = "af125a0d5279fd576c1b4418a3e8276d"
LIVEHIME_BUILD: str = "10082"
LIVEHIME_VERSION: str = "7.40.0.10082"

# 配置
TITLE_MAX_CHAR: int = 40
AREA_OUTPUT_LINE_NUM: int = 4

# URL
URL_GET_ROOM_ID: str = "https://api.live.bilibili.com/room/v2/Room/room_id_by_uid"
URL_GET_QR_RES: str = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
URL_GENERATE_QR: str = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
URL_GET_AREA_LIST: str = "https://api.live.bilibili.com/room/v1/Area/getList"
URL_GET_ROOM_STATUS: str = "https://api.live.bilibili.com/room/v1/Room/get_info"
URL_UPDATE_ROOM: str = "https://api.live.bilibili.com/room/v1/Room/update"
URL_GET_USER_STATUS: str = "https://api.bilibili.com/x/web-interface/nav/stat"
URL_CHECK_FACE: str = "https://api.live.bilibili.com/xlive/app-blink/v1/preLive/IsUserIdentifiedByFaceAuth"
URL_START_LIVE: str = "https://api.live.bilibili.com/room/v1/Room/startLive"
URL_STOP_LIVE: str = "https://api.live.bilibili.com/room/v1/Room/stopLive"
URL_GET_LIVE_VERSION: str = "https://api.live.bilibili.com/xlive/app-blink/v1/liveVersionInfo/getHomePageLiveVersion"
URL_SET_LIVE_TIMESHIFT: str = "https://api.live.bilibili.com/xlive/app-blink/v1/upStreamConfig/SetAnchorSelfStreamTimeShift"
from enum import auto, StrEnum


class FAIL(StrEnum):
    NOT_FAIL = auto()
    # 函数调用相关
    ARG_ERROR = auto()
    # api相关
    API_ERROR = auto()
    INVALID_COOKIES = auto()
    NO_RESULT = auto()
    # 配置相关
    EMPTY_CONFIG = auto()
    # 文件相关
    FILE_NOT_FOUND = auto()
    READ_FILE_FAIL = auto()
    WRITE_FILE_FAIL = auto()
    NOT_PERMISSION = auto()


class BASE_ERROR(Exception):
    pass


class BASE_API_ERROR(BASE_ERROR):
    pass


class API_ERROR(BASE_API_ERROR):
    pass


class API_ARG_ERROR(BASE_API_ERROR):
    pass


class API_STATUS_CODE_ERROR(BASE_API_ERROR):
    pass


class API_BILI_CODE_ERROR(BASE_API_ERROR):
    pass


class API_DATA_ERROR(BASE_API_ERROR):
    pass


FAIL_BILI_CODE: dict[int, str] = {
    60009: "分区已下线",
    60013: "所在地区受实名认证限制无法开播",
    60024: "目标分区需要人脸认证",
    60034: "系统维护仅支持直播姬开/关播",
    60037: "web在线开播已下线",
    65530: "token错误（登录错误）",
}

FAIL_STATUS_CODE: dict[int, str] = {
    -1: "应用程序不存在或已被封禁",
    -2: "Access Key 错误",
    -3: "API 校验密匙错误",
    -4: "调用方对该 Method 没有权限",
    -101: "账号未登录",
    -102: "账号被封停",
    -103: "积分不足",
    -104: "硬币不足",
    -105: "验证码错误",
    -106: "账号非正式会员或在适应期",
    -107: "应用不存在或者被封禁",
    -108: "未绑定手机",
    -110: "未绑定手机",
    -111: "csrf 校验失败",
    -112: "系统升级中",
    -113: "账号尚未实名认证",
    -114: "请先绑定手机",
    -115: "请先完成实名认证",
    -304: "木有改动",
    -307: "撞车跳转",
    -352: "风控校验失败 (UA 或 wbi 参数不合法)",
    -400: "请求错误",
    -401: "未认证 (或非法请求)",
    -403: "访问权限不足",
    -404: "啥都木有",
    -405: "不支持该方法",
    -409: "冲突",
    -412: "请求被拦截 (客户端 ip 被服务端风控)",
    -500: "服务器错误",
    -503: "过载保护,服务暂不可用",
    -504: "服务调用超时",
    -509: "超出限制",
    -616: "上传文件不存在",
    -617: "上传文件太大",
    -625: "登录失败次数太多",
    -626: "用户不存在",
    -628: "密码太弱",
    -629: "用户名或密码错误",
    -632: "操作对象数量限制",
    -643: "被锁定",
    -650: "用户等级太低",
    -652: "重复的用户",
    -658: "Token 过期",
    -662: "密码时间戳过期",
    -688: "地理区域限制",
    -689: "版权限制",
    -701: "扣节操失败",
    -799: "请求过于频繁，请稍后再试",
    -8888: "对不起，服务器开小差了~ (ಥ﹏ಥ)",
}

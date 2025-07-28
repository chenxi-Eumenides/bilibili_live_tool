from enum import IntEnum, auto


class Fail(IntEnum):
    NotFail = 0
    ApiNeedIDAuth = auto()
    ApiNeedFaceAuth = auto()
    ApiAreaNotFound = auto()
    ApiOnlyBiliLive = auto()
    ApiCannotLiveFromWeb = auto()
    ArgError = auto()
    FileNotFound = auto()
    ReadFileFail = auto()
    WriteFileFail = auto()
    EmptyConfig = auto()
    InvalidCookies = auto()
    NoPermission = auto()
    NoResult = auto()


Fail_Bili_Code: dict[int, Fail] = {
    60009: Fail.ApiAreaNotFound,
    60013: Fail.ApiNeedIDAuth,
    60024: Fail.ApiNeedFaceAuth,
    60034: Fail.ApiOnlyBiliLive,
    60037: Fail.ApiCannotLiveFromWeb,
}


class Base_Error(Exception):
    pass


class BASE_API_ERROR(Base_Error):
    pass


class API_ERROR(BASE_API_ERROR):
    pass


class API_ARG_ERROR(BASE_API_ERROR):
    pass


class API_TOO_MUCH_ERROR(BASE_API_ERROR):
    pass


class API_STATUS_CODE_ERROR(BASE_API_ERROR):
    pass


class API_BILI_CODE_ERROR(BASE_API_ERROR):
    pass


class API_DATA_ERROR(BASE_API_ERROR):
    pass


Fail_STATUS_Code: dict[int, str] = {
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

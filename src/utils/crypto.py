"""加密/签名工具模块

处理API请求签名等加密相关功能。
"""

from urllib.parse import urlencode
from hashlib import md5
from time import time

from .constants import APP_KEY, APP_SECRET


def sign_api_data(data: dict) -> dict:
    """对请求数据进行B站API签名
    
    参考B站APP端签名算法，用于直播相关API调用。
    
    Args:
        data: 原始请求数据字典
        
    Returns:
        dict: 添加了ts、appkey、sign字段的数据字典
        
    Example:
        >>> data = {"room_id": 12345, "platform": "pc_link"}
        >>> signed = sign_api_data(data)
        >>> print(signed)
        {'room_id': 12345, 'platform': 'pc_link', 'ts': '1234567890', 
         'appkey': 'aae92bc66f3edfab', 'sign': 'xxxxxxxx'}
    """
    # 添加必要字段
    data = data.copy()  # 避免修改原始数据
    data.update({
        "ts": str(int(time())),
        "appkey": APP_KEY,
    })

    # 按key排序并编码
    sorted_data = dict(sorted(data.items()))
    query = urlencode(sorted_data, encoding="utf-8")

    # 添加签名（拼接appsecret后md5）
    sign_str = query + APP_SECRET
    sign = md5(sign_str.encode(encoding="utf-8")).hexdigest()

    sorted_data["sign"] = sign
    return sorted_data
"""WBI签名模块

处理B站WBI签名算法，用于API请求鉴权。
"""

import asyncio
import hashlib
import logging
import urllib.parse
import weakref
from datetime import datetime, timedelta
from typing import Optional

import aiohttp


logger = logging.getLogger(__name__)


__all__ = (
    'WbiSigner',
    'get_wbi_signer',
)


# 默认User-Agent（与客户端共享）
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'

# API地址
WBI_INIT_URL = 'https://api.bilibili.com/x/web-interface/nav'


_session_to_wbi_signer: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def get_wbi_signer(session: aiohttp.ClientSession) -> 'WbiSigner':
    """获取WBI签名器（每个session一个）"""
    wbi_signer = _session_to_wbi_signer.get(session, None)
    if wbi_signer is None:
        wbi_signer = _session_to_wbi_signer[session] = WbiSigner(session)
    return wbi_signer


class WbiSigner:
    """WBI签名器"""
    
    WBI_KEY_INDEX_TABLE = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
        27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13
    ]
    """WBI密钥索引表"""
    
    WBI_KEY_TTL = timedelta(hours=11, minutes=59, seconds=30)
    """WBI密钥有效期"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._wbi_key = ''
        self._refresh_future: Optional[asyncio.Future] = None
        self._last_refresh_time: Optional[datetime] = None
    
    @property
    def wbi_key(self) -> str:
        """缓存的WBI鉴权口令"""
        return self._wbi_key
    
    def reset(self):
        """重置密钥"""
        self._wbi_key = ''
        self._last_refresh_time = None
    
    @property
    def need_refresh_wbi_key(self) -> bool:
        """是否需要刷新WBI密钥"""
        if self._wbi_key == '':
            return True
        if self._last_refresh_time is None:
            return True
        return datetime.now() - self._last_refresh_time >= self.WBI_KEY_TTL
    
    def refresh_wbi_key(self) -> asyncio.Future:
        """刷新WBI密钥（避免并发刷新）"""
        if self._refresh_future is None:
            self._refresh_future = asyncio.create_task(self._do_refresh_wbi_key())
            
            def on_done(_fu):
                self._refresh_future = None
            self._refresh_future.add_done_callback(on_done)
        return self._refresh_future
    
    async def _do_refresh_wbi_key(self):
        """执行刷新"""
        wbi_key = await self._get_wbi_key()
        if wbi_key:
            self._wbi_key = wbi_key
            self._last_refresh_time = datetime.now()
    
    async def _get_wbi_key(self) -> str:
        """从API获取WBI密钥"""
        try:
            async with self._session.get(
                WBI_INIT_URL,
                headers={'User-Agent': USER_AGENT},
            ) as res:
                if res.status != 200:
                    logger.warning('WbiSigner failed to get wbi key: status=%d %s', res.status, res.reason)
                    return ''
                data = await res.json()
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('WbiSigner failed to get wbi key:')
            return ''
        
        try:
            wbi_img = data['data']['wbi_img']
            img_key = wbi_img['img_url'].rpartition('/')[2].partition('.')[0]
            sub_key = wbi_img['sub_url'].rpartition('/')[2].partition('.')[0]
        except (KeyError, TypeError):
            logger.warning('WbiSigner failed to get wbi key: data=%s', data)
            return ''
        
        # 混淆密钥
        shuffled_key = img_key + sub_key
        wbi_key = []
        for index in self.WBI_KEY_INDEX_TABLE:
            if index < len(shuffled_key):
                wbi_key.append(shuffled_key[index])
        return ''.join(wbi_key)
    
    def add_wbi_sign(self, params: dict) -> dict:
        """给参数添加WBI签名"""
        if self._wbi_key == '':
            return params
        
        wts = str(int(datetime.now().timestamp()))
        params_to_sign = {**params, 'wts': wts}
        
        # 按key字典序排序
        params_to_sign = {key: params_to_sign[key] for key in sorted(params_to_sign.keys())}
        
        # 过滤特殊字符
        for key, value in params_to_sign.items():
            value = ''.join(ch for ch in str(value) if ch not in "!'()*")
            params_to_sign[key] = value
        
        # 计算签名
        str_to_sign = urllib.parse.urlencode(params_to_sign) + self._wbi_key
        w_rid = hashlib.md5(str_to_sign.encode('utf-8')).hexdigest()
        
        return {
            **params,
            'wts': wts,
            'w_rid': w_rid
        }
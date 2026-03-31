"""弹幕客户端模块

参考blivedm的实现重新设计，采用分层架构：
- DanmuClient: Web端弹幕客户端
- 支持自动重连、故障转移
- 支持消息处理器
"""

import asyncio
import json
import logging
import weakref
from datetime import datetime, timedelta
from typing import Callable, Optional, Union

import aiohttp
import brotli
import yarl
import zlib

from . import danmaku_handler, danmaku_models
from .danmaku_protocol import (
    HeaderTuple,
    HEADER_STRUCT,
    ProtoVer,
    Operation,
    AuthReplyCode,
    InitError,
    AuthError,
    make_packet,
)
from .danmaku_wbi import USER_AGENT, get_wbi_signer


logger = logging.getLogger(__name__)

__all__ = (
    'DanmakuClient',
    'DanmakuMessage',
)

# 导出数据模型
DanmakuMessage = danmaku_models.DanmakuMessage

# API地址
UID_INIT_URL = 'https://api.bilibili.com/x/web-interface/nav'
BUVID_INIT_URL = 'https://www.bilibili.com/'
ROOM_INIT_URL = 'https://api.live.bilibili.com/room/v1/Room/get_info'
DANMAKU_SERVER_CONF_URL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo'

# 默认弹幕服务器列表
DEFAULT_DANMAKU_SERVER_LIST = [
    {'host': 'broadcastlv.chat.bilibili.com', 'port': 2243, 'wss_port': 443, 'ws_port': 2244}
]

# 默认重连策略：固定1秒间隔
def _constant_retry_policy(interval: float):
    def get_interval(_retry_count: int, _total_retry_count: int):
        return interval
    return get_interval

DEFAULT_RECONNECT_POLICY = _constant_retry_policy(1)


# ===== DanmuClient =====

class DanmakuClient:
    """Web端弹幕客户端
    
    :param room_id: URL中的房间ID，可以用短ID
    :param uid: B站用户ID，0表示未登录，None表示自动获取
    :param session: cookie、连接池
    :param heartbeat_interval: 发送心跳包的间隔时间（秒）
    """
    
    def __init__(
        self,
        room_id: int,
        *,
        uid: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
        heartbeat_interval: float = 30,
    ):
        # session管理
        if session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            self._own_session = True
        else:
            self._session = session
            self._own_session = False
            assert self._session.loop is asyncio.get_event_loop()
        
        self._wbi_signer = get_wbi_signer(self._session)
        self._heartbeat_interval = heartbeat_interval
        
        # 房间相关
        self._tmp_room_id = room_id
        """临时房间ID（用于初始化）"""
        self._uid = uid
        """用户ID"""
        
        # 初始化后设置的字段
        self._room_id: Optional[int] = None
        """真实房间ID"""
        self._room_owner_uid: Optional[int] = None
        """主播用户ID"""
        self._host_server_list: Optional[list] = None
        """弹幕服务器列表"""
        self._host_server_token: Optional[str] = None
        """连接弹幕服务器用的token"""
        
        # 运行时字段
        self._websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        """WebSocket连接"""
        self._network_future: Optional[asyncio.Future] = None
        """网络协程的future"""
        self._heartbeat_timer_handle: Optional[asyncio.TimerHandle] = None
        """心跳定时器handle"""
        self._need_init_room = True
        """是否需要初始化房间"""
        
        # 处理器
        self._handler: Optional[danmaku_handler.HandlerInterface] = None
        """消息处理器"""
        self._get_reconnect_interval: Callable[[int, int], float] = DEFAULT_RECONNECT_POLICY
        """重连间隔策略"""
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._network_future is not None
    
    @property
    def room_id(self) -> Optional[int]:
        """房间ID（初始化后可用）"""
        return self._room_id
    
    @property
    def tmp_room_id(self) -> int:
        """构造时传入的room_id参数"""
        return self._tmp_room_id
    
    @property
    def uid(self) -> Optional[int]:
        """当前登录的用户ID"""
        return self._uid
    
    def set_handler(self, handler: Optional[danmaku_handler.HandlerInterface]):
        """设置消息处理器"""
        self._handler = handler
    
    def set_reconnect_policy(self, get_reconnect_interval: Callable[[int, int], float]):
        """设置重连策略
        
        :param get_reconnect_interval: 输入(retry_count, total_retry_count)，返回间隔时间
        """
        self._get_reconnect_interval = get_reconnect_interval
    
    def start(self):
        """启动客户端"""
        if self.is_running:
            logger.warning('room=%s client is running, cannot start() again', self.room_id)
            return
        
        self._network_future = asyncio.create_task(self._network_coroutine_wrapper())
        logger.info('room=%d client started', self._tmp_room_id)
    
    def stop(self):
        """停止客户端"""
        if not self.is_running:
            logger.warning('room=%s client is stopped, cannot stop() again', self.room_id)
            return
        
        self._network_future.cancel()
        logger.info('room=%d client stopping...', self._tmp_room_id)
    
    async def stop_and_close(self):
        """停止并释放资源"""
        if self.is_running:
            self.stop()
            await self.join()
        await self.close()
    
    async def join(self):
        """等待客户端停止"""
        if not self.is_running:
            logger.warning('room=%s client is stopped, cannot join()', self.room_id)
            return
        
        await asyncio.shield(self._network_future)
    
    async def close(self):
        """释放资源，调用后客户端将不可用"""
        if self.is_running:
            logger.warning('room=%s is calling close(), but client is running', self.room_id)
        
        if self._own_session:
            await self._session.close()
    
    # ===== 网络协程 =====
    
    async def _network_coroutine_wrapper(self):
        """网络协程包装器（处理异常）"""
        exc = None
        try:
            await self._network_coroutine()
        except asyncio.CancelledError:
            # 正常停止
            pass
        except Exception as e:
            logger.exception('room=%s _network_coroutine() finished with exception:', self.room_id)
            exc = e
        finally:
            logger.debug('room=%s _network_coroutine() finished', self.room_id)
            self._network_future = None
        
        if self._handler is not None:
            self._handler.on_client_stopped(self, exc)
    
    async def _network_coroutine(self):
        """网络协程（核心逻辑）"""
        retry_count = 0
        total_retry_count = 0
        
        while True:
            try:
                # 连接前初始化
                await self._on_before_ws_connect(retry_count)
                
                # 建立WebSocket连接
                ws_url = self._get_ws_url(retry_count)
                logger.debug('room=%d connecting to %s', self.room_id, ws_url)
                
                async with self._session.ws_connect(
                    ws_url,
                    headers={'User-Agent': USER_AGENT},
                    receive_timeout=self._heartbeat_interval + 5,
                ) as websocket:
                    self._websocket = websocket
                    logger.info('room=%d WebSocket connected', self.room_id)
                    await self._on_ws_connect()
                    
                    # 消息接收循环
                    async for message in websocket:
                        await self._on_ws_message(message)
                        # 成功处理消息后重置重试计数
                        retry_count = 0
                        
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
                # 连接错误，准备重连
                logger.debug('room=%d connection error, will retry', self.room_id)
            except AuthError:
                # 认证失败，需要重新初始化房间
                logger.exception('room=%d auth failed, trying init_room() again', self.room_id)
                self._need_init_room = True
            finally:
                self._websocket = None
                await self._on_ws_close()
            
            # 准备重连
            retry_count += 1
            total_retry_count += 1
            interval = self._get_reconnect_interval(retry_count, total_retry_count)
            logger.warning(
                'room=%d is reconnecting, retry_count=%d, total_retry_count=%d, interval=%.1fs',
                self.room_id, retry_count, total_retry_count, interval
            )
            await asyncio.sleep(interval)
    
    # ===== WebSocket事件处理 =====
    
    async def _on_before_ws_connect(self, retry_count: int):
        """连接前调用，用于初始化房间"""
        if not self._need_init_room:
            return
        
        # 重连次数太多时重新init_room
        reinit_period = max(3, len(self._host_server_list or []))
        if retry_count > 0 and retry_count % reinit_period == 0:
            logger.debug('room=%d reinitializing room after %d retries', self.room_id, retry_count)
        
        if not await self.init_room():
            raise InitError('init_room() failed')
        self._need_init_room = False
    
    async def _on_ws_connect(self):
        """WebSocket连接成功"""
        await self._send_auth()
        # 启动心跳定时器
        self._heartbeat_timer_handle = asyncio.get_running_loop().call_later(
            self._heartbeat_interval, self._on_send_heartbeat
        )
    
    async def _on_ws_close(self):
        """WebSocket连接断开"""
        if self._heartbeat_timer_handle is not None:
            self._heartbeat_timer_handle.cancel()
            self._heartbeat_timer_handle = None
    
    async def _on_ws_message(self, message: aiohttp.WSMessage):
        """收到WebSocket消息"""
        if message.type != aiohttp.WSMsgType.BINARY:
            logger.warning('room=%d unknown websocket message type=%s', self.room_id, message.type)
            return
        
        try:
            await self._parse_ws_message(message.data)
        except AuthError:
            raise
        except Exception:
            logger.exception('room=%d _parse_ws_message() error:', self.room_id)
    
    def _on_send_heartbeat(self):
        """心跳定时器回调"""
        if self._websocket is None or self._websocket.closed:
            self._heartbeat_timer_handle = None
            return
        
        # 重新调度
        self._heartbeat_timer_handle = asyncio.get_running_loop().call_later(
            self._heartbeat_interval, self._on_send_heartbeat
        )
        # 发送心跳
        asyncio.create_task(self._send_heartbeat())
    
    async def _send_heartbeat(self):
        """发送心跳包"""
        if self._websocket is None or self._websocket.closed:
            return
        
        try:
            await self._websocket.send_bytes(make_packet({}, Operation.HEARTBEAT))
        except (ConnectionResetError, aiohttp.ClientConnectionError) as e:
            logger.warning('room=%d _send_heartbeat() failed: %r', self.room_id, e)
        except Exception:
            logger.exception('room=%d _send_heartbeat() failed:', self.room_id)
    
    # ===== 消息解析 =====
    
    async def _parse_ws_message(self, data: bytes):
        """解析WebSocket消息"""
        offset = 0
        
        try:
            header = HeaderTuple(*HEADER_STRUCT.unpack_from(data, offset))
        except struct.error:
            logger.exception('room=%d parsing header failed, data=%s', self.room_id, data[:50])
            return
        
        if header.operation in (Operation.SEND_MSG_REPLY, Operation.AUTH_REPLY):
            # 业务消息或认证回复，可能有多个包
            while True:
                body = data[offset + header.raw_header_size: offset + header.pack_len]
                await self._parse_business_message(header, body)
                
                offset += header.pack_len
                if offset >= len(data):
                    break
                
                try:
                    header = HeaderTuple(*HEADER_STRUCT.unpack_from(data, offset))
                except struct.error:
                    logger.exception('room=%d parsing header failed, offset=%d', self.room_id, offset)
                    break
        
        elif header.operation == Operation.HEARTBEAT_REPLY:
            # 心跳回复，前4字节是人气值
            body = data[offset + header.raw_header_size: offset + header.raw_header_size + 4]
            popularity = int.from_bytes(body, 'big') if len(body) >= 4 else 0
            # 转换为业务消息处理
            command = {
                'cmd': '_HEARTBEAT',
                'data': {'popularity': popularity}
            }
            self._handle_command(command)
        
        else:
            # 未知消息
            logger.warning('room=%d unknown message operation=%d', self.room_id, header.operation)
    
    async def _parse_business_message(self, header: HeaderTuple, body: bytes):
        """解析业务消息"""
        if header.operation == Operation.SEND_MSG_REPLY:
            # 业务消息
            if header.ver == ProtoVer.BROTLI:
                # Brotli压缩，在后台线程解压
                body = await asyncio.get_running_loop().run_in_executor(None, brotli.decompress, body)
                await self._parse_ws_message(body)
            elif header.ver == ProtoVer.DEFLATE:
                # Zlib压缩
                body = await asyncio.get_running_loop().run_in_executor(None, zlib.decompress, body)
                await self._parse_ws_message(body)
            elif header.ver == ProtoVer.NORMAL:
                # 未压缩
                if len(body) != 0:
                    try:
                        command = json.loads(body.decode('utf-8'))
                        self._handle_command(command)
                    except Exception:
                        logger.error('room=%d, body=%s', self.room_id, body[:200])
                        raise
            else:
                logger.warning('room=%d unknown protocol version=%d', self.room_id, header.ver)
        
        elif header.operation == Operation.AUTH_REPLY:
            # 认证回复
            command = json.loads(body.decode('utf-8'))
            if command['code'] != AuthReplyCode.OK:
                raise AuthError(f"auth reply error, code={command['code']}, body={command}")
            # 认证成功后立即发送心跳
            await self._websocket.send_bytes(make_packet({}, Operation.HEARTBEAT))
        
        else:
            logger.warning('room=%d unknown message operation=%d', self.room_id, header.operation)
    
    def _handle_command(self, command: dict):
        """处理业务命令"""
        if self._handler is None:
            return
        try:
            self._handler.handle(self, command)
        except Exception as e:
            logger.exception('room=%d _handle_command() failed, command=%s', self.room_id, command, exc_info=e)
    
    # ===== 初始化方法 =====
    
    async def init_room(self) -> bool:
        """初始化连接房间需要的字段
        
        :return: True代表没有降级
        """
        result = True
        
        # 初始化UID
        if self._uid is None:
            if not await self._init_uid():
                logger.warning('room=%d _init_uid() failed', self._tmp_room_id)
                self._uid = 0
        
        # 初始化buvid
        if self._get_buvid() == '':
            if not await self._init_buvid():
                logger.warning('room=%d _init_buvid() failed', self._tmp_room_id)
        
        # 初始化房间ID和主播ID
        if not await self._init_room_id_and_owner():
            result = False
            # 降级处理
            self._room_id = self._tmp_room_id
            self._room_owner_uid = 0
        
        # 初始化弹幕服务器
        if not await self._init_host_server():
            result = False
            # 降级处理
            self._host_server_list = DEFAULT_DANMAKU_SERVER_LIST
            self._host_server_token = None
        
        return result
    
    async def _init_uid(self) -> bool:
        """初始化用户ID"""
        cookies = self._session.cookie_jar.filter_cookies(yarl.URL(UID_INIT_URL))
        sessdata_cookie = cookies.get('SESSDATA', None)
        if sessdata_cookie is None or sessdata_cookie.value == '':
            # 没有cookie，直接设置为未登录
            self._uid = 0
            return True
        
        try:
            async with self._session.get(
                UID_INIT_URL,
                headers={'User-Agent': USER_AGENT},
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_uid() failed, status=%d', self._tmp_room_id, res.status)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    if data['code'] == -101:
                        # 未登录
                        self._uid = 0
                        return True
                    logger.warning('room=%d _init_uid() failed, message=%s', self._tmp_room_id, data['message'])
                    return False
                
                data = data['data']
                if not data.get('isLogin', False):
                    self._uid = 0
                else:
                    self._uid = data['mid']
                return True
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_uid() failed:', self._tmp_room_id)
            return False
    
    def _get_buvid(self) -> str:
        """获取buvid"""
        cookies = self._session.cookie_jar.filter_cookies(yarl.URL(BUVID_INIT_URL))
        buvid_cookie = cookies.get('buvid3', None)
        return buvid_cookie.value if buvid_cookie else ''
    
    async def _init_buvid(self) -> bool:
        """初始化buvid（访问首页获取）"""
        try:
            async with self._session.get(
                BUVID_INIT_URL,
                headers={'User-Agent': USER_AGENT},
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_buvid() status error, status=%d', self._tmp_room_id, res.status)
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_buvid() exception:', self._tmp_room_id)
        return self._get_buvid() != ''
    
    async def _init_room_id_and_owner(self) -> bool:
        """初始化房间ID和主播ID"""
        try:
            async with self._session.get(
                ROOM_INIT_URL,
                headers={'User-Agent': USER_AGENT},
                params={'room_id': self._tmp_room_id},
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_room_id_and_owner() failed, status=%d', 
                                   self._tmp_room_id, res.status)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('room=%d _init_room_id_and_owner() failed, message=%s',
                                   self._tmp_room_id, data['message'])
                    return False
                return self._parse_room_init(data['data'])
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_room_id_and_owner() failed:', self._tmp_room_id)
            return False
    
    def _parse_room_init(self, data: dict) -> bool:
        """解析房间初始化数据"""
        self._room_id = data['room_id']
        self._room_owner_uid = data['uid']
        logger.debug('room=%d owner_uid=%d', self._room_id, self._room_owner_uid)
        return True
    
    async def _init_host_server(self) -> bool:
        """初始化弹幕服务器配置"""
        if self._wbi_signer.need_refresh_wbi_key:
            await self._wbi_signer.refresh_wbi_key()
            if self._wbi_signer.wbi_key == '':
                logger.warning('room=%d _init_host_server() failed: no wbi key', self._room_id)
                return False
        
        try:
            async with self._session.get(
                DANMAKU_SERVER_CONF_URL,
                headers={'User-Agent': USER_AGENT},
                params=self._wbi_signer.add_wbi_sign({'id': self._room_id, 'type': 0}),
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_host_server() failed, status=%d',
                                   self._room_id, res.status)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    if data['code'] == -352:
                        # WBI签名错误，重置key
                        self._wbi_signer.reset()
                    logger.warning('room=%d _init_host_server() failed, message=%s',
                                   self._room_id, data['message'])
                    return False
                return self._parse_danmaku_server_conf(data['data'])
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_host_server() failed:', self._room_id)
            return False
    
    def _parse_danmaku_server_conf(self, data: dict) -> bool:
        """解析弹幕服务器配置"""
        self._host_server_list = data['host_list']
        self._host_server_token = data['token']
        if not self._host_server_list:
            logger.warning('room=%d _parse_danmaku_server_conf() failed: host_list is empty', self._room_id)
            return False
        logger.debug('room=%d got %d host servers', self._room_id, len(self._host_server_list))
        return True
    
    def _get_ws_url(self, retry_count: int) -> str:
        """获取WebSocket URL（支持故障转移）"""
        host_server = self._host_server_list[retry_count % len(self._host_server_list)]
        return f"wss://{host_server['host']}:{host_server['wss_port']}/sub"
    
    async def _send_auth(self):
        """发送认证包"""
        auth_params = {
            'uid': self._uid or 0,
            'roomid': self._room_id,
            'protover': 3,
            'platform': 'web',
            'type': 2,
            'buvid': self._get_buvid(),
        }
        if self._host_server_token is not None:
            auth_params['key'] = self._host_server_token
        
        logger.debug('room=%d sending auth, uid=%s', self.room_id, self._uid)
        await self._websocket.send_bytes(make_packet(auth_params, Operation.AUTH))
import json
import sys
from pathlib import Path
from pprint import pp
from random import randint
from time import sleep
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase, main
from unittest.mock import mock_open, patch

import qrcode
from websockets import ClientConnection, State

sys.path.insert(0, str(Path.cwd()))
from src.utils.api import (
    api,
    api_check_face_auth,
    api_check_login,
    api_get_area_list,
    api_get_login_qr,
    api_get_room_data,
    api_get_room_id,
    api_get_user_nav,
    api_start_live,
    api_stop_live,
    api_update_room,
    get_danmaku_info,
    get_danmaku_websocket,
    get_wbi_key,
    ws_listen_danmaku,
    ws_send_auth,
    ws_send_heart,
)
from src.utils.data import (
    ApiType,
    FuncType,
    LiveArea,
    LiveAreaList,
    LiveSubArea,
    WebSocketMessage,
)
from src.utils.error import API_BILI_CODE_ERROR, API_DATA_ERROR


class Test_Api(IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.config = SimpleNamespace()
        self.read_config(Path("unittest/config.json"))
        self.cookies = json.loads(self.config.cookies_str)
        self.user_id = self.cookies.get("DedeUserID", self.config.uid)

    def read_config(self, path: Path):
        """读取配置文件，用于独立测试各函数"""
        if not path.exists():
            raise Exception(
                "没有配置文件，请将 有配置信息的config.json 放在 unittest 文件夹下"
            )
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") == 2:
            user = data.get("user")
            live = data.get("live")
            vars(self.config).update(user)
            vars(self.config).update(live)
        else:
            vars(self.config).update(data)

    def test_api_get_user_nav(self):
        result = api_get_user_nav(self.cookies)
        self.assertEqual(result.type, FuncType.SUCCESS)
        data = result.result
        self.assertIsInstance(data.get("following"), int)
        self.assertIsInstance(data.get("follower"), int)
        self.assertIsInstance(data.get("dynamic_count"), int)
        result = api_get_user_nav({})
        self.assertEqual(result.type, FuncType.FAIL)

    def test_api_get_room_id(self):
        # 存在的uid
        result = api_get_room_id(cookies=self.cookies, user_id=730732)
        self.assertEqual(result.type, FuncType.SUCCESS)
        room_id = result.result
        self.assertEqual(room_id, 42062)
        # 不存在的uid
        with self.assertRaises(API_BILI_CODE_ERROR) as error:
            api_get_room_id(cookies=self.cookies, user_id=1243)
        self.assertEqual(error.exception.code, 404)

    def test_api_get_login_qr(self):
        result = api_get_login_qr()
        self.assertEqual(result.type, FuncType.SUCCESS)
        qr_url, qr_key = result.result.values()
        self.assertIsInstance(qr_url, str)
        self.assertIsInstance(qr_key, str)
        self.assertRegex(
            qr_url,
            "https://account.bilibili.com/h5/account-h5/auth/scan-web?",
        )
        self.assertRegex(
            qr_url,
            f"qrcode_key={qr_key}",
        )

    def test_api_get_room_data(self):
        result = api_get_room_data(self.cookies, 42062)
        self.assertEqual(result.type, FuncType.SUCCESS)
        room_data: dict = result.result
        self.assertEqual(len(room_data), 16)

    def test_api_get_area_list(self):
        result = api_get_area_list(self.cookies)
        self.assertEqual(result.type, FuncType.SUCCESS)
        area_list: LiveAreaList = result.result
        self.assertIsInstance(area_list, LiveAreaList)
        main_area = area_list[0]
        self.assertIsInstance(main_area, LiveArea)
        sub_area = main_area.list[0]
        self.assertIsInstance(sub_area, LiveSubArea)

    def test_api_check_login(self):
        qr_key = api_get_login_qr().result["qr_key"]
        with self.assertRaises(API_BILI_CODE_ERROR) as e:
            result = api_check_login(qr_key)
        self.assertEqual(e.exception.code, 86101)
        with self.assertRaises(API_BILI_CODE_ERROR) as e:
            result = api_check_login("invalid_qr_key")
        self.assertEqual(e.exception.code, 86038)

    def test_api_check_face_auth(self):
        with self.assertRaises(API_DATA_ERROR):
            result = api_check_face_auth(self.cookies, 1243)

    def test_api_get_user_nav_no_cookies(self):
        with self.assertRaises(API_BILI_CODE_ERROR) as e:
            api_get_user_nav({})
        self.assertEqual(e.exception.code, 101)

    def test_api_get_wbi_key(self):
        # 需要登录
        result = get_wbi_key(self.cookies)
        self.assertEqual(result.type, FuncType.SUCCESS)
        img_key, sub_key = result.result.values()
        self.assertEqual(len(img_key), 32)
        self.assertEqual(len(sub_key), 32)
        # 非法cookies/无效cookies
        with self.assertRaises(API_BILI_CODE_ERROR) as e:
            result = get_wbi_key({})
        self.assertEqual(e.exception.code, 101)

    def test_get_danmaku_info(self):
        img_key, sub_key = get_wbi_key(self.cookies).result.values()
        result = get_danmaku_info(self.cookies, 42062, img_key, sub_key)
        self.assertEqual(result.type, FuncType.SUCCESS)

    def test_api_start_live(self):
        result = api_start_live(self.cookies, self.config.room_id, self.config.area_id)
        if result.type == FuncType.SUCCESS:
            self.assertEqual(result.result["face_auth"], False)
            self.assertTrue(hasattr(result.result, "rtmp_addr"))
            self.assertTrue(hasattr(result.result, "rtmp_code"))
            self.assertTrue(hasattr(result.result, "live_build"))
            self.assertTrue(hasattr(result.result, "live_version"))
        elif result.type == FuncType.FAIL:
            self.assertEqual(result.result["face_auth"], True)
            self.assertIsInstance(result.result.get("qr_url"), str)

    def test_api_stop_live(self):
        result = api_stop_live(self.cookies, self.config.room_id)
        self.assertEqual(result.type, FuncType.SUCCESS)

    def test_api_update_room(self):
        # 更新标题和分区
        result = api_update_room(
            cookies=self.cookies,
            room_id=self.config.room_id,
            title=self.config.title,
            area_id=self.config.area_id,
        )
        self.assertEqual(result.type, FuncType.SUCCESS)

    async def test_danmaku_websocket(self):
        test_room_id = 92613
        test_room_id = api_get_room_data(self.cookies, test_room_id).result.get(
            "room_id"
        )
        img_key, sub_key = get_wbi_key(self.cookies).result.values()
        key, ws_url_list = get_danmaku_info(
            self.cookies, test_room_id, img_key, sub_key
        ).result.values()
        # self.assertIsInstance(key, str)
        # self.assertIsInstance(ws_uri, str)

        result = await get_danmaku_websocket(ws_url_list[0])
        # self.assertEqual(result.type, FuncType.SUCCESS)
        ws: ClientConnection = result.result
        # self.assertIsInstance(ws, ClientConnection)

        result = await ws_send_auth(ws, self.user_id, test_room_id, key)
        # self.assertEqual(result.type, FuncType.SUCCESS)

        async for result in ws_listen_danmaku(ws):
            # self.assertEqual(result.type, FuncType.SUCCESS)
            message_list: list[WebSocketMessage] = result.result
            # self.assertIsInstance(message_list, list)

            for message in message_list:
                # self.assertIsInstance(message, WebSocketMessage)
                pp(message)

    def test_login(self):
        qr_url, qr_key = api_get_login_qr().result.values()
        self.print_qr_url(qr_url)
        cookies_dict = None
        while True:
            try:
                result = api_check_login(qr_key)
            except Exception as e:
                print(e)
                break
            if result.type == FuncType.FAIL:
                sleep(0.5)
                continue
            data = result.result
            cookies = data["cookies"]
            refresh_token = data["refresh_token"]
            cookies_dict = cookies.get_dict()
            break
        pp(cookies_dict)
        pass

    def print_qr_url(self, qr_url: str) -> None:
        CHARS = {
            (False, False): " ",
            (True, False): "▀",
            (False, True): "▄",
            (True, True): "█",
        }
        qr_data = []
        qr = qrcode.QRCode(
            version=6,
            error_correction=1,
            box_size=1,
            border=0,
        )
        qr.add_data(qr_url)
        qr.make(fit=False)
        matrix = qr.get_matrix()
        size = len(matrix)
        for row in range(0, size, 2):
            qr_line = ""
            for line in range(size):
                qr_line += CHARS[
                    (
                        matrix[row][line],
                        matrix[row + 1][line] if row + 1 < size else False,
                    )
                ]
            qr_data.append(qr_line)
        qr_text = "\n".join(qr_data)
        pp(qr_text)


if __name__ == "__main__":
    main(
        argv=[
            "",
            # "Test_Api.test_test",
            # "Test_Api.test_api_get_room_id",
            # "Test_Api.test_api_get_login_qr",
            # "Test_Api.test_api_get_room_data",
            # "Test_Api.test_api_get_area_list",
            # "Test_Api.test_api_check_login",
            # "Test_Api.test_api_check_face_auth",
            # "Test_Api.test_get_wbi_key",
            # "Test_Api.test_get_danmaku_info",
            # "Test_Api.test_danmaku_websocket",
            # "Test_Api.test_login",
            "Test_Api.test_api_get_user_nav",
        ]
    )

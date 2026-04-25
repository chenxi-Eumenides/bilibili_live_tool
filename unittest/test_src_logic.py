"""Logic 层单元测试 —— session / auth / live / danmaku"""

import sys
from asyncio import Event
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase, main
from unittest.mock import MagicMock, patch

from requests import HTTPError, Response

sys.path.insert(0, str(Path.cwd()))

from src.logic.auth import (
    auth_generate_qrcode,
    auth_poll_login,
    auth_validate_login,
    auth_logout,
)
from src.logic.danmaku import danmaku_start, danmaku_stop
from src.logic.live import (
    live_get_area_list,
    live_get_room_info,
    live_refresh_room_info,
    live_start,
    live_stop,
    live_update_title,
)
from src.logic.session import Session
from src.utils.config import CONFIG
from src.utils.constant import BiliCode, SessionEvent
from src.utils.data import AppState, FuncResult, FuncType
from src.utils.error import API_BILI_CODE_ERROR


class TestSession(TestCase):

    def setUp(self):
        self.session = Session()

    def test_init_defaults(self):
        self.assertFalse(self.session.is_logged_in)
        self.assertFalse(self.session.is_live)
        self.assertEqual(self.session.app_state, AppState.UNAUTH)
        self.assertEqual(self.session.room_id, 0)
        self.assertEqual(self.session.user_id, 0)
        self.assertEqual(self.session.cookies, {})
        self.assertEqual(self.session.csrf, "")

    def test_init_custom_config(self):
        cfg = CONFIG(uid=12345, room_id=99999)
        s = Session(cfg)
        self.assertEqual(s.user_id, 12345)
        self.assertEqual(s.room_id, 99999)

    def test_on_register_and_emit(self):
        calls = []
        self.session.on("test_event", lambda *a: calls.append(a))
        self.session._emit("test_event", "arg1", 2)
        self.assertEqual(calls, [("arg1", 2)])

    def test_on_multiple_listeners(self):
        results = []
        self.session.on("e", lambda: results.append(1))
        self.session.on("e", lambda: results.append(2))
        self.session._emit("e")
        self.assertEqual(results, [1, 2])

    def test_on_rejects_non_callable(self):
        with self.assertRaises(TypeError):
            self.session.on("e", "not_callable")

    def test_off_removes_listener(self):
        results = []
        cb = lambda: results.append(1)
        self.session.on("e", cb)
        self.session.off("e", cb)
        self.session._emit("e")
        self.assertEqual(results, [])

    def test_off_safe_when_not_registered(self):
        self.session.off("nonexistent", lambda: None)

    def test_once_triggers_only_once(self):
        results = []
        cb = lambda x: results.append(x)
        self.session.once("e", cb)
        self.session._emit("e", 1)
        self.session._emit("e", 2)
        self.assertEqual(results, [1])

    def test_emit_catches_callback_exceptions(self):
        def faulty():
            raise ValueError("boom")

        def normal():
            pass

        self.session.on("e", faulty)
        self.session.on("e", normal)
        self.session._emit("e")

    def test_is_logged_in_depends_on_verified(self):
        self.assertFalse(self.session.is_logged_in)
        self.session.config.cookies = {"token": "x"}
        self.assertFalse(self.session.is_logged_in)
        self.session._login_verified = True
        self.assertTrue(self.session.is_logged_in)

    def test_is_live_depends_on_app_state(self):
        self.assertFalse(self.session.is_live)
        self.session.app_state = AppState.LIVE
        self.assertTrue(self.session.is_live)
        self.session.app_state = AppState.IDLE
        self.assertFalse(self.session.is_live)

    def test_config_getter_setter(self):
        new_cfg = CONFIG(uid=42)
        self.session.config = new_cfg
        self.assertEqual(self.session.user_id, 42)

    def test_properties_reflect_config(self):
        self.session.config.cookies = {"bili_jct": "csrf_token"}
        self.session.config.csrf = "explicit_csrf"
        self.session.config.uid = 777
        self.session.config.room_id = 888
        self.assertEqual(self.session.csrf, "explicit_csrf")
        self.assertEqual(self.session.user_id, 777)
        self.assertEqual(self.session.room_id, 888)


class TestAuth(TestCase):

    def setUp(self):
        self.session = Session()

    @patch("src.logic.auth.api_get_login_qr")
    def test_auth_generate_qrcode_success(self, mock_qr):
        mock_qr.return_value = FuncResult(
            type=FuncType.SUCCESS,
            result={"qr_url": "https://bili.com/qr", "qr_key": "abc123"},
        )
        emit_calls = []
        self.session.on(SessionEvent.AUTH_QRCODE_READY, lambda *a: emit_calls.append(a))

        result = auth_generate_qrcode(self.session)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(result.result["qr_key"], "abc123")
        self.assertEqual(len(emit_calls), 1)

    @patch("src.logic.auth.api_get_login_qr")
    def test_auth_generate_qrcode_failure(self, mock_qr):
        mock_qr.return_value = FuncResult(type=FuncType.FAIL, result="bili error")
        result = auth_generate_qrcode(self.session)
        self.assertEqual(result.type, FuncType.FAIL)

    @patch("src.logic.auth.api_check_login")
    def test_auth_poll_login_success(self, mock_check):
        mock_check.return_value = FuncResult(
            type=FuncType.SUCCESS,
            result={
                "cookies": {"DedeUserID": "123", "bili_jct": "csrf_abc"},
                "refresh_token": "refresh_xyz",
            },
        )
        emit_calls = []
        self.session.on(SessionEvent.AUTH_LOGIN_SUCCESS, lambda: emit_calls.append(1))

        result = auth_poll_login(self.session, "qr_key", timeout_sec=5)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertTrue(self.session.is_logged_in)
        self.assertEqual(self.session.csrf, "csrf_abc")
        self.assertEqual(self.session.config.refresh_token, "refresh_xyz")
        self.assertEqual(len(emit_calls), 1)

    @patch("src.logic.auth.api_check_login")
    def test_auth_poll_login_scanned_then_success(self, mock_check):
        mock_check.side_effect = [
            FuncResult(type=FuncType.FAIL, result=BiliCode.LOGIN_QR_SCANNED),
            FuncResult(
                type=FuncType.SUCCESS,
                result={"cookies": {"bili_jct": "ok"}, "refresh_token": ""},
            ),
        ]
        emit_calls = []
        self.session.on(SessionEvent.AUTH_LOGIN_POLLING, lambda *a: emit_calls.append("polling"))
        self.session.on(SessionEvent.AUTH_LOGIN_SUCCESS, lambda: emit_calls.append("success"))

        result = auth_poll_login(self.session, "qr_key", timeout_sec=5)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertIn("polling", emit_calls)
        self.assertIn("success", emit_calls)

    @patch("src.logic.auth.api_check_login")
    def test_auth_poll_login_expired(self, mock_check):
        mock_check.return_value = FuncResult(type=FuncType.FAIL, result=BiliCode.LOGIN_QR_EXPIRED)

        emit_calls = []
        self.session.on(SessionEvent.AUTH_LOGIN_FAILED, lambda *a: emit_calls.append(a))

        result = auth_poll_login(self.session, "qr_key", timeout_sec=5)

        self.assertEqual(result.type, FuncType.FAIL)
        self.assertFalse(self.session.is_logged_in)
        self.assertEqual(len(emit_calls), 1)

    @patch("src.logic.auth.api_check_login")
    def test_auth_poll_login_timeout(self, mock_check):
        mock_check.return_value = FuncResult(type=FuncType.FAIL, result=BiliCode.LOGIN_QR_WAITING)

        result = auth_poll_login(self.session, "qr_key", timeout_sec=1)
        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("超时", result.result)

    @patch("src.logic.auth.api")
    def test_auth_validate_login_success(self, mock_api):
        mock_res = MagicMock()
        mock_res.cookies = {"some": "cookie"}
        mock_res.data = {"uname": "test_user"}
        mock_api.return_value = mock_res

        self.session.config.cookies = {"token": "x"}
        result = auth_validate_login(self.session)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertTrue(self.session.is_logged_in)

    @patch("src.logic.auth.api")
    def test_auth_validate_login_no_cookies(self, mock_api):
        result = auth_validate_login(self.session)
        self.assertEqual(result.type, FuncType.FAIL)
        self.assertFalse(self.session.is_logged_in)

    @patch("src.logic.auth.api")
    def test_auth_validate_login_api_error(self, mock_api):
        mock_api.side_effect = API_BILI_CODE_ERROR(
            -101, "未登录",
            HTTPError(response=MagicMock(spec=Response))
        )

        self.session.config.cookies = {"token": "expired"}
        result = auth_validate_login(self.session)

        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("过期", result.result)
        self.assertFalse(self.session.is_logged_in)

    def test_auth_logout(self):
        self.session.config.cookies = {"token": "x"}
        self.session.config.csrf = "csrf_val"
        self.session.config.uid = 123
        self.session._login_verified = True

        emit_calls = []
        self.session.on(SessionEvent.AUTH_LOGOUT_DONE, lambda: emit_calls.append(1))

        result = auth_logout(self.session)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(self.session.config.cookies, {})
        self.assertEqual(self.session.config.csrf, "")
        self.assertEqual(self.session.config.uid, 0)
        self.assertFalse(self.session.is_logged_in)
        self.assertEqual(len(emit_calls), 1)


class TestLive(TestCase):

    def setUp(self):
        self.session = Session()
        self.session._login_verified = True
        self.session.config.room_id = 12345

    def _assert_not_logged_in(self, func, *args):
        self.session._login_verified = False
        result = func(self.session, *args)
        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("未登录", str(result.result))

    @patch("src.logic.live.api_start_live")
    def test_live_start_success(self, mock_start):
        mock_start.return_value = FuncResult(
            type=FuncType.SUCCESS,
            result={"rtmp_addr": "rtmp://x", "rtmp_code": "code123"},
        )
        emit_calls = []
        self.session.on(SessionEvent.LIVE_STATE_CHANGED, lambda *a: emit_calls.append(a))

        result = live_start(self.session, area_id=100)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(self.session.app_state, AppState.LIVE)
        self.assertEqual(self.session.config.rtmp_addr, "rtmp://x")
        self.assertEqual(self.session.config.rtmp_code, "code123")
        self.assertEqual(len(emit_calls), 1)

    def test_live_start_requires_login(self):
        self._assert_not_logged_in(live_start, 100)

    @patch("src.logic.live.api_start_live")
    def test_live_start_api_failure(self, mock_start):
        mock_start.return_value = FuncResult(type=FuncType.FAIL, result="need face auth")
        result = live_start(self.session, area_id=100)
        self.assertEqual(result.type, FuncType.FAIL)
        self.assertNotEqual(self.session.app_state, AppState.LIVE)

    @patch("src.logic.live.api_stop_live")
    def test_live_stop_success(self, mock_stop):
        self.session.app_state = AppState.LIVE
        mock_stop.return_value = FuncResult(type=FuncType.SUCCESS, result={})

        emit_calls = []
        self.session.on(SessionEvent.LIVE_STATE_CHANGED, lambda *a: emit_calls.append(a))

        result = live_stop(self.session)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(self.session.app_state, AppState.IDLE)
        self.assertEqual(len(emit_calls), 1)

    def test_live_stop_requires_login(self):
        self._assert_not_logged_in(live_stop)

    @patch("src.logic.live.api_update_room")
    def test_live_update_title_success(self, mock_update):
        mock_update.return_value = FuncResult(type=FuncType.SUCCESS, result={})

        emit_calls = []
        self.session.on(SessionEvent.LIVE_INFO_UPDATED, lambda *a: emit_calls.append(a))

        result = live_update_title(self.session, "新标题")

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(self.session.config.title, "新标题")
        self.assertEqual(len(emit_calls), 1)

    def test_live_update_title_requires_login(self):
        self._assert_not_logged_in(live_update_title, "tit")

    @patch("src.logic.live.api_get_room_data")
    def test_live_refresh_room_info_success(self, mock_room):
        mock_room.return_value = FuncResult(
            type=FuncType.SUCCESS,
            result={"room_id": 12345, "title": "test"},
        )

        emit_calls = []
        self.session.on(SessionEvent.LIVE_INFO_UPDATED, lambda *a: emit_calls.append(a))

        result = live_refresh_room_info(self.session)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(self.session.config.room_data, {"room_id": 12345, "title": "test"})
        self.assertEqual(len(emit_calls), 1)

    def test_live_refresh_room_info_requires_login(self):
        self._assert_not_logged_in(live_refresh_room_info)

    def test_live_get_room_info_with_cache(self):
        self.session.config.room_data = {"room_id": 999}
        result = live_get_room_info(self.session)
        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertEqual(result.result["room_id"], 999)

    def test_live_get_room_info_without_cache(self):
        result = live_get_room_info(self.session)
        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("尚无房间数据", str(result.result))

    @patch("src.logic.live.api_get_area_list")
    def test_live_get_area_list_success(self, mock_area):
        mock_area.return_value = FuncResult(type=FuncType.SUCCESS, result=["area1"])
        result = live_get_area_list(self.session)
        self.assertEqual(result.type, FuncType.SUCCESS)

    def test_live_get_area_list_requires_login(self):
        self._assert_not_logged_in(live_get_area_list)


class TestDanmaku(TestCase):

    def setUp(self):
        self.session = Session()
        self.session._login_verified = True
        self.session.config.room_id = 12345

    def test_danmaku_start_success(self):
        result = danmaku_start(self.session)

        self.assertEqual(result.type, FuncType.SUCCESS)
        self.assertTrue(self.session._danmaku_running)
        self.assertIsInstance(self.session._danmaku_stop_event, Event)

    def test_danmaku_start_duplicate(self):
        danmaku_start(self.session)
        result = danmaku_start(self.session)

        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("已在运行", str(result.result))

    def test_danmaku_start_requires_login(self):
        self.session._login_verified = False
        result = danmaku_start(self.session)

        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("未登录", str(result.result))

    def test_danmaku_start_requires_room(self):
        self.session.config.room_id = 0
        result = danmaku_start(self.session)

        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("房间号", str(result.result))

    def test_danmaku_stop_sets_event(self):
        danmaku_start(self.session)
        self.assertFalse(self.session._danmaku_stop_event.is_set())

        danmaku_stop(self.session)
        self.assertTrue(self.session._danmaku_stop_event.is_set())

    def test_danmaku_stop_not_running(self):
        result = danmaku_stop(self.session)

        self.assertEqual(result.type, FuncType.FAIL)
        self.assertIn("未在运行", str(result.result))


if __name__ == "__main__":
    main(argv=[""])

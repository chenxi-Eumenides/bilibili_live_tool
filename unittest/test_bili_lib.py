import io
import os
import sys
from platform import system as get_platform
from unittest import TestCase, main
from unittest.mock import mock_open, patch

sys.path.append(os.getcwd())
from src.bili_lib import Config, Data, get, get_json, open_file, post, post_json

lib_str = "src.bili_lib."


class Test(TestCase):
    def setUp(self):
        super().setUp()
        # init
        self.config = Config()
        self.data = Data()
        self.config.config_file = "unittest/test.json"
        self.config.read_config(self.data)

    def test_read_config(self):
        self.assertEqual(self.data.user_id, 1111, msg="用户名为 1111")
        self.assertEqual(self.data.room_id, 2222, msg="房间号为 2222")
        self.assertEqual(self.data.title, "title", msg="标题为 title")
        self.assertEqual(self.data.area_id, 35, msg="分区id为 35")
        self.assertEqual(
            self.data.rtmp_addr,
            "rtmp://live-push.bilivideo.com/live-bvc/",
            msg="推流地址为默认地址",
        )
        self.assertEqual(
            self.data.rtmp_code,
            "?streamname=live_rtmp_code_streamname&key=rtmp_code_key=rtmp&pflag=2",
            msg="推流码",
        )
        self.assertEqual(self.data.csrf, "csrf", msg="csrf")
        self.assertDictEqual(
            self.data.room_data,
            {
                "uid": 1111,
                "room_id": 2222,
                "attention": 33,
                "online": 0,
                "description": "&lt;p&gt;description&lt;/p&gt;",
                "live_status": 0,
                "area_id": 35,
                "parent_area_id": 3,
                "parent_area_name": "手游",
                "title": "title",
                "live_time": "0000-00-00 00:00:00",
                "tags": "瞎玩,随缘,游戏,MC,王者荣耀,单机游戏",
                "area_name": "王者荣耀",
            },
            msg="房间信息",
        )
        self.assertListEqual(
            self.data.area,
            [
                {
                    "name": "网游",
                    "id": 2,
                    "list": [
                        {"name": "英雄联盟", "id": 86},
                        {"name": "无畏契约", "id": 329},
                    ],
                },
                {
                    "name": "手游",
                    "id": 3,
                    "list": [
                        {"name": "王者荣耀", "id": 35},
                        {"name": "和平精英", "id": 256},
                    ],
                },
            ],
            msg="分区信息",
        )

    def test_get_data(self):
        self.assertDictEqual(
            self.data.get_data_start(),
            {
                "room_id": 2222,
                "platform": "pc_link",
                "area_v2": 35,
                "csrf_token": "csrf",
                "csrf": "csrf",
                "type": 2,
            },
            msg="开播请求数据，正常需要签名",
        )
        self.assertDictEqual(
            self.data.get_data_stop(),
            {
                "room_id": 2222,
                "platform": "pc_link",
                "csrf_token": "csrf",
                "csrf": "csrf",
            },
            msg="下播请求数据",
        )
        self.assertDictEqual(
            self.data.get_data_area(),
            {
                "room_id": 2222,
                "area_id": 35,
                "activity_id": 0,
                "platform": "pc_link",
                "csrf_token": "csrf",
                "csrf": "csrf",
            },
            msg="更改分区请求数据",
        )
        self.assertDictEqual(
            self.data.get_data_title(),
            {
                "room_id": 2222,
                "platform": "pc_link",
                "title": "title",
                "csrf_token": "csrf",
                "csrf": "csrf",
            },
            msg="更改标题请求数据",
        )
        self.assertDictEqual(
            self.data.get_data_face(),
            {
                "room_id": 2222,
                "face_auth_code": "60024",
                "csrf_token": "csrf",
                "csrf": "csrf",
                "visit_id": "",
            },
            msg="人脸识别请求数据",
        )

    def test_get_area_name(self):
        self.assertListEqual(
            self.data.get_area_name(root_id=0), ["网游", "手游"], msg="获取主分区列表"
        )
        self.assertListEqual(
            self.data.get_area_name(root_id=2),
            ["英雄联盟", "无畏契约"],
            msg="获取主分区id为2的子分区列表",
        )
        self.assertListEqual(
            self.data.get_area_name(root_id=4),
            [],
            msg="获取主分区id为4的子分区列表，应当为空列表",
        )

    def test_get_area_name_by_id(self):
        self.assertTupleEqual(
            self.data.get_area_name_by_id(id=86),
            ("网游", "英雄联盟"),
            msg="获取id为86的主分区和子分区",
        )
        self.assertIsNone(
            self.data.get_area_name_by_id(id=-1),
            msg="获取id为-1的主分区和子分区，应当为None",
        )
        self.assertIsNone(
            self.data.get_area_name_by_id(id=999),
            msg="获取id为999的主分区和子分区，应当为None",
        )

    def test_get_area_id_by_name(self):
        self.assertEqual(
            self.data.get_area_id_by_name("王者荣耀", area_id=-1),
            35,
            msg="搜索所有分区，返回 35",
        )
        self.assertEqual(
            self.data.get_area_id_by_name("不存在", area_id=-1),
            0,
            msg="搜索所有分区，未找到，返回 0",
        )
        self.assertEqual(
            self.data.get_area_id_by_name("手游", area_id=0),
            3,
            msg="搜索主分区，返回3",
        )
        self.assertEqual(
            self.data.get_area_id_by_name("不存在", area_id=0),
            0,
            msg="搜索主分区，未找到，返回0",
        )
        self.assertEqual(
            self.data.get_area_id_by_name("王者荣耀", area_id=3),
            35,
            msg="搜索特定分区，返回 35",
        )
        self.assertEqual(
            self.data.get_area_id_by_name("不存在", area_id=3),
            0,
            msg="搜索特定分区，返回 0",
        )
        self.assertEqual(
            self.data.get_area_id_by_name("王者荣耀", area_id=999),
            0,
            msg="搜索不存在的分区，返回 0",
        )

    def test_is_valid_area_id(self):
        self.assertFalse(self.data.is_valid_area_id(2), msg="搜索存在的主分区，未找到")
        self.assertTrue(self.data.is_valid_area_id(329), msg="搜索存在的子分区，找到")
        self.assertFalse(
            self.data.is_valid_area_id(999), msg="搜索不存在的子分区，未找到"
        )

    def test_is_valid_live_title(self):
        self.assertTrue(self.data.is_valid_live_title("1" * 19), msg="长度为19的标题")
        self.assertTrue(self.data.is_valid_live_title("1" * 20), msg="长度为20的标题")
        self.assertTrue(self.data.is_valid_live_title("1" * 21), msg="长度为21的标题")
        self.assertTrue(self.data.is_valid_live_title("1" * 39), msg="长度为39的标题")
        self.assertTrue(self.data.is_valid_live_title("1" * 40), msg="长度为40的标题")
        self.assertFalse(self.data.is_valid_live_title("1" * 41), msg="长度为41的标题")
        self.assertFalse(self.data.is_valid_live_title(""), msg="长度为0的标题")

    def test_open_file(self):
        if get_platform() == "Windows":

            @patch(
                lib_str + "subprocess.call",
                lambda t: print(f"subprocess.call {t[0]} {t[1]}"),
            )
            @patch(lib_str + "os.startfile", lambda u: print(f"os.startfile {u}"))
            def test(self: Test):
                with patch(lib_str + "platform.system") as p:
                    p.return_value = "Windows"
                    with patch("sys.stdout", new=io.StringIO()) as output:
                        open_file("test.txt")
                    self.assertEqual(
                        output.getvalue(),
                        "os.startfile test.txt\n",
                        msg="win平台打开文件",
                    )
                    p.return_value = "Darwin"
                    with patch("sys.stdout", new=io.StringIO()) as output:
                        open_file("test.txt")
                    self.assertEqual(
                        output.getvalue(),
                        "subprocess.call open test.txt\n",
                        msg="mac平台打开文件",
                    )
                    p.return_value = "Manjaro"
                    with patch("sys.stdout", new=io.StringIO()) as output:
                        open_file("test.txt")
                    self.assertEqual(
                        output.getvalue(),
                        "subprocess.call xdg-open test.txt\n",
                        msg="linux平台(manjaro)打开文件",
                    )
        else:

            @patch(
                lib_str + "subprocess.call",
                lambda t: print(f"subprocess.call {t[0]} {t[1]}"),
            )
            def test(self: Test):
                with patch(lib_str + "platform.system") as p:
                    p.return_value = "Darwin"
                    with patch("sys.stdout", new=io.StringIO()) as output:
                        open_file("test.txt")
                    self.assertEqual(
                        output.getvalue(),
                        "subprocess.call open test.txt\n",
                        msg="mac平台打开文件",
                    )
                    p.return_value = "Manjaro"
                    with patch("sys.stdout", new=io.StringIO()) as output:
                        open_file("test.txt")
                    self.assertEqual(
                        output.getvalue(),
                        "subprocess.call xdg-open test.txt\n",
                        msg="linux平台(manjaro)打开文件",
                    )

        test(self)


if __name__ == "__main__":
    main()

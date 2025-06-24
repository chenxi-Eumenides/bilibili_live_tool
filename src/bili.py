import atexit
import json
from time import sleep

from qrcode import QRCode

from .lib import Config, Data
from .utils import get, get_json, is_exist, log, post, post_json


class Bili_Live:
    """
    B站直播
    """

    def __init__(self, config_file: str = None):
        self._config_ = Config(config_file=config_file)
        self._data_ = Data()
        self.exit_register()
        pass

    def _get_area_id_from_user_choose_(self) -> int:
        """
        从用户获取分区id

        Returns:
            int -- 分区id
        """
        print_max = 3
        id = 0
        while id <= 0:
            # 主分区
            print("请选择主分区：")
            root_area = self._data_.get_area_name()
            for index, data in enumerate(root_area):
                end = "\n" if index % 4 == print_max - 1 else " "
                print(f"{index + 1:2}: {data:<8}", end=end)
            print("\n请输入要选择的主分区 序号 或 名称：")
            select = input()
            while select == "":
                print("输入为空，重新输入主分区 序号 或 名称：")
                select = input()
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                select = self._data_.get_area_id(select)
            else:
                # 输入了序号
                select = self._data_.get_area_id(root_area[select - 1])
            root_id = select

            # 子分区
            print("\n子分区：")
            child_area = self._data_.get_area_name(root_id)
            for index, data in enumerate(child_area):
                end = "\n" if index % 4 == print_max - 1 else " "
                print(f"{index + 1:>2}: {data:<6}", end=end)
            print("\n请输入要选择的子分区 序号 或 名称（回车重新选择主分区）：")
            select = input()
            if select == "":
                log("重新选择主分区")
                continue
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                select = self._data_.get_area_id(select, root_id)
            else:
                # 输入了序号
                select = self._data_.get_area_id(child_area[select - 1], root_id)
            id = select
        return id

    def _get_live_title_from_user_(self) -> str:
        """
        从用户获取直播标题

        Returns:
            str -- 直播标题
        """
        log(f"当前标题为： {self._data_.room_data.get('title')}")
        log("请输入标题，标题不得超过20字（直接回车为原标题）：")
        new_title = input()
        while len(new_title) > 20:
            log("标题不得超过20字，请重新输入（直接回车为原标题）：")
            new_title = input()
        return new_title

    def _set_area_by_id_(self, id: int = 0):
        """
        根据id设置分区

        Keyword Arguments:
            id {int} -- 指定分区id (default: {0})

        Returns:
            _type_ -- _description_
        """
        if self._data_.is_valid_area_id(id):
            self._data_.area_id = id
        else:
            self._data_.area_id = self._get_area_id_from_user_choose_()

    def _set_live_title_(self, title: str = None):
        """
        设置直播间标题

        Keyword Arguments:
            title {str} -- 直播间标题 (default: {None})

        Returns:
            _type_ -- _description_
        """
        if title is None or len(title) <= 0:
            return False
        elif self._data_.is_valid_live_title(title):
            new_title = title
        else:
            new_title = self._get_live_title_from_user_()
            if not self._data_.is_valid_live_title(new_title):
                return False
        self._data_.title = new_title
        return True

    def _qr_login_(self):
        """
        二维码登录

        Arguments:
            data {Data} -- 数据类
        """
        res = get_json(
            "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
            headers={"User-Agent": self._data_.get_user_agent()},
        )
        qr_url = res["data"]["url"]
        qr_key = res["data"]["qrcode_key"]

        qr = QRCode()
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr.make_image().show()
        status = False
        while not status:
            status = self._get_qr_cookies_(qr_key, status)
            sleep(1)
        self._data_.cookies_str = json.dumps(
            self._data_.cookies, separators=(",", ":"), ensure_ascii=False
        )
        self._data_.csrf = self._data_.cookies.get("bili_jct")

    def _get_qr_cookies_(self, qr_key: str, status: bool) -> dict:
        """
        获取二维码登录结果

        Arguments:
            qr_key {str} -- 本次登录的二维码密钥
            status {bool} -- 之前的结果

        Returns:
            dict -- 本次的结果
        """
        login_res = get(
            url="https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
            headers={"User-Agent": self._data_.get_user_agent()},
            params={"qrcode_key": qr_key},
        )
        code = login_res.json()["data"]["code"]
        if code == 0:
            self._data_.cookies = login_res.cookies.get_dict()
            self._data_.refresh_token = login_res.json()["data"]["refresh_token"]
            return True
        elif code == 86038:
            log("二维码已失效，请重新启动软件", 18)
        elif code == 86090:
            if not status:
                log("二维码已扫描，等待确认")
        return False

    def login(self) -> dict:
        """
        登录
        """
        if not is_exist(self._config_.config_file):
            self._qr_login_()
        elif not self._config_.read_config(self._data_):
            self._qr_login_()
        else:
            if self.get_user_status() != 0:
                self._qr_login_()
            else:
                return True

    def update_area(self):
        """
        更新直播分区列表 \n
        分区结构：\n
        area = [ \n
            {
                "name":name,
                "id":id,
                "list":[
                    {
                        "name":name,
                        "id":id,
                    },
                ],
            },
        ]
        """
        pt_data: dict = get_json(
            "https://api.live.bilibili.com/room/v1/Area/getList",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
        )
        results = []
        for root in pt_data.get("data"):
            part_results = []
            for part in root.get("list"):
                part_result = {"name": part.get("name"), "id": int(part.get("id"))}
                part_results.append(part_result)
            result = {
                "name": root.get("name"),
                "id": int(root.get("id")),
                "list": part_results,
            }
            results.append(result)

        self._config_.area = results

    def update_room_data(self):
        """
        更新直播状态
        """
        if self._data_.room_id < 0:
            log("room_id获取失败，请重新尝试", 3)
        res = post_json(
            "https://api.live.bilibili.com/room/v1/Room/get_info",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data={"room_id": self._data_.room_id},
        )
        if res.get("code") != 0:
            log("获取直播间状态出错，不存在该直播间", 3)
        else:
            self._data_.room_data = res.get("data")
            self._data_.live_status = self._data_.room_data.get("live_status", -1)

    def set_live_title(self, title: str = None):
        """
        单独设置直播标题

        Keyword Arguments:
            title {str} -- 直播标题 (default: {None})
        """
        if self._set_live_title_(title):
            res = post(
                url="https://api.live.bilibili.com/room/v1/Room/update",
                headers=self._data_.get_header(),
                cookies=self._data_.cookies,
                data=self._data_.get_data_title(),
            )
            return res

    def set_area(self, id: int = 0):
        """
        单独设置分区(开播无需单独设置)。

        Keyword Arguments:
            id {int} -- 分区id (default: {0})
        """
        self._set_area_by_id_(id)
        data = post_json(
            "https://api.live.bilibili.com/room/v1/Room/update",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_id(),
        )
        if data.get("code") == 0:
            log("更改分区成功！")
        else:
            log(f"更改分区({self._data_.area_id})失败,", 20, data.get("msg"))

    def start_live(self):
        """
        启动直播
        """
        self._set_area_by_id_()
        res = post_json(
            "https://api.live.bilibili.com/room/v1/Room/startLive",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_start(),
        )
        if res["code"] != 0:
            log("获取推流码失败，cookie可能失效，请重新获取！", 5, res)
        else:
            rtmp = res["data"]["rtmp"]
            self._data_.rtmp_addr = rtmp["addr"]
            self._data_.rtmp_code = rtmp["code"]
        return res

    def stop_live(self):
        """
        停止直播
        """
        res = post(
            "https://api.live.bilibili.com/room/v1/Room/stopLive",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_stop(),
        )
        return res

    def get_live_status(self):
        return self._data_.live_status

    def get_rtmp(self):
        return self._data_.rtmp_addr, self._data_.rtmp_code

    def get_user_status(self) -> int:
        res = get_json(
            # url="https://account.bilibili.com/site/getCoin",
            url="https://api.bilibili.com/x/web-interface/nav/stat",
            headers=self._data_.get_header(),
            cookies=self._data_.cookies,
        )
        if res is None:
            return -1
        if res.get("code") == -101:
            self._data_.cookies = {}
            self._data_.cookies_str = ""
            self._data_.cookies_str_old = ""
            log("cookies已过期，请重新登录")
        return res.get("code")

    def get_room_status(self) -> str:
        data = self._data_.room_data
        res = [
            f"主播uid ：{data.get('uid')}      粉丝数：{data.get('attention')}",
            f"直播标题：{data.get('title')}  直播间号：{data.get('room_id')}",
            f"直播间描述：{data.get('description')}",
            f"当前分区：{data.get('parent_area_name')}({data.get('parent_area_id')}) {data.get('area_name')}({data.get('area_id')})",
            f"直播时长：{data.get('live_time')}",
        ]
        print("\n".join(res))

    def save(self):
        log("正在保存配置...")
        self._config_.save_config(self._data_)

    def exit_register(self):
        atexit.register(self.save)

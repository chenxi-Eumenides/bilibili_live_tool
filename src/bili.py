import atexit
import json
from time import sleep

from qrcode import QRCode

from .lib import Config, Data
from .utils import (
    check_bat,
    check_readme,
    get,
    get_help_content,
    get_json,
    get_version,
    is_exist,
    log,
    post_json,
)


class Bili_Live:
    """
    B站直播
    """

    def __init__(self, config_file: str = "config.json", cookies: str = ""):
        self._config_ = Config(config_file=config_file)
        self._data_ = Data()
        atexit.register(self._exit_)
        atexit.register(self.save_config)
        check_readme(config_file=config_file)
        check_bat()

        if cookies:
            try:
                self._data_.cookies = json.loads(cookies)
                self._get_info_from_cookies_(self._data_.cookies)
            except Exception as e:
                log("传入的cookies错误，无法加载", 21, str(e))

        log(f"初始化完成，当前版本：{get_version()}")
        log("任何时候，按 Ctrl+C 退出程序")
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
            log("请选择主分区：")
            root_area = self._data_.get_area_name()
            for index, data in enumerate(root_area):
                end = "\n" if index % 4 == print_max - 1 else " "
                print(f"{index + 1:2}: {data:<8}", end=end)
            log("\n请输入要选择的主分区 序号 或 名称：")
            select = input()
            while select == "":
                log("输入为空，重新输入主分区 序号 或 名称：")
                select = input()
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                select = self._data_.get_area_id_by_name(select)
            else:
                # 输入了序号
                select = self._data_.get_area_id_by_name(root_area[select - 1])
            root_id = select

            # 子分区
            log("\n子分区：")
            child_area = self._data_.get_area_name(root_id)
            for index, data in enumerate(child_area):
                end = "\n" if index % 4 == print_max - 1 else " "
                print(f"{index + 1:>2}: {data:<6}", end=end)
            log("\n请输入要选择的子分区 序号 或 名称（回车重新选择主分区）：")
            select = input()
            if select == "":
                log("重新选择主分区")
                continue
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                select = self._data_.get_area_id_by_name(select, root_id)
            else:
                # 输入了序号
                select = self._data_.get_area_id_by_name(
                    child_area[select - 1], root_id
                )
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

    def _get_info_from_cookies_(self):
        self._data_.csrf = self._data_.cookies.get("bili_jct")
        self._data_.user_id = self._data_.cookies.get("DedeUserID")
        self._data_.room_id = (
            get_json(
                url=f"https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid={self._data_.user_id}",
                headers={"User-Agent": self._data_.get_user_agent()},
            )
            .get("data")
            .get("room_id")
        )

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

    def _update_area_(self):
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

        self._data_.area = results

    def _update_room_data_(self):
        """
        更新直播间状态
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
            self._data_.title = self._data_.room_data.get("title", "")
            self._data_.area_id = self._data_.room_data.get("area_id", -1)

    def _exit_(self):
        print("按回车结束程序 或 直接关闭窗口")
        input()

    def login(self) -> dict:
        """
        登录
        """
        if not is_exist(self._config_.config_file):
            self.qr_login()
        elif not self.read_config():
            self.qr_login()
        else:
            if self.get_user_status() != 0:
                self.qr_login()
        self._get_info_from_cookies_()
        self._update_area_()
        self._update_room_data_()

    def read_config(self):
        return self._config_.read_config(self._data_)

    def qr_login(self):
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

    def set_live_title(self, title: str = None):
        """
        设置直播标题。不传入则为手动输入。

        Keyword Arguments:
            title {str} -- 直播标题 (default: {None})
        """
        if title is None:
            title = self._get_live_title_from_user_()
        if len(title) <= 0 or not self._data_.is_valid_live_title(title):
            log("非法标题，跳过。")
            return
        self._data_.title = title
        res = post_json(
            url="https://api.live.bilibili.com/room/v1/Room/update",
            headers=self._data_.get_header(),
            cookies=self._data_.cookies,
            data=self._data_.get_data_title(),
        )
        if res.get("code") == 0:
            if (status := res.get("data").get("audit_title_status")) == 0:
                log("更改标题成功。")
            elif status == 2:
                log("更改标题成功，正在审核中。")
        else:
            log(f"更改标题失败，{res.get('msg')}")

    def set_live_area(self, id: int | str = None):
        """
        单独设置分区，开播需单独设置。不传入则为手动选择。

        Keyword Arguments:
            id {int|str} -- 分区id或分区名称 (default: {None})
        """
        if id is None:
            self._set_area_by_id_(self._get_area_id_from_user_choose_())
        elif type(id) is int:
            self._set_area_by_id_(id)
        elif type(id) is str:
            self._set_area_by_id_(self.get_area_id_by_name(id))
        else:
            log("id值需要为int或str", 20)
        data = post_json(
            "https://api.live.bilibili.com/room/v1/Room/update",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_id(),
        )
        if data.get("code") == 0:
            log(
                f"更改分区({self._data_.get_area_name_by_id(self._data_.area_id)[1]}:{self._data_.area_id})成功！"
            )
        else:
            log(
                f"更改分区({self._data_.get_area_name_by_id(self._data_.area_id)[1]}:{self._data_.area_id})失败,",
                20,
                data.get("msg"),
            )

    def get_user_status(self) -> int:
        res = get_json(
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

    def start_live(self):
        """
        启动直播
        """
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
            log("已开播")
        return res

    def stop_live(self):
        """
        停止直播
        """
        res = post_json(
            "https://api.live.bilibili.com/room/v1/Room/stopLive",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_stop(),
        )
        if res["code"] != 0:
            log(
                "下播失败，请手动前往网页下播：https://link.bilibili.com/p/center/index#/my-room/start-live",
                21,
            )
        else:
            log("已下播")
        return res

    def save_config(self):
        if self._data_.cookies_str != "":
            log("正在保存配置...")
            self._config_.save_config(self._data_)
        else:
            log("无数据，跳过保存。")

    def get_live_status(self) -> int:
        return self._data_.live_status

    def get_rtmp(self) -> tuple[str, str]:
        return self._data_.rtmp_addr, self._data_.rtmp_code

    def get_area_id_by_name(self, name: str) -> int:
        return self._data_.get_area_id_by_name(name=name, area_id=-1)

    def get_room_info(self) -> str:
        data = self._data_.room_data
        res = [
            "当前正在直播" if self.get_live_status() == 1 else "当前不在直播",
            f"主播uid ：{data.get('uid')}      粉丝数：{data.get('attention')}",
            f"直播间号：{data.get('room_id')}",
            f"直播标题：{data.get('title')}",
            f"直播间描述：{data.get('description')[9:-10]}",
            f"当前分区：{data.get('parent_area_name')}({data.get('parent_area_id')}) {data.get('area_name')}({data.get('area_id')})",
            f"直播起始时间：{data.get('live_time')}",
            f"当前在线观众：{data.get('online')}",
        ]
        return "\n".join(res)

    def get_help_info(self) -> str:
        return "\n".join(get_help_content())

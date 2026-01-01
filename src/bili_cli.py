import atexit
import json
import os
from time import sleep

from qrcode import QRCode

from .bili_lib import (
    Data,
    check_bat,
    check_readme,
    get,
    get_help_content,
    get_json,
    get_version,
    is_exist,
    post_json,
    sign_data,
    wait_print,
)
from .constant import (
    AREA_OUTPUT_LINE_NUM,
    CONFIG_FILE,
    QR_FACE_IMG,
    QR_IMG,
    TITLE_MAX_CHAR,
    LIVEHIME_BUILD,
    LIVEHIME_VERSION,
    URL_GET_ROOM_ID,
    URL_GET_QR_RES,
    URL_GENERATE_QR,
    URL_GET_AREA_LIST,
    URL_GET_ROOM_STATUS,
    URL_UPDATE_ROOM,
    URL_GET_USER_STATUS,
    URL_CHECK_FACE,
    URL_START_LIVE,
    URL_STOP_LIVE,
    URL_GET_LIVE_VERSION,
)


class Bili_Live:
    """
    B站直播
    """
    _data_: Data

    def __init__(self, config_file: str = CONFIG_FILE, cookies: str = ""):
        self._data_ = Data(config_file=config_file)
        atexit.register(self._exit_)
        atexit.register(self.save_config)
        check_readme(config_file=config_file)
        check_bat()

        if cookies:
            try:
                self._data_.cookies = json.loads(cookies)
                self._get_info_from_cookies_()
            except Exception as e:
                print(f"传入的cookies错误，无法加载\n报错原因：{str(e)}")
                raise e

        print(f"初始化完成，当前版本：{get_version()}")
        print("任何时候，按 Ctrl+C 退出程序")
        pass

    def _get_area_id_from_user_choose_(self) -> int:
        """
        从用户获取分区id

        Returns:
            int -- 分区id
        """
        id = 0
        while id <= 0:
            # 主分区
            print("请选择主分区：")
            root_area = self._data_.get_area_name()
            for index, data in enumerate(root_area):
                end = (
                    "\n"
                    if index % AREA_OUTPUT_LINE_NUM == AREA_OUTPUT_LINE_NUM - 1
                    else " "
                )
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
                area_id = self._data_.get_area_id_by_name(select, area_id=0)
                if area_id == 0:
                    # 输入的不是主分区
                    area_id = self._data_.get_area_id_by_name(select, area_id=-1)
                    if area_id == 0:
                        raise Exception("输入错误，未找到分区名")
                    id = area_id
                    break
            else:
                # 输入了序号
                if 1 <= select <= len(root_area):
                    area_id = self._data_.get_area_id_by_name(
                        root_area[select - 1], area_id=0
                    )
                else:
                    print("序号不在范围内，请重新输入。")
                    continue
            root_id = area_id

            # 子分区
            child_area = self._data_.get_area_name(root_id)
            if child_area == []:
                raise Exception("子分区获取错误，检查主分区id是否正确")
            print("\n请选择子分区：")
            for index, data in enumerate(child_area):
                end = (
                    "\n"
                    if index % AREA_OUTPUT_LINE_NUM == AREA_OUTPUT_LINE_NUM - 1
                    else " "
                )
                print(f"{index + 1:>2}: {data:<6}", end=end)
            print("\n请输入要选择的子分区 序号 或 名称（回车重新选择主分区）：")
            select = input()
            if select == "":
                print("重新选择主分区")
                continue
            try:
                select = int(select)
            except Exception:
                # 输入了字符串
                area_id = self._data_.get_area_id_by_name(select, root_id)
            else:
                # 输入了序号
                if 1 <= select <= len(child_area):
                    area_id = self._data_.get_area_id_by_name(
                        child_area[select - 1], root_id
                    )
                else:
                    print("输入的序号不在范围内")
                    continue
            id = area_id
        return id

    def _get_live_title_from_user_(self) -> str:
        """
        从用户获取直播标题

        Returns:
            str -- 直播标题
        """
        print(f"当前标题为： {self._data_.room_data.get('title')}")
        print(f"请输入标题，标题不得超过{TITLE_MAX_CHAR}字（直接回车为原标题）：")
        new_title = input()
        while len(new_title) > TITLE_MAX_CHAR:
            print(f"标题不得超过{TITLE_MAX_CHAR}字，请重新输入（直接回车为原标题）：")
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
        room_data = get_json(
            url=f"{URL_GET_ROOM_ID}?uid={self._data_.user_id}",
            headers={"User-Agent": self._data_.get_user_agent()},
        )
        if room_data.get("code") != 0:
            raise Exception("获取直播间号失败，检查是否开通直播间。")
        self._data_.room_id = room_data.get("data").get("room_id")

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
            url=URL_GET_QR_RES,
            headers={"User-Agent": self._data_.get_user_agent()},
            params={"qrcode_key": qr_key},
        )
        code = login_res.json()["data"]["code"]
        if code == 0:
            self._data_.cookies = login_res.cookies.get_dict()
            self._data_.refresh_token = login_res.json()["data"]["refresh_token"]
            return True
        elif code == 86038:
            raise Exception("二维码已失效，请重新启动软件")
        elif code == 86090:
            if not status:
                print("二维码已扫描，等待确认")
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
            url=URL_GET_AREA_LIST,
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
        if len(results) > 0:
            self._data_.area = results

    def _update_room_data_(self):
        """
        更新直播间状态
        """
        if self._data_.room_id < 0:
            print("room_id获取失败，请重新尝试")
            raise
        res = post_json(
            url=URL_GET_ROOM_STATUS,
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data={"room_id": self._data_.room_id},
        )
        if res.get("code") != 0:
            print("获取直播间状态出错，不存在该直播间")
            raise
        else:
            self._data_.room_data = res.get("data")
            self._data_.live_status = self._data_.room_data.get("live_status", -1)
            self._data_.title = self._data_.room_data.get("title", "")
            self._data_.area_id = self._data_.room_data.get("area_id", -1)

    def _exit_(self):
        try:
            if os.path.exists(QR_IMG):
                os.remove(QR_IMG)
            if os.path.exists(QR_FACE_IMG):
                os.remove(QR_FACE_IMG)
            print("按 Enter回车 结束程序 或 直接关闭窗口")
            input()
        except (EOFError,KeyboardInterrupt):
            pass

    def login(self) -> dict:
        """
        登录
        """
        if not self.check_config():
            self.qr_login()
        elif not self.read_config():
            print(f"读取{self._data_.config_file}失败，请重新登陆")
            self.qr_login()
        else:
            if self.get_user_status() != 0:
                self.qr_login()
        self._get_info_from_cookies_()
        self._update_area_()
        self._update_room_data_()

    def read_config(self):
        return self._data_.read_config()
    
    def check_config(self):
        return self._data_.check_config()

    def qr_login(self):
        """
        二维码登录

        Arguments:
            data {Data} -- 数据类
        """
        res = get_json(
            url=URL_GENERATE_QR,
            headers={"User-Agent": self._data_.get_user_agent()},
        )
        qr_url = res.get("data").get("url")
        qr_key = res.get("data").get("qrcode_key")

        qr = QRCode()
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        qr_image.show()
        print(f"若无法弹出二维码，请手动打开目录下的 {QR_IMG} 进行扫码。")
        qr_image.save(QR_IMG)
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
            print("非法标题，跳过。")
            return
        self._data_.title = title
        if (data := self._data_.get_data_title()) is None:
            raise Exception(
                f"数据错误(room_id={self._data_.room_id},title={self._data_.title},csrf={self._data_.csrf})"
            )
        res = post_json(
            url=URL_UPDATE_ROOM,
            headers=self._data_.get_header(),
            cookies=self._data_.cookies,
            data=data,
        )
        if res.get("code") == 0:
            if (status := res.get("data").get("audit_title_status")) == 0:
                print("更改标题成功。")
            elif status == 2:
                print("更改标题成功，正在审核中。")
        else:
            print(f"更改标题失败，{res.get('msg')}")

    def set_live_area(self, id: int | str = None):
        """
        单独设置分区，开播需单独设置。不传入则为手动选择。

        Keyword Arguments:
            id {int|str} -- 分区id或分区名称 (default: {None})
        """
        # 获取分区id
        if id is None:
            self._set_area_by_id_(self._get_area_id_from_user_choose_())
        elif type(id) is int:
            self._set_area_by_id_(id)
        elif type(id) is str:
            self._set_area_by_id_(self.get_area_id_by_name(id))
        else:
            raise Exception("id值需要为int或str")
        # 发送分区api
        if (data := self._data_.get_data_area()) is None:
            raise Exception(
                f"数据错误(room_id={self._data_.room_id},area_id={self._data_.area_id},csrf={self._data_.csrf})"
            )
        data = post_json(
            url=URL_UPDATE_ROOM,
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=data,
        )
        # api结果
        if (area_name := self._data_.get_area_name_by_id(self._data_.area_id)) is None:
            print(f"无法找到分区名 (area_id={self._data_.area_id})")
        if data.get("code") == 0:
            print(f"更改分区({area_name[1]}:{self._data_.area_id})成功！")
        else:
            raise Exception(
                f"更改分区({area_name[1]}:{self._data_.area_id})失败\n报错原因：{data.get('msg')}"
            )

    def get_user_status(self) -> int:
        res = get_json(
            url=URL_GET_USER_STATUS,
            headers=self._data_.get_header(),
            cookies=self._data_.cookies,
        )
        if res is None:
            return -1
        if res.get("code") == -101:
            self._data_.cookies = {}
            self._data_.cookies_str = ""
            self._data_.cookies_str_old = ""
            print("cookies已过期，请重新登录")
        return res.get("code")

    def qr_face(self, qr_url: str) -> bool:
        """
        二维码人脸识别

        Arguments:
            qr_url {str} -- 扫码url
        """
        qr = QRCode()
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        qr_image.show()
        print(f"若没有弹出二维码，请手动打开目录下的 {QR_FACE_IMG} 进行扫码")
        qr_image.save(QR_FACE_IMG)

        data = self._data_.get_data_face()
        status = False
        while not status:
            try:
                res = post_json(
                    URL_CHECK_FACE,
                    cookies=self._data_.cookies,
                    headers=self._data_.get_header(),
                    data=data
                )
                print(res)
                if res.get("data") and res.get("data").get("is_identified"):
                    status = True
                else:
                    sleep(1)
            except Exception as e:
                print(f"报错：{str(e)}")
                return False
        return True

    def start_live(self, retry: int = 0) -> bool:
        """
        启动直播
        """
        self.update_live_version()
        data = self._data_.get_data_start()
        res = post_json(
            url=URL_START_LIVE,
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=sign_data(data),
        )
        if res.get("code") != 0:
            if res.get("code") == 60024 or "qr" in res.get("data"):
                print(f"{res.get('msg')} ({res.get('code')})，请用客户端扫码进行人脸识别。")
                if self.qr_face(res.get("data").get("qr")):
                    return self.start_live()
                else:
                    raise Exception(
                        f"请使用app扫码完成人脸识别后，重新使用本软件开播。"
                    )

            raise Exception(
                f"获取推流码失败！\n报错原因：{res.get('msg')} ({res.get('code')})"
            )
        else:
            rtmp = res.get("data").get("rtmp")
            self._data_.rtmp_addr = rtmp.get("addr")
            self._data_.rtmp_code = rtmp.get("code")
            print("已开播")
            return True

    def stop_live(self):
        """
        停止直播
        """
        if (data := self._data_.get_data_stop()) is None:
            raise Exception(
                f"数据错误(room_id={self._data_.room_id},csrf={self._data_.csrf})"
            )
        res = post_json(
            url=URL_STOP_LIVE,
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=data,
        )
        if res.get("code") != 0:
            raise Exception(
                f"下播失败,{res.get('msg')}\n请手动前往网页下播：https://link.bilibili.com/p/center/index#/my-room/start-live"
            )
        else:
            print("已下播")
        return res

    def save_config(self):
        print("")
        if self._data_.cookies_str != "" and self._data_.user_id != -1:
            print("正在保存配置...")
            self._data_.save_config()
        else:
            print("无数据，跳过保存。")

    def get_live_status(self) -> int:
        return self._data_.live_status

    def get_rtmp(self) -> tuple[str, str]:
        print("推流地址：")
        print("")
        print(self._data_.rtmp_addr)
        print("")
        print("推流码：")
        print("")
        print(self._data_.rtmp_code)
        print("")
        if self._data_.rtmp_code == self._data_.rtmp_code_old:
            print("推流码无变化，可以直接开播。")
        else:
            print("请将 推流地址 和 推流码 复制到obs直播配置中，再开播。")

    def get_area_id_by_name(self, name: str) -> int:
        return self._data_.get_area_id_by_name(name=name, area_id=-1)

    def print_room_info(self):
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
        print("\n".join(res))

    def get_help_info(self) -> str:
        return "\n".join(get_help_content())

    def update_live_version(self):
        data=sign_data({
            "system_version":2,
        })
        res = get_json(
            url=f"{URL_GET_LIVE_VERSION}?{'&'.join([f'{k}={v}' for k, v in data.items()])}",
            headers=self._data_.get_header(),
        )
        if res.get("code")==0:
            self._data_.live_version = res.get("data").get("curr_version")
            self._data_.live_build = str(res.get("data").get("build"))
            
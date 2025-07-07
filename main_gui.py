import sys
import json
import threading
import time
from dataclasses import dataclass, field
from PIL import Image, ImageQt
import io
import requests
from qrcode import QRCode
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QSizePolicy, QMessageBox, QDialog,
    QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QFontDatabase, QIcon, QFontInfo
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, QEvent

gui_log_text_widget = None


class WorkerSignals(QObject):
    log_message = pyqtSignal(str)
    qr_code_ready = pyqtSignal(QPixmap)
    login_success = pyqtSignal()
    update_info = pyqtSignal()
    show_rtmp_info = pyqtSignal(str, str)
    title_history_updated = pyqtSignal(list)


def log(string: str, reason: int = -1, error_data: any = None):
    message = string
    if reason != -1 and error_data is not None:
        message = f"{string}\n错误原因：{str(error_data)}"

    if gui_log_text_widget:
        QApplication.instance().postEvent(gui_log_text_widget, LogEvent(message))
    else:
        print(message)


class LogEvent(QEvent):
    def __init__(self, message):
        super().__init__(QEvent.Type(QEvent.User + 1))
        self.message = message


class LogTextEdit(QTextEdit):
    def event(self, event):
        if event.type() == QEvent.Type(QEvent.User + 1):
            self.insertPlainText(event.message + "\n")
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
            return True
        return super().event(event)


def is_exist(file) -> bool:
    import os
    return os.path.exists(file)


def post(url: str, params=None, cookies=None, headers=None, data=None):
    try:
        res = requests.post(
            url=url, params=params, cookies=cookies, headers=headers, data=data
        )
    except ConnectionResetError as e:
        log(f"请求API ({url}) 过多，请稍后再尝试。", error_data=str(e))
        return None
    except Exception as e:
        log(f"请求API ({url}) 出错", error_data=str(e))
        return None
    else:
        if res.status_code != 200:
            log(f"请求API ({url}) 出错，状态码为 {res.status_code}")
            return None
    return res


def post_json(
        url: str, params=None, cookies=None, headers=None, data=None
) -> dict | list | None:
    res = post(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res and res.status_code == 200:
        return res.json()
    return None


def get(url: str, params=None, cookies=None, headers=None, data=None):
    try:
        res = requests.get(
            url=url, params=params, cookies=cookies, headers=headers, data=data
        )
    except Exception as e:
        log(f"请求API ({url}) 出错", error_data=str(e))
        return None
    else:
        if res.status_code != 200:
            log(f"请求API ({url}) 出错，状态码为 {res.status_code}")
            return None
    return res


def get_json(
        url: str, params=None, cookies=None, headers=None, data=None
) -> dict | list | None:
    res = get(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res and res.status_code == 200:
        return res.json()
    return None


def get_cookies(url: str, params=None, cookies=None, headers=None, data=None) -> dict:
    res = get(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res:
        return res.cookies.get_dict()
    return {}


def gen_list():
    return []


def gen_dict():
    return {}


@dataclass
class Config:
    config_file: str = "config.json"

    def read_config(self, data: "Data") -> bool:
        if not is_exist(self.config_file):
            log("config.json 不存在，请重新登录。")
            return False
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config: dict = json.load(f)
        except json.JSONDecodeError as e:
            log(f"读取 config.json 失败，JSON 格式错误: {e}")
            return False
        except Exception as e:
            log(f"读取 config.json 失败，请重新登录: {e}")
            return False
        else:
            data.user_id = config.get("user_id", -1)
            data.room_id = config.get("room_id", -1)
            data.area_id = config.get("area_id", -1)
            data.title = config.get("title", "")
            data.rtmp_addr = config.get("rtmp_addr", "")
            data.rtmp_code = config.get("rtmp_code", "")
            data.rtmp_code_old = config.get("rtmp_code", "")
            data.cookies_str = config.get("cookies_str", "")
            data.cookies_str_old = config.get("cookies_str", "")
            data.csrf = config.get("csrf", "")
            data.refresh_token = config.get("refresh_token", "")
            self.area = config.get("area", []) if isinstance(config.get("area"), list) else []
            data.room_data = config.get("room_data", {})
            data.title_history = config.get("title_history", [])

        if not data.cookies_str:
            log("config.json 中 cookies 为空，请重新登录。")
            return False

        try:
            data.cookies = json.loads(data.cookies_str)
        except json.JSONDecodeError as e:
            log(f"加载 cookies 失败，cookies 格式错误: {e}")
            return False
        except Exception as e:
            log(f"加载 cookies 失败: {e}")
            return False
        return True

    def save_config(self, data: "Data"):
        config = {
            "user_id": data.user_id,
            "room_id": data.room_id,
            "area_id": data.area_id,
            "title": data.title,
            "rtmp_addr": data.rtmp_addr,
            "rtmp_code": data.rtmp_code,
            "cookies_str": data.cookies_str,
            "csrf": data.csrf,
            "refresh_token": data.refresh_token,
            "room_data": data.room_data,
            "area": data.area,
            "title_history": data.title_history,
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            log(f"保存 config.json 失败: {e}")


@dataclass
class Data:
    user_id: int = -1
    room_id: int = -1
    area_id: int = -1
    title: str = ""
    live_status: int = -1
    room_data: dict = field(default_factory=gen_dict)
    rtmp_addr: str = ""
    rtmp_code: str = ""
    rtmp_code_old: str = ""
    cookies: dict = field(default_factory=gen_dict)
    cookies_str: str = ""
    cookies_str_old: str = ""
    csrf: str = ""
    refresh_token: str = ""
    area: list[dict[str, str | int | dict[str, str | int]]] = field(
        default_factory=gen_list
    )
    title_history: list[str] = field(default_factory=gen_list)

    def get_data_start(self) -> dict[str, str | int]:
        if not (self.room_id > 0 and self.area_id > 0 and self.csrf):
            log(f"参数无效 (room_id={self.room_id},area_id={self.area_id},csrf={self.csrf})")
            raise ValueError("启动直播参数无效")
        return {
            "room_id": self.room_id,
            "platform": "pc_link",
            "area_v2": self.area_id,
            "backup_stream": "0",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_stop(self) -> dict[str, str]:
        if not (self.room_id > 0 and self.csrf):
            log(f"参数无效 (room_id={self.room_id},csrf={self.csrf})")
            raise ValueError("停止直播参数无效")
        return {
            "room_id": self.room_id,
            "platform": "pc_link",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_title(self) -> dict[str, str]:
        if not (self.room_id > 0 and self.title and self.csrf):
            log(f"参数无效 (room_id={self.room_id},title={self.title},csrf={self.csrf})")
            raise ValueError("设置标题参数无效")
        return {
            "room_id": self.room_id,
            "platform": "pc_link",
            "title": self.title,
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_id(self) -> dict[str, str | int]:
        if not (self.room_id > 0 and self.area_id > 0 and self.csrf):
            log(f"参数无效 (room_id={self.room_id},area_id={self.area_id},csrf={self.csrf})")
            raise ValueError("设置分区参数无效")
        return {
            "room_id": self.room_id,
            "area_id": self.area_id,
            "activity_id": 0,
            "platform": "pc_link",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_user_agent(self) -> str:
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def get_header(self) -> dict[str, str]:
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://link.bilibili.com",
            "referer": "https://link.bilibili.com/p/center/index",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": self.get_user_agent(),
        }

    def get_area_name_by_id(self, id: int) -> tuple[str | None, str | None]:
        if id <= 0 or id >= 1000:
            return None, None
        for data in self.area:
            for part in data.get("list", []):
                if id == part.get("id"):
                    return data.get("name"), part.get("name")
        return None, None

    def get_area_name(self, root_id: int = 0) -> list[str]:
        results = []
        for data in self.area:
            if root_id:
                if data.get("id") == root_id:
                    for part in data.get("list", []):
                        results.append(part.get("name"))
                    break
            else:
                results.append(data.get("name"))
        return results

    def get_area_id_by_name(self, name: str, area_id: int = 0) -> int:
        if not name:
            log("搜索名称为空，请重新尝试！")
            return 0
        for part in self.area:
            if area_id > 0:
                if area_id == part.get("id"):
                    for p in part.get("list", []):
                        if name in p.get("name"):
                            return p.get("id")
            elif area_id == 0:
                if name in part.get("name"):
                    return part.get("id")
            elif area_id == -1:
                for p in part.get("list", []):
                    if name in p.get("name"):
                        return p.get("id")
        if area_id > 0:
            log("获取子分区ID失败，请重新尝试！")
        elif area_id == 0:
            log("获取主分区ID失败，请重新尝试！")
        elif area_id == -1:
            log(f"获取分区ID失败。({name}:{area_id})")
        return 0

    def is_valid_area_id(self, id: int) -> bool:
        if id <= 0 or id >= 1000:
            return False
        for data in self.area:
            for part in data.get("list", []):
                if id == part.get("id"):
                    return True
        return False

    def is_valid_live_title(self, title: str) -> bool:
        if title is None:
            return False
        if len(title) > 20 or len(title) <= 0:
            return False
        return True


class Bili_Live(QObject):
    def __init__(self, config_file: str = "config.json", signals=None):
        super().__init__()
        self._config_ = Config(config_file=config_file)
        self._data_ = Data()
        self.signals = signals if signals else WorkerSignals()
        self._stop_qr_poll_flag = False

        log(f"初始化完成")

    def _get_info_from_cookies_(self):
        self._data_.csrf = self._data_.cookies.get("bili_jct")
        self._data_.user_id = self._data_.cookies.get("DedeUserID")

        room_res = get_json(
            url=f"https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid={self._data_.user_id}",
            headers={"User-Agent": self._data_.get_user_agent()},
        )
        if room_res and room_res.get("data"):
            self._data_.room_id = room_res.get("data").get("room_id")
        else:
            log("获取直播间ID失败，请检查登录状态或UID是否正确。")
            self._data_.room_id = -1

    def _get_qr_cookies_(self, qr_key: str) -> bool:
        login_res = get(
            url="https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
            headers={"User-Agent": self._data_.get_user_agent()},
            params={"qrcode_key": qr_key},
        )
        if not login_res:
            return False

        res_json = login_res.json()
        code = res_json["data"]["code"]

        if code == 0:
            self._data_.cookies = login_res.cookies.get_dict()
            self._data_.refresh_token = res_json["data"]["refresh_token"]
            return True
        elif code == 86038:
            log("二维码已失效，请重新点击登录按钮。")
            self._stop_qr_poll_flag = True
            return False
        elif code == 86090:
            log("二维码已扫描，等待确认。")
            return False
        return False

    def _update_area_(self):
        pt_data: dict | None = get_json(
            "https://api.live.bilibili.com/room/v1/Area/getList",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
        )
        if not pt_data or pt_data.get("code") != 0:
            log("获取分区列表失败。")
            return

        results = []
        for root in pt_data.get("data", []):
            part_results = []
            for part in root.get("list", []):
                part_result = {"name": part.get("name"), "id": int(part.get("id"))}
                part_results.append(part_result)
            result = {
                "name": root.get("name"),
                "id": int(root.get("id")),
                "list": part_results,
            }
            results.append(result)

        self._data_.area = results
        self._config_.area = results

    def _update_room_data_(self):
        if self._data_.room_id < 0:
            log("获取 room_id 失败，无法更新直播间状态。")
            return
        res = post_json(
            "https://api.live.bilibili.com/room/v1/Room/get_info",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data={"room_id": self._data_.room_id},
        )
        if not res or res.get("code") != 0:
            log("获取直播间状态出错，直播间不存在或 Cookie 无效。")
        else:
            self._data_.room_data = res.get("data")
            self._data_.live_status = self._data_.room_data.get("live_status", -1)
            self._data_.title = self._data_.room_data.get("title", "")
            self._data_.area_id = self._data_.room_data.get("area_id", -1)
            log("直播间信息已更新。")

    def login_gui(self):
        log("正在尝试登录。")
        if is_exist(self._config_.config_file) and self._config_.read_config(self._data_):
            if self.get_user_status():
                log("已从配置文件加载 Cookie，且 Cookie 有效。")
                self._get_info_from_cookies_()
                self._update_area_()
                self._update_room_data_()
                self.save_config()
                self.signals.login_success.emit()
                log("登录成功。")
                return
            else:
                log("配置文件存在但 Cookie 无效或已过期，将进行二维码登录。")
                self.qr_login_gui()
        else:
            log("配置文件不存在或读取失败，将进行二维码登录。")
            self.qr_login_gui()

    def qr_login_gui(self):
        self._stop_qr_poll_flag = False
        res = get_json(
            "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
            headers={"User-Agent": self._data_.get_user_agent()},
        )
        if not res or res.get("code") != 0:
            log("获取二维码失败。")
            return

        qr_url = res["data"]["url"]
        qr_key = res["data"]["qrcode_key"]

        qr = QRCode()
        qr.add_data(qr_url)
        qr.make(fit=True)
        img_pil = qr.make_image(fill_color="black", back_color="white")

        img_qt = ImageQt.toqpixmap(img_pil)

        pixmap = img_qt
        self.signals.qr_code_ready.emit(pixmap)

        log("请扫描二维码登录。")

        def poll_qr_status():
            status = False
            while not self._stop_qr_poll_flag and not status:
                status = self._get_qr_cookies_(qr_key)
                if status:
                    log("二维码扫描成功，登录中...")
                    self._get_info_from_cookies_()
                    self._update_area_()
                    self._update_room_data_()
                    self._data_.cookies_str = json.dumps(
                        self._data_.cookies, separators=(",", ":"), ensure_ascii=False
                    )
                    self.save_config()
                    self.signals.login_success.emit()
                    log("登录成功。")
                    self._stop_qr_poll_flag = True
                    break
                time.sleep(1)

        threading.Thread(target=poll_qr_status).start()

    def set_live_title_gui(self, title: str):
        if not self._data_.is_valid_live_title(title):
            log("非法标题，标题不得超过20字或为空。")
            return
        self._data_.title = title
        res = post_json(
            url="https://api.live.bilibili.com/room/v1/Room/update",
            headers=self._data_.get_header(),
            cookies=self._data_.cookies,
            data=self._data_.get_data_title(),
        )
        if res and res.get("code") == 0:
            if (status := res.get("data", {}).get("audit_title_status")) == 0:
                log("更改标题成功。")
            elif status == 2:
                log("更改标题成功，正在审核中。")

            if title not in self._data_.title_history:
                self._data_.title_history.insert(0, title)
                if len(self._data_.title_history) > 10:
                    self._data_.title_history = self._data_.title_history[:10]
            self.save_config()
            self.signals.title_history_updated.emit(self._data_.title_history)
        else:
            log(f"更改标题失败：{res.get('msg', '未知错误')}")
        self._update_room_data_()
        self.signals.update_info.emit()

    def set_live_area_gui(self, area_id: int):
        if not self._data_.is_valid_area_id(area_id):
            log("无效的分区ID。")
            return
        self._data_.area_id = area_id
        data = post_json(
            "https://api.live.bilibili.com/room/v1/Room/update",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_id(),
        )
        if data and data.get("code") == 0:
            parent_name, child_name = self._data_.get_area_name_by_id(self._data_.area_id)
            log(f"更改分区({parent_name}:{child_name}:{self._data_.area_id})成功！")
        else:
            log(
                f"更改分区失败：{data.get('msg', '未知错误')}"
            )
        self._update_room_data_()
        self.signals.update_info.emit()

    def get_user_status(self) -> bool:
        res = get_json(
            url="https://api.bilibili.com/x/web-interface/nav",
            headers=self._data_.get_header(),
            cookies=self._data_.cookies,
        )
        if res and res.get("code") == 0 and res.get("data") and res["data"].get("isLogin"):
            return True
        else:
            return False

    def start_live(self):
        if self._data_.live_status == 1:
            log("直播已在进行中。")
            return

        res = post_json(
            "https://api.live.bilibili.com/room/v1/Room/startLive",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_start(),
        )
        if res and res["code"] != 0:
            log(f"获取推流码失败，Cookie 可能失效，请重新获取！{res.get('msg', '未知错误')}")
        elif res:
            rtmp = res["data"]["rtmp"]
            self._data_.rtmp_addr = rtmp["addr"]
            self._data_.rtmp_code = rtmp["code"]
            log("已开播。")
            log(f"推流地址：{self._data_.rtmp_addr}")
            masked_rtmp_code = self._data_.rtmp_code
            if len(masked_rtmp_code) > 8:
                masked_rtmp_code = masked_rtmp_code[:4] + '*' * (len(masked_rtmp_code) - 8) + masked_rtmp_code[-4:]
            else:
                masked_rtmp_code = '*' * len(masked_rtmp_code)
            log(f"推流码：{masked_rtmp_code}")
            log("完整密钥请点击 '显示RTMP'。")
            self.signals.show_rtmp_info.emit(self._data_.rtmp_addr, self._data_.rtmp_code)
        self._update_room_data_()
        self.signals.update_info.emit()

    def stop_live(self):
        if self._data_.live_status != 1:
            log("当前不在直播中。")
            return

        res = post_json(
            "https://api.live.bilibili.com/room/v1/Room/stopLive",
            cookies=self._data_.cookies,
            headers=self._data_.get_header(),
            data=self._data_.get_data_stop(),
        )
        if res and res["code"] != 0:
            log(
                f"下播失败，请手动前往网页下播：https://link.bilibili.com/p/center/index#/my-room/start-live 错误：{res.get('msg', '未知错误')}"
            )
        elif res:
            log("已下播。")
        self._update_room_data_()
        self.signals.update_info.emit()

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

    def get_room_info_str(self) -> str:
        data = self._data_.room_data
        if not data:
            return "直播间信息未加载，请先登录。"

        status_text = "当前正在直播" if self.get_live_status() == 1 else "当前不在直播"

        uid = data.get('uid', '未知')
        attention = data.get('attention', '未知')
        room_id = data.get('room_id', '未知')
        title = data.get('title', '未知')
        description = data.get('description', '')
        if description.startswith('<p>') and description.endswith('</p>'):
            description = description[3:-4]

        parent_area_name = data.get('parent_area_name', '未知')
        parent_area_id = data.get('parent_area_id', '未知')
        area_name = data.get('area_name', '未知')
        area_id = data.get('area_id', '未知')
        live_time = data.get('live_time', '未知')
        online = data.get('online', '未知')

        res = [
            status_text,
            f"主播UID: {uid}      粉丝数: {attention}",
            f"直播间号: {room_id}",
            f"直播标题: {title}",
            f"直播间描述: {description}",
            f"当前分区: {parent_area_name}({parent_area_id}) {area_name}({area_id})",
            f"直播起始时间: {live_time}",
            f"当前在线观众: {online}",
        ]
        return "\n".join(res)

    def get_all_areas(self) -> dict[str, list[tuple[str, int]]]:
        all_areas = {}
        for root_area in self._data_.area:
            root_name = root_area.get("name")
            root_id = root_area.get("id")

            sub_areas = []
            for sub_area in root_area.get("list", []):
                sub_areas.append((sub_area.get("name"), sub_area.get("id")))
            all_areas[root_name] = sub_areas
        return all_areas

    def logout(self):
        self._data_ = Data()
        self._config_.area = []
        self._data_.title_history = []

        if os.path.exists(self._config_.config_file):
            try:
                os.remove(self._config_.config_file)
                log(f"配置文件 '{self._config_.config_file}' 已删除。")
            except Exception as e:
                log(f"删除配置文件失败: {e}")
        log("已成功登出。")
        self.signals.update_info.emit()
        self.signals.title_history_updated.emit([])


class BilibiliLiveApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili 直播工具")
        self.setGeometry(100, 100, 800, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.worker_signals = WorkerSignals()
        self.live = Bili_Live(config_file="config.json", signals=self.worker_signals)

        self.worker_signals.qr_code_ready.connect(self.display_qr_code)
        self.worker_signals.login_success.connect(self.on_login_success)
        self.worker_signals.update_info.connect(self.update_room_info_display)
        self.worker_signals.show_rtmp_info.connect(self.show_rtmp_dialog)
        self.worker_signals.title_history_updated.connect(self.update_title_history_combobox)

        self.font_family = QApplication.font().family()
        self.font_size = 11
        log(f"将使用系统默认字体：{self.font_family}")

        font = QFont(self.font_family, self.font_size)
        self.setFont(font)

        self.bold_font = QFont(self.font_family, self.font_size + 2, QFont.Bold)

        self.create_widgets()
        self.update_room_info_display()

        self.login_thread = threading.Thread(target=self.live.login_gui)
        self.login_thread.daemon = True
        self.login_thread.start()

        self.closeEvent = self._custom_close_event

        self.tray_icon = None
        self.create_tray_icon()

    def create_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log("系统托盘不可用。")
            return

        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor("blue"))
        painter.drawEllipse(0, 0, 16, 16)
        painter.end()
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Bilibili 直播工具")

        tray_menu = QMenu()
        restore_action = QAction("显示主窗口", self)
        restore_action.triggered.connect(self.showNormal)
        tray_menu.addAction(restore_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._handle_tray_quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and self.live.get_live_status() == 1:
                self.hide()
                if self.tray_icon:
                    self.tray_icon.show()
                    self.tray_icon.showMessage(
                        "Bilibili 直播工具",
                        "程序已最小化到系统托盘，直播仍在进行中。",
                        QSystemTrayIcon.Information,
                        2000
                    )
            elif event.oldState() == Qt.WindowMinimized and self.windowState() == Qt.WindowNoState:
                if self.tray_icon:
                    self.tray_icon.hide()
        super().changeEvent(event)

    def create_widgets(self):
        top_frame = QWidget()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)

        button_column_layout = QVBoxLayout()
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.start_login)
        button_column_layout.addWidget(self.login_button)

        self.logout_button = QPushButton("登出")
        self.logout_button.clicked.connect(self.start_logout)
        button_column_layout.addWidget(self.logout_button)
        top_layout.addLayout(button_column_layout)

        self.room_info_label = QLabel("直播间信息加载中...")
        self.room_info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.room_info_label.setWordWrap(True)
        top_layout.addWidget(self.room_info_label, 1)

        self.status_light_label = QLabel()
        self.status_light_label.setFixedSize(20, 20)
        self.status_light_label.setStyleSheet("border-radius: 10px; background-color: gray;")
        top_layout.addWidget(self.status_light_label)

        self.main_layout.addWidget(top_frame)

        self.qr_frame = QWidget()
        qr_layout = QVBoxLayout(self.qr_frame)
        qr_label_title = QLabel("二维码扫描")
        qr_label_title.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(qr_label_title)
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_label)
        self.main_layout.addWidget(self.qr_frame)
        self.qr_frame.hide()

        action_frame = QWidget()
        action_layout = QGridLayout(action_frame)

        action_layout.addWidget(QLabel("直播标题:"), 0, 0)
        self.title_combobox = QComboBox()
        self.title_combobox.setEditable(True)
        self.title_combobox.setPlaceholderText("请输入直播标题 (不超过20字)")
        action_layout.addWidget(self.title_combobox, 0, 1)
        self.set_title_button = QPushButton("设置标题")
        self.set_title_button.clicked.connect(self.set_title)
        action_layout.addWidget(self.set_title_button, 0, 2)

        action_layout.addWidget(QLabel("主分区:"), 1, 0)
        self.main_area_combobox = QComboBox()
        self.main_area_combobox.currentIndexChanged.connect(self.on_main_area_selected)
        action_layout.addWidget(self.main_area_combobox, 1, 1)

        action_layout.addWidget(QLabel("子分区:"), 2, 0)
        self.sub_area_combobox = QComboBox()
        action_layout.addWidget(self.sub_area_combobox, 2, 1)
        self.set_area_button = QPushButton("设置分区")
        self.set_area_button.clicked.connect(self.set_area)
        action_layout.addWidget(self.set_area_button, 2, 2)

        self.start_live_button = QPushButton("开始直播")
        self.start_live_button.clicked.connect(self.start_live)
        action_layout.addWidget(self.start_live_button, 3, 0)

        self.stop_live_button = QPushButton("停止直播")
        self.stop_live_button.clicked.connect(self.stop_live)
        action_layout.addWidget(self.stop_live_button, 3, 1)

        self.rtmp_button = QPushButton("显示RTMP")
        self.rtmp_button.clicked.connect(
            lambda: self.worker_signals.show_rtmp_info.emit(self.live.get_rtmp()[0], self.live.get_rtmp()[1]))
        action_layout.addWidget(self.rtmp_button, 3, 2)

        action_layout.setColumnStretch(1, 1)
        self.main_layout.addWidget(action_frame)

        log_frame = QWidget()
        log_layout = QVBoxLayout(log_frame)
        log_label_title = QLabel("日志")
        log_label_title.setAlignment(Qt.AlignLeft)
        log_layout.addWidget(log_label_title)
        self.log_text = LogTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont(self.font_family, self.font_size))
        log_layout.addWidget(self.log_text)
        self.main_layout.addWidget(log_frame, 1)

        global gui_log_text_widget
        gui_log_text_widget = self.log_text

        for frame in [self.qr_frame, action_frame, log_frame]:
            for child in frame.children():
                if isinstance(child, QLabel) and child.text() in ["二维码扫描", "直播操作", "日志"]:
                    child.setFont(self.bold_font)

    def display_qr_code(self, pixmap):
        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.qr_label.setPixmap(scaled_pixmap)
        self.qr_frame.show()

    def update_room_info_display(self):
        info_text = self.live.get_room_info_str()
        self.room_info_label.setText(info_text)

        live_status = self.live.get_live_status()
        if live_status == 1:
            self.status_light_label.setStyleSheet("border-radius: 10px; background-color: green;")
        elif live_status == 0 or live_status == 2:
            self.status_light_label.setStyleSheet("border-radius: 10px; background-color: red;")
        else:
            self.status_light_label.setStyleSheet("border-radius: 10px; background-color: gray;")

    def update_area_comboboxes(self):
        all_areas = self.live.get_all_areas()
        main_area_names = list(all_areas.keys())
        self.main_area_combobox.clear()
        self.main_area_combobox.addItems(main_area_names)

        self.sub_area_combobox.clear()

        current_parent_name, current_child_name = self.live._data_.get_area_name_by_id(self.live._data_.area_id)
        if current_parent_name in main_area_names:
            self.main_area_combobox.setCurrentText(current_parent_name)
            self.on_main_area_selected(self.main_area_combobox.currentIndex())
            if current_child_name:
                current_sub_areas = [name for name, _id in all_areas.get(current_parent_name, [])]
                if current_child_name in current_sub_areas:
                    self.sub_area_combobox.setCurrentText(current_child_name)
                else:
                    log(f"当前子分区 '{current_child_name}' 不在列表中。")

        self.title_combobox.setEditText(self.live._data_.title)

    def update_title_history_combobox(self, history_list):
        current_text = self.title_combobox.currentText()
        self.title_combobox.clear()
        self.title_combobox.addItems(history_list)
        if current_text and current_text not in history_list:
            self.title_combobox.insertItem(0, current_text)
        self.title_combobox.setEditText(current_text)

    def on_main_area_selected(self, index):
        selected_main_area = self.main_area_combobox.currentText()
        all_areas = self.live.get_all_areas()
        sub_areas_data = all_areas.get(selected_main_area, [])
        sub_area_names = [name for name, _id in sub_areas_data]
        self.sub_area_combobox.clear()
        self.sub_area_combobox.addItems(sub_area_names)

    def on_login_success(self):
        self.update_room_info_display()
        self.update_area_comboboxes()
        self.qr_label.clear()
        self.qr_frame.hide()
        self.update_title_history_combobox(self.live._data_.title_history)

    def run_in_thread(self, func, *args):
        def wrapper():
            try:
                func(*args)
            except Exception as e:
                log(f"操作失败：{e}")
            finally:
                self.worker_signals.update_info.emit()

        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()

    def start_login(self):
        self.qr_frame.show()
        self.run_in_thread(self.live.login_gui)

    def start_logout(self):
        reply = QMessageBox.question(self, "确认登出", "您确定要登出吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.run_in_thread(self.live.logout)
            self.reset_gui_for_logout()
        else:
            pass

    def reset_gui_for_logout(self):
        self.qr_label.clear()
        self.qr_frame.show()

        self.room_info_label.setText("直播间信息未加载，请先登录。")

        self.title_combobox.clear()
        self.title_combobox.setEditText("")

        self.main_area_combobox.clear()
        self.main_area_combobox.setPlaceholderText("选择主分区")
        self.sub_area_combobox.clear()
        self.sub_area_combobox.setPlaceholderText("选择子分区")

        self.status_light_label.setStyleSheet("border-radius: 10px; background-color: gray;")

    def set_title(self):
        new_title = self.title_combobox.currentText()
        self.run_in_thread(self.live.set_live_title_gui, new_title)

    def set_area(self):
        selected_main_area_name = self.main_area_combobox.currentText()
        selected_sub_area_name = self.sub_area_combobox.currentText()

        if not selected_main_area_name or not selected_sub_area_name:
            QMessageBox.warning(self, "警告", "请选择主分区和子分区。")
            return

        all_areas = self.live.get_all_areas()
        sub_areas_data = all_areas.get(selected_main_area_name, [])

        selected_area_id = 0
        for name, _id in sub_areas_data:
            if name == selected_sub_area_name:
                selected_area_id = _id
                break

        if selected_area_id:
            self.run_in_thread(self.live.set_live_area_gui, selected_area_id)
        else:
            QMessageBox.warning(self, "警告", "无法找到对应的分区ID。")

    def start_live(self):
        self.run_in_thread(self.live.start_live)

    def stop_live(self):
        self.run_in_thread(self.live.stop_live)

    def _custom_close_event(self, event):
        if self.live.get_live_status() == 1:
            reply = QMessageBox.question(self, "确认退出", "直播正在进行中。您想在退出前停止它吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                threading.Thread(target=self.live.stop_live).start()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _handle_tray_quit(self):
        if self.live.get_live_status() == 1:
            reply = QMessageBox.question(self, "确认退出", "直播正在进行中。您想在退出前停止它吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                threading.Thread(target=self.live.stop_live).start()
                QApplication.quit()
            else:
                pass
        else:
            QApplication.quit()

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        log(f"已复制到剪贴板：{text}")
        QMessageBox.information(self, "已复制", "文本已复制到剪贴板！")

    def show_rtmp_dialog(self, rtmp_addr, rtmp_code):
        if rtmp_addr and rtmp_code:
            rtmp_dialog = QDialog(self)
            rtmp_dialog.setWindowTitle("推流信息")
            rtmp_dialog.setFixedSize(500, 250)

            layout = QVBoxLayout(rtmp_dialog)

            addr_label = QLabel("推流地址:")
            addr_entry = QLineEdit(rtmp_addr)
            addr_entry.setReadOnly(True)
            copy_addr_button = QPushButton("复制地址")
            copy_addr_button.clicked.connect(lambda: self.copy_to_clipboard(rtmp_addr))

            layout.addWidget(addr_label)
            layout.addWidget(addr_entry)
            layout.addWidget(copy_addr_button)

            code_label = QLabel("推流码:")
            code_entry = QLineEdit(rtmp_code)
            code_entry.setReadOnly(True)
            copy_code_button = QPushButton("复制推流码")
            copy_code_button.clicked.connect(lambda: self.copy_to_clipboard(rtmp_code))

            layout.addWidget(code_label)
            layout.addWidget(code_entry)
            layout.addWidget(copy_code_button)

            close_button = QPushButton("关闭")
            close_button.clicked.connect(rtmp_dialog.accept)
            layout.addWidget(close_button)

            rtmp_dialog.exec_()
        else:
            QMessageBox.warning(self, "警告", "未获取到推流信息，请先开始直播。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_family = QApplication.font().family()
    font_size = 11
    log(f"将使用系统默认字体：{font_family}")

    font = QFont(font_family, font_size)
    app.setFont(font)

    window = BilibiliLiveApp()
    window.show()
    sys.exit(app.exec_())

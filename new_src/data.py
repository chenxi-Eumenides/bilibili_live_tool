from dataclasses import dataclass, field

from .constant import TITLE_MAX_CHAR
from .lib import RES, RES_STATUS, Fail


def gen_list():
    return []


def gen_dict():
    return {}


@dataclass
class Area:
    root = None
    area = None

    root_name = None
    root_pinyin = None
    root_py = None

    area_name = None
    area_pinyin = None
    area_py = None

    area_child = None

    @classmethod
    def init(cls, areas):
        cls.root = areas["root"]
        cls.area = areas["area"]

        cls.root_name = {}
        cls.root_pinyin = {}
        cls.root_py = {}
        cls.area_child = {}
        cls.area_name = {}
        cls.area_pinyin = {}
        cls.area_py = {}
        for root_id in cls.root:
            cls.root_name.update({cls.root[root_id]["name"]: int(root_id)})
            cls.root_pinyin.update({cls.root[root_id]["pinyin"]: int(root_id)})
            cls.root_py.update({cls.root[root_id]["py"]: int(root_id)})
            cls.area_child.update({str(cls.root[root_id]["id"]): {}})
            cls.area_name.update({str(cls.root[root_id]["id"]): {}})
            cls.area_pinyin.update({str(cls.root[root_id]["id"]): {}})
            cls.area_py.update({str(cls.root[root_id]["id"]): {}})

        for area_id in cls.area:
            cls.area_child[str(cls.area[area_id]["parent_id"])].update(
                {area_id: cls.area[area_id]}
            )
            cls.area_name[str(cls.area[area_id]["parent_id"])].update(
                {cls.area[area_id]: area_id}
            )
            cls.area_name[str(cls.area[area_id]["parent_id"])].update(
                {area_id: cls.area[area_id]}
            )


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


def get_area_name_by_id(areas: dict, id: int) -> tuple[str, str]:
    """
    根据分区id获取分区名

    :param id: 分区id
    :return: DATA: {name, parent_name}
    """
    area: dict = areas.get("area")
    if area and str(id) in area:
        data = area.get(str(id))
        return RES(
            RES_STATUS.OK,
            DATA={
                "name": data.get("name"),
                "parent_name": data.get("parent_name"),
            },
        )
    return RES(RES_STATUS.FAIL, Fail.NoResult)


def get_area_name_list(areas: dict, root_id: int = 0) -> RES:
    """
    获取分区主题下的所有分区名字

    :param root_id: 分区主题id，默认为0，即返回主分区名字
    :return: DATA: {name_list}
    """
    if root_id == 0:
        name_list = [areas["root"][str(root_id)]["name"] for root_id in areas["root"]]
    elif str(root_id) in areas["root"]:
        name_list = areas["root"][str(root_id)].get("child_name")
    else:
        return RES(RES_STATUS.FAIL, Fail.NoResult)
    return RES(
        RES_STATUS.OK,
        DATA={"name_list": name_list},
    )


def get_area_id_by_name(areas: dict, name: str, area_id: int = 0) -> RES:
    """
    通过分区名字获取对应的id

    :param name: 搜索的分区名字，可以是拼音
    :param area_id: 搜索分区所在的主分区id（0为只获取主分区名，-1为从所有分区中搜索）
    :return: DATA: {name, id}
    """
    if name == "":
        return RES(RES_STATUS.FAIL, REASON=Fail.ArgError)
    if area_id == -1:
        # 从所有分区中搜索
        for area in areas.get("area").values():
            if name in area["name"]:
                return RES(RES_STATUS.OK, DATA={"name": area["name"], "id": area["id"]})
            elif name in area["pinyin"]:
                return RES(RES_STATUS.OK, DATA={"name": area["name"], "id": area["id"]})
            elif name in area["py"]:
                return RES(RES_STATUS.OK, DATA={"name": area["name"], "id": area["id"]})
    elif area_id == 0:
        # 从主分区中搜索
        for root in areas.get("root").values():
            if name in root["name"]:
                return RES(RES_STATUS.OK, DATA={"name": root["name"], "id": root["id"]})
            elif name in root["pinyin"]:
                return RES(RES_STATUS.OK, DATA={"name": root["name"], "id": root["id"]})
            elif name in root["py"]:
                return RES(RES_STATUS.OK, DATA={"name": root["name"], "id": root["id"]})
    elif area_id > 0 and str(area_id) in areas.get("root"):
        # 搜索特定分区
        if str(area_id) in areas.get("root"):
            area_id_list = areas.get("root").get(str(area_id)).get("list")
            for area_id in area_id_list:
                area = areas.get("area").get(str(area_id))
                if name in area["name"]:
                    return RES(
                        RES_STATUS.OK, DATA={"name": area["name"], "id": area["id"]}
                    )
                elif name in area["pinyin"]:
                    return RES(
                        RES_STATUS.OK, DATA={"name": area["name"], "id": area["id"]}
                    )
                elif name in area["py"]:
                    return RES(
                        RES_STATUS.OK, DATA={"name": area["name"], "id": area["id"]}
                    )
    return RES(RES_STATUS.FAIL, REASON=Fail.NoResult)


def is_valid_area_id(areas: dict, id: int) -> RES:
    """
    检查是否是合法的分区id

    :param id: 分区id
    :return: DATA:{id, name, pinyin, py, parent_id, parent_name}
    """
    area: dict = areas.get("area")
    if area and area.get(str(id)):
        return RES(RES_STATUS.OK, DATA=area.get(str(id)))
    else:
        return RES(RES_STATUS.FAIL, REASON=Fail.ArgError)


def is_valid_live_title(title: str) -> RES:
    """
    是否是合法的直播标题

    :param title: 标题
    :return: DATA: title
    """
    if title is None:
        return RES(RES_STATUS.FAIL, REASON=Fail.ArgError)
    if len(title) > TITLE_MAX_CHAR or len(title) <= 0:
        return RES(RES_STATUS.FAIL, REASON=Fail.ArgError)
    return RES(RES_STATUS.OK, DATA=title)

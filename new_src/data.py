from dataclasses import dataclass, field

from .constant import TITLE_MAX_CHAR


def gen_list():
    return []


def gen_dict():
    return {}


@dataclass
class Area:
    pass


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


# broken
def get_area_name_by_id(area: dict, id: int) -> tuple[str, str]:
    """
    根据分区id获取分区名

    :param id: 分区id
    :return: (主分区名, 子分区名)
    """
    if id <= 0 or id >= 1000:
        return None
    for data in area:
        for part in data.get("list"):
            if id == part.get("id"):
                return data.get("name"), part.get("name")
    return None


# broken
def get_area_name(area: dict, root_id: int = 0) -> list[str]:
    """
    获取分区主题下的所有分区名字

    :param root_id: 分区主题id，默认为0，即返回主分区名字
    :return: 返回特定主题的所有分区的名字
    """
    results = []
    for data in area:
        if root_id:
            if data.get("id") == root_id:
                for part in data.get("list"):
                    results.append(part.get("name"))
                break
        else:
            results.append(data.get("name"))
    return results


# broken
def get_area_id_by_name(area: dict, name: str, area_id: int = 0) -> int:
    """
    获取分区名字对应的id

    :param name: 搜索的分区名字
    :param area_id: 搜索分区所在的主分区id（0为只获取主分区，-1为从所有分区中搜索）
    :return: 分区id
    """
    if name == "":
        return 0
    for part in area:
        if area_id > 0:
            # 指定子分区id
            if area_id == part.get("id"):
                for p in part.get("list"):
                    if name in p.get("name"):
                        return p.get("id")
        elif area_id == 0:
            # 指定主分区
            if name in part.get("name"):
                return part.get("id")
        elif area_id == -1:
            # 指定所有分区
            for p in part.get("list"):
                if name in p.get("name"):
                    return p.get("id")
    return 0


# broken
def is_valid_area_id(area: dict[str, dict], id: int) -> bool:
    """
    检查是否是合法的分区id

    :param id: 分区id
    :return: 是否合法
    """
    if id <= 0 or id >= 1000:
        return False
    for data in area:
        for part in data.get("list"):
            if id == part.get("id"):
                return True
    return False


def is_valid_live_title(title: str) -> bool:
    """
    是否是合法的直播标题

    :param title: 标题
    :return: 是否合法
    """
    if title is None:
        return False
    if len(title) > TITLE_MAX_CHAR or len(title) <= 0:
        return False
    return True

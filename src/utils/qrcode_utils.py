"""二维码生成工具函数."""

import qrcode


def build_qr_matrix(qr_url: str) -> list:
    """生成二维码矩阵.

    Args:
        qr_url: 二维码 URL

    Returns:
        bool 矩阵, True 表示黑色模块
    """
    qr = qrcode.QRCode(
        version=6,
        error_correction=1,
        box_size=1,
        border=0,
    )
    qr.add_data(qr_url)
    qr.make(fit=False)
    return qr.get_matrix()


def build_qr_lines(matrix: list, compat: bool) -> list[str]:
    """从二维码矩阵生成字符画行列表.

    Args:
        matrix: 二维码矩阵
        compat: True 使用全块字符 (兼容模式), False 使用半块字符 (现代模式)

    Returns:
        字符画行列表, 每行一个字符串
    """
    if compat:
        chars = {True: "██", False: "  "}
        lines = []
        for row in range(len(matrix)):
            line = ""
            for col in range(len(matrix)):
                line += chars[matrix[row][col]]
            lines.append(line)
    else:
        chars = {
            (False, False): " ",
            (True, False): "▀",
            (False, True): "▄",
            (True, True): "█",
        }
        size = len(matrix)
        lines = []
        for row in range(0, size, 2):
            line = ""
            for col in range(size):
                upper = matrix[row][col]
                lower = matrix[row + 1][col] if row + 1 < size else False
                line += chars[(upper, lower)]
            lines.append(line)
    return lines

"""清理工具模块

处理程序退出时的资源清理工作。
"""

import logging
from pathlib import Path

from .constants import QR_IMG, QR_FACE_IMG

logger = logging.getLogger(__name__)


def cleanup_qr_files() -> None:
    """清理二维码图片文件
    
    在程序退出、登录完成或出错时调用，删除临时生成的二维码图片。
    """
    files_to_cleanup = [QR_IMG, QR_FACE_IMG]
    
    for file_path in files_to_cleanup:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"已清理文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理文件失败 {file_path}: {e}")


def cleanup_file(file_path: Path) -> bool:
    """清理指定文件
    
    Args:
        file_path: 要删除的文件路径
        
    Returns:
        bool: 是否成功删除（文件不存在也返回True）
    """
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return True  # 文件不存在也算成功
    except Exception as e:
        logger.warning(f"清理文件失败 {file_path}: {e}")
        return False
"""清理工具模块

处理程序退出时的资源清理工作。
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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
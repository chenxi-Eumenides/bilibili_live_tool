"""
pyinstaller打包入口文件
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cli.main import main

if __name__ == "__main__":
    main()

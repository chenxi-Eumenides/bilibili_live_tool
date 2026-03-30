uv sync

uv run --dev pyinstaller -n "bili-live-tool" -c -i .\src\static\bili-icon.ico --onefile --clean .\cli\main.py
uv run --dev pyinstaller -n "bili-live-tool-tui" -c -i .\src\static\bili-icon.ico --onefile --clean tui/app/main.py
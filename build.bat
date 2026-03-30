@echo off
uv sync

printf "\n========== packaging CLI version ==========\n\n"
uv run --dev pyinstaller ^
    -n "bili-live-tool" ^
    -c -i .\src\static\bili-icon.ico ^
    --collect-submodules cli ^
    --onefile --clean ^
    .\cli\build.py

printf "\n========== packaging TUI version ==========\n\n"
uv run --dev pyinstaller ^
    -n "bili-live-tool-tui" ^
    -c -i .\src\static\bili-icon.ico ^
    --collect-submodules tui ^
    --add-data=".\tui\ui\styles;.\tui\ui\styles" ^
    --onefile --clean ^
    .\tui\build.py

printf "\n=================== Done ===================\n"
@echo off
uv sync

printf "\n========== packaging CLI version ==========\n\n"
uv run --group cli --group build pyinstaller ^
    -n "bili-live-tool" ^
    -c -i .\src\static\bili-icon.ico ^
    --collect-submodules src ^
    --onefile --clean ^
    .\src\build.py

printf "\n=================== Done ===================\n"

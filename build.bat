@echo off
uv sync

printf "\n========== packaging exe ==========\n\n"
uv run --group build pyinstaller ^
    -n "bili-live-tool" ^
    -c -i .\src\static\bili-icon.ico ^
    --collect-submodules src ^
    --add-data=".\src\ui\styles;.\src\ui\styles" ^
    --onefile --clean ^
    .\src\build.py

printf "\n=================== Done ===================\n"

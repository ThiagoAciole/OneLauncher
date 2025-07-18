@echo off
echo -------------------------------
echo Compilando OneLauncher...
echo -------------------------------

REM Executa o PyInstaller com as opções desejadas
pyinstaller src/main.py ^
--onefile ^
--noconsole ^
--icon=src/assets/icone.ico ^
--name=OneLauncher ^
--distpath=. ^
--add-data "src/assets;assets" ^
--add-data "game;game"

REM Remove o arquivo .spec após o build
if exist OneLauncher.spec (
    del OneLauncher.spec
    echo Arquivo OneLauncher.spec removido.
)

echo -------------------------------
echo Build finalizado!
echo Arquivo gerado: OneLauncher.exe
echo -------------------------------

pause

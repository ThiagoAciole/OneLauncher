@echo off
echo -------------------------------
echo Compilando OneLauncher...
echo -------------------------------

REM Executa o PyInstaller com as opções desejadas
pyinstaller launcher.py --onefile --noconsole --icon=game/assets/icone.ico --name=OneLauncher --distpath=.

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

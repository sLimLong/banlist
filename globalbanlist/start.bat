@echo off
REM Запуск скрипта проверки глобального бан-листа
chcp 65001 >nul

REM Путь к Python (если он в PATH, можно просто python)
set PYTHON=py

REM Путь к скрипту
set SCRIPT=global_ban_to_xml.py

echo Запуск проверки глобального бан-листа...
%PYTHON% %SCRIPT%

echo.
echo Работа завершена. Нажмите любую клавишу для выхода.
pause

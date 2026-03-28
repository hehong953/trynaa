@echo off
title 
echo 正在啟動...

:: 1. 切換到當前檔案所在的目錄
cd /d "%~dp0"

:: 2. 檢查虛擬環境是否存在並啟動
if exist .venv\Scripts\activate (
    echo 正在啟動虛擬環境...
    call .venv\Scripts\activate
) else (
    echo [警告] 找不到 .venv 虛擬環境，將嘗試使用系統 Python。
)

:: 3. 檢查資料庫是否存在
if not exist daijirin2.db (
    echo [錯誤] 找不到 daijirin2.db！
    echo 請先執行 python init_db.py 建立資料庫。
    pause
    exit
)

:: 4. 啟動 Uvicorn 伺服器
echo ------------------------------------------

uvicorn app:app --host 127.0.0.1 --port 8080

pause
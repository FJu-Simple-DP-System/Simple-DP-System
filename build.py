import PyInstaller.__main__
import customtkinter
import os
import sys

# 1. 取得 CustomTkinter 函式庫的路徑 (這是最關鍵的一步)
ctk_path = os.path.dirname(customtkinter.__file__)

# 2. 定義分隔符號 (Windows用 ; Mac/Linux用 :)
separator = ';' if sys.platform.startswith('win') else ':'

# 3. 執行 PyInstaller
PyInstaller.__main__.run([
    'main.py',                        # 您的程式入口檔案 (請確認檔名是否為 main.py)
    '--name=SimpleDPSystem',          # 生成的 exe 名稱
    #'--noconsole',                    # 隱藏黑色終端機視窗 (除錯時可先拿掉這行)
    '--onefile',                      # 打包成單一執行檔 (啟動會慢一點，但方便)
    '--windowed',                     # 使用視窗模式執行
    '--clean',                        # 清除快取
    
    # 加入 CustomTkinter 的資源檔 (格式: 來源路徑;目標路徑)
    f'--add-data={ctk_path}{separator}customtkinter',
    
    # 如果您有其他的 icon，可以取消下面這行的註解
    # '--icon=my_icon.ico',
])
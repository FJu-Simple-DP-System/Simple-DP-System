import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
import os
import pandas as pd

# 引入所有元件
from src.view.components import FileDropFrame
from src.view.preview_table import DataPreviewTable
from src.view.settings_panel import SettingsPanel

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("簡單差分隱私系統 - V0.2")
        self.geometry("1100x700")

        # --- Grid 佈局設定 ---
        # column 0: 設定欄 (固定寬度)
        # column 1: 主要內容區 (自動伸縮)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. 左側設定面板 (Sidebar) ---
        self.settings_panel = SettingsPanel(self, width=250, corner_radius=0)
        self.settings_panel.grid(row=0, column=0, sticky="nsew")

        # --- 2. 右側主要內容區 (Main Content) ---
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # 右側內部佈局設定：
        # row 0: 標題
        # row 1: 拖曳區
        # row 2: 預覽標題
        # row 3: 表格 (權重設為 1，讓它佔據最大空間)
        # row 4: 狀態列 (放在最下面)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(3, weight=1) # 【關鍵修改】讓表格區負責伸縮

        # 標題 (Row 0)
        self.title_label = ctk.CTkLabel(self.right_frame, text="資料導入與預覽", font=("Arial", 24, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # 拖曳上傳區 (Row 1)
        self.drop_area = FileDropFrame(self.right_frame, width=700, height=120, on_drop_callback=self.handle_file_upload)
        self.drop_area.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        # 資料表格標題 (Row 2) - 預設隱藏
        self.preview_label = ctk.CTkLabel(self.right_frame, text="資料預覽 (前 15 筆)", font=("Arial", 16, "bold"))
        
        # 資料表格本體 (Row 3) - 預設隱藏
        self.table_frame = DataPreviewTable(self.right_frame)
        
        # 狀態列 (Row 4) - 【關鍵修改】預設放在 Row 4
        self.status_label = ctk.CTkLabel(self.right_frame, text="請上傳檔案以開始...", text_color="gray")
        self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))

    def handle_file_upload(self, file_path):
        """處理檔案上傳"""
        print(f"收到檔案：{file_path}")
        
        if file_path.lower().endswith(('.csv', '.xlsx')):
            file_name = os.path.basename(file_path)
            
            # 更新表格資料
            success, message = self.table_frame.update_data(file_path)

            if success:
                self.status_label.configure(text=f"已載入：{file_name} | {message}", text_color="green")
                
                # 顯示表格相關元件
                # Row 2: 顯示「資料預覽」文字
                self.preview_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
                
                # Row 3: 顯示表格，並填滿空間
                self.table_frame.grid(row=3, column=0, sticky="nsew")
                
                # Row 4: 確保狀態列在最下方 (雖已在 __init__ 設定，這裡確保它不會跑掉)
                self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))

                # 更新左側選單
                try:
                    if file_path.endswith(".csv"):
                        # 只讀取 Header 以節省效能
                        cols = list(pd.read_csv(file_path, nrows=0).columns)
                    else:
                        cols = list(pd.read_excel(file_path, nrows=0).columns)
                    
                    self.settings_panel.update_columns(cols)
                except Exception as e:
                    print(f"欄位讀取失敗: {e}")

            else:
                self.status_label.configure(text=message, text_color="red")
        else:
            self.status_label.configure(text="錯誤：僅支援 CSV 或 XLSX 格式", text_color="red")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
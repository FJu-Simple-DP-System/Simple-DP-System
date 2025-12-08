import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
import os
import pandas as pd

# 引入所有元件 (包含剛剛寫的 StartScreen)
from src.view.components import FileDropFrame
from src.view.preview_table import DataPreviewTable
from src.view.settings_panel import SettingsPanel
from src.view.result_panel import ResultPanel
from src.view.start_screen import StartScreen  # 【新增】

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("簡單差分隱私系統 - V0.3")
        self.geometry("1100x800")
        
        # 【新增】應用程式狀態管理
        # 啟動時，先顯示 StartScreen
        self.show_start_screen()

    def show_start_screen(self):
        """顯示開始畫面"""
        self.start_screen = StartScreen(self, on_start_callback=self.enter_main_app)
        # 使用 pack fill 佔滿全螢幕
        self.start_screen.pack(fill="both", expand=True)

    def enter_main_app(self):
        """
        從開始畫面進入主程式
        1. 銷毀 StartScreen
        2. 建構並顯示主介面 (原本 __init__ 裡的程式碼移到這裡)
        """
        # 移除開始畫面
        self.start_screen.destroy()
        
        # --- 初始化主介面 (原本的邏輯) ---
        self.init_main_interface()

    def init_main_interface(self):
        """建構主應用程式介面"""
        # --- Grid 佈局設定 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. 左側設定面板 ---
        self.settings_panel = SettingsPanel(self, width=250, corner_radius=0)
        self.settings_panel.grid(row=0, column=0, sticky="nsew")

        # --- 2. 右側主要內容區 ---
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # 右側內部佈局
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(4, weight=1) # 表格區伸縮

        # Row 0: 標題
        self.title_label = ctk.CTkLabel(self.right_frame, text="資料導入與預覽", font=("Arial", 24, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Row 1: 拖曳上傳區
        self.drop_area = FileDropFrame(self.right_frame, width=700, height=100, on_drop_callback=self.handle_file_upload)
        self.drop_area.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        # Row 2: 結果展示區 (Result Panel)
        self.result_panel = ResultPanel(self.right_frame)
        self.result_panel.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        
        # Row 3: 預覽標題 (預設隱藏)
        self.preview_label = ctk.CTkLabel(self.right_frame, text="資料預覽 (前 15 筆)", font=("Arial", 16, "bold"))

        # Row 4: 表格 (預設隱藏)
        self.table_frame = DataPreviewTable(self.right_frame)
        
        # Row 5: 狀態列
        self.status_label = ctk.CTkLabel(self.right_frame, text="請上傳檔案以開始...", text_color="gray")
        self.status_label.grid(row=5, column=0, sticky="ew", pady=(10, 0))

        # 綁定測試按鈕 (模擬)
        self.settings_panel.btn_run.configure(command=self.mock_run_analysis)

    def handle_file_upload(self, file_path):
        """處理檔案上傳"""
        # ... (這部分程式碼維持不變) ...
        print(f"收到檔案：{file_path}")
        if file_path.lower().endswith(('.csv', '.xlsx')):
            file_name = os.path.basename(file_path)
            success, message = self.table_frame.update_data(file_path)

            if success:
                self.status_label.configure(text=f"已載入：{file_name} | {message}", text_color="green")
                self.preview_label.grid(row=3, column=0, sticky="w", pady=(0, 5))
                self.table_frame.grid(row=4, column=0, sticky="nsew")
                
                try:
                    if file_path.endswith(".csv"):
                        cols = list(pd.read_csv(file_path, nrows=0).columns)
                    else:
                        cols = list(pd.read_excel(file_path, nrows=0).columns)
                    self.settings_panel.update_columns(cols)
                except Exception:
                    pass
            else:
                self.status_label.configure(text=message, text_color="red")
        else:
            self.status_label.configure(text="錯誤：僅支援 CSV 或 XLSX 格式", text_color="red")

    def mock_run_analysis(self):
        """模擬運算"""
        self.result_panel.show_loading()
        self.after(1000, lambda: self.result_panel.show_result_value(
            "差分隱私運算完成！ (模擬)\nEpsilon: 1.0\nResult: 50,024.5"
        ))

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
import os
import pandas as pd

# 引入所有元件
from src.view.components import FileDropFrame
from src.view.preview import DataPreviewTable
from src.view.settings import SettingsPanel
from src.view.start import StartScreen
from src.view.results import ResultPanel

from src.core.elements import dp_settings
from src.core.engine import run_dp_from_settings

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("簡單差分隱私系統 - V0.2")
        self.geometry("1100x700")

        # show start screen
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
        self.init_configs()

    def init_configs(self):
        self.current_df = None  # 暫存目前載入的完整 DataFrame

        # --- Grid 佈局設定 ---
        # column 0: 設定欄 (固定寬度)
        # column 1: 主要內容區 (自動伸縮)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. 左側設定面板 (Sidebar) ---
        self.settings_panel = SettingsPanel(self, width=250, corner_radius=0, on_run=self.execute_dp)
        self.settings_panel.grid(row=0, column=0, sticky="nsew")

        # --- 2. 右側主要內容區 (Main Content) ---
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)


        # 右側內部佈局設定：
        # row 0: 標題
        # row 1: 拖曳區
        # row 2: 預覽標題
        # row 3: 表格 (權重設為 1，讓它佔據最大空間)
        # row 4: 狀態列
        # row 5: 運算結果 ResultPanel
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(3, weight=1)  # 讓表格區伸縮

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

        # 狀態列 (Row 4)
        self.status_label = ctk.CTkLabel(self.right_frame, text="請上傳檔案以開始...", text_color="gray")
        self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        # 運算結果面板 (Row 5)
        self.result_panel = ResultPanel(self.right_frame)
        self.result_panel.grid(row=5, column=0, sticky="nsew", pady=(10, 0))

    def handle_file_upload(self, file_path):
        """處理檔案上傳"""
        print(f"收到檔案：{file_path}")

        # 每次載入新檔案時，重置結果區
        if hasattr(self, "result_panel"):
            self.result_panel.reset()

        if file_path.lower().endswith(('.csv', '.xlsx')):
            file_name = os.path.basename(file_path)

            # 讀取完整資料，存起來給差分隱私運算用
            try:
                if file_path.endswith(".csv"):
                    self.current_df = pd.read_csv(file_path)
                else:
                    self.current_df = pd.read_excel(file_path)
            except Exception as e:
                self.status_label.configure(text=f"讀取檔案失敗：{e}", text_color="red")
                return

            # 更新表格資料（預覽）
            success, message = self.table_frame.update_data(file_path)

            if success:
                self.status_label.configure(text=f"已載入：{file_name} | {message}", text_color="green")

                # 顯示表格相關元件
                # Row 2: 顯示「資料預覽」文字
                self.preview_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

                # Row 3: 顯示表格，並填滿空間
                self.table_frame.grid(row=3, column=0, sticky="nsew")

                # Row 4: 確保狀態列在最下方
                self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))

                # 更新左側欄位選單
                try:
                    if file_path.endswith(".csv"):
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

    def execute_dp(self):
        """按下『執行差分隱私運算』時執行的邏輯"""
        # 確認有資料
        if self.current_df is None:
            self.status_label.configure(text="請先上傳資料檔案再執行差分隱私運算", text_color="red")
            return

        # 顯示「運算中」狀態
        if hasattr(self, "result_panel"):
            self.result_panel.show_loading()

        # 呼叫 DP 引擎
        result = run_dp_from_settings(self.current_df)

        if not result["ok"]:
            # 發生錯誤：狀態列顯示錯誤，結果區重置
            self.status_label.configure(text=result["message"], text_color="red")
            if hasattr(self, "result_panel"):
                self.result_panel.reset()
            return

        payload = result["result"]
        query = payload.get("query")

        # 組合顯示用文字
        base_info = (
            f"查詢類型：{query}\n"
            f"ε (epsilon)：{payload.get('epsilon')}\n"
            f"機制 (mechanism)：{payload.get('mechanism')}\n"
            f"欄位 (column)：{payload.get('column')}\n"
            f"資料邊界 (bounds)：{payload.get('bounds')}\n"
        )

        # 標量統計：mean / sum / count
        if query in ("mean", "sum", "count"):
            value = payload.get("value")
            text = base_info + f"\n差分隱私後 {query} ：{value:.4f}"
            # 狀態列給一個簡短版本
            # self.status_label.configure(
            #     text=f"DP {query} 結果：{value:.4f}",
            #     text_color="green"
            # )
            # 結果區顯示完整說明
            if hasattr(self, "result_panel"):
                # self.result_panel.show_result_value(text)
                self.result_panel.update_result(payload, text, source_df=self.current_df)

        # 直方圖 histogram
        elif query == "histogram":
            hist = payload.get("hist")
            bin_edges = payload.get("bin_edges")
            text = base_info + f"\n直方圖 bins 數量：{len(hist)}"
            self.status_label.configure(
                text=f"DP histogram 完成，bins={len(hist)}",
                text_color="green"
            )
            # 現階段先用文字顯示；之後你可以在這裡畫圖
            if hasattr(self, "result_panel"):
                # self.result_panel.show_result_value(text)
                self.result_panel.update_result(payload, text, source_df=self.current_df)

        else:
            self.status_label.configure(
                text="差分隱私運算完成（未知的 query 類型）",
                text_color="green"
            )
            if hasattr(self, "result_panel"):
                self.result_panel.show_result_value(base_info + "\n(未知的 query 類型)")

        # Debug 用：也可以看一下目前所有設定
        print("DP settings:", dp_settings.get_all())

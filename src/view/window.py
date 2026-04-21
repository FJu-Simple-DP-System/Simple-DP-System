# src/view/window.py
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
import os
import pandas as pd
import threading
from AI_predata.ai_helper import suggest_dp_parameters

# 引入所有元件
from src.view.components import FileDropFrame
from src.view.preview import DataPreviewTable
from src.view.settings import SettingsPanel
from src.view.start import StartScreen
from src.view.results import ResultPanel
from src.view.predata_panel import PreDataPanel  # 引入剛建立的預處理面板

from src.core.elements import dp_settings
from src.core.engine import run_dp_from_settings

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("簡單差分隱私系統 - V0.3 (整合版)")
        self.geometry("1200x800")

        self.show_start_screen()

    def show_start_screen(self):
        self.start_screen = StartScreen(self, on_start_callback=self.enter_main_app)
        self.start_screen.pack(fill="both", expand=True)

    def enter_main_app(self):
        self.start_screen.destroy()
        self.init_configs()

    def init_configs(self):
        self.current_df = None

        # --- 建立 Tabview (分頁元件) ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_predata = self.tabview.add("1. 資料預處理 (AI)")
        self.tab_dp = self.tabview.add("2. 差分隱私分析 (DP)")

        # ==========================================
        # 分頁 1: 資料預處理面板
        # ==========================================
        self.predata_panel = PreDataPanel(
            self.tab_predata, 
            on_data_ready=self.handle_df_from_predata  # 綁定自動拋轉事件
        )
        self.predata_panel.pack(fill="both", expand=True)

        # ==========================================
        # 分頁 2: 差分隱私分析面板
        # ==========================================
        # 建立一個容器 Frame 來放置原有的 DP UI
        self.dp_container = ctk.CTkFrame(self.tab_dp, fg_color="transparent")
        self.dp_container.pack(fill="both", expand=True)

        self.dp_container.grid_columnconfigure(1, weight=1)
        self.dp_container.grid_rowconfigure(0, weight=1)

        # 左側 DP 設定面板
        self.settings_panel = SettingsPanel(
            self.dp_container, width=250, corner_radius=0, 
            on_run=self.execute_dp, on_ai_suggest=self.handle_ai_suggestion
        )
        self.settings_panel.grid(row=0, column=0, sticky="nsew")

        # 右側 DP 內容區
        self.right_frame = ctk.CTkFrame(self.dp_container, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(3, weight=1) 

        # 標題
        self.title_label = ctk.CTkLabel(self.right_frame, text="資料導入與預覽", font=("Arial", 24, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # 拖曳區
        self.drop_area = FileDropFrame(self.right_frame, width=700, height=120, on_drop_callback=self.handle_file_upload)
        self.drop_area.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        # 預覽標籤與表格
        self.preview_label = ctk.CTkLabel(self.right_frame, text="資料預覽 (前 15 筆)", font=("Arial", 16, "bold"))
        self.table_frame = DataPreviewTable(self.right_frame)

        # 狀態列
        self.status_label = ctk.CTkLabel(self.right_frame, text="請上傳檔案或從預處理接收資料...", text_color="gray")
        self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        # 運算結果面板
        self.result_panel = ResultPanel(self.right_frame)
        self.result_panel.grid(row=5, column=0, sticky="nsew", pady=(10, 0))

    # ==========================================
    # 核心邏輯整合
    # ==========================================
    
    def handle_df_from_predata(self, df):
        """從 AI 預處理面板直接接收 DataFrame 的回呼函式"""
        self.current_df = df
        
        # 1. 重置結果區
        if hasattr(self, "result_panel"):
            self.result_panel.reset()
            
        # 2. 自動切換到 DP 分頁
        self.tabview.set("2. 差分隱私分析 (DP)")

        # 3. 為了讓 DataPreviewTable 可以顯示，我們先將 df 存成一個暫存檔，或者改寫 table_frame 支援直接吃 df
        # 這裡為了相容你原有的架構，我們先寫一個暫存檔並讀取它 (最穩定的做法)
        temp_file = "temp_from_predata.csv"
        df.to_csv(temp_file, index=False)
        
        success, message = self.table_frame.update_data(temp_file)
        
        if success:
            self.status_label.configure(text=f"已從 AI 預處理模組接收資料！總計 {len(df)} 筆", text_color="green")
            self.preview_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
            self.table_frame.grid(row=3, column=0, sticky="nsew")
            self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))
            self.settings_panel.update_columns(list(df.columns))
            
            # 刪除暫存檔保持乾淨
            if os.path.exists(temp_file):
                os.remove(temp_file)
        else:
            self.status_label.configure(text=f"接收資料失敗: {message}", text_color="red")

    def handle_file_upload(self, file_path):
        if hasattr(self, "result_panel"):
            self.result_panel.reset()

        if file_path.lower().endswith(('.csv', '.xlsx')):
            try:
                if file_path.endswith(".csv"):
                    self.current_df = pd.read_csv(file_path)
                else:
                    self.current_df = pd.read_excel(file_path)
            except Exception as e:
                self.status_label.configure(text=f"讀取檔案失敗：{e}", text_color="red")
                return

            success, message = self.table_frame.update_data(file_path)

            if success:
                self.status_label.configure(text=f"已載入：{os.path.basename(file_path)} | {message}", text_color="green")
                self.preview_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
                self.table_frame.grid(row=3, column=0, sticky="nsew")
                self.status_label.grid(row=4, column=0, sticky="ew", pady=(10, 0))
                
                cols = list(self.current_df.columns)
                self.settings_panel.update_columns(cols)
            else:
                self.status_label.configure(text=message, text_color="red")
        else:
            self.status_label.configure(text="錯誤：僅支援 CSV 或 XLSX 格式", text_color="red")

    def execute_dp(self):
        if self.current_df is None:
            self.status_label.configure(text="請先上傳資料檔案再執行差分隱私運算", text_color="red")
            return

        if hasattr(self, "result_panel"):
            self.result_panel.show_loading()

        result = run_dp_from_settings(self.current_df)

        if not result["ok"]:
            self.status_label.configure(text=result["message"], text_color="red")
            if hasattr(self, "result_panel"):
                self.result_panel.reset()
            return

        payload = result["result"]
        query = payload.get("query")

        base_info = (
            f"查詢類型：{query}\n"
            f"ε (epsilon)：{payload.get('epsilon')}\n"
            f"機制 (mechanism)：{payload.get('mechanism')}\n"
            f"欄位 (column)：{payload.get('column')}\n"
            f"資料邊界 (bounds)：{payload.get('bounds')}\n"
        )

        if query in ("mean", "sum", "count"):
            value = payload.get("value")
            text = base_info + f"\n差分隱私後 {query} ：{value:.4f}"
            if hasattr(self, "result_panel"):
                self.result_panel.update_result(payload, text, source_df=self.current_df)

        elif query == "histogram":
            hist = payload.get("hist")
            text = base_info + f"\n直方圖 bins 數量：{len(hist)}"
            self.status_label.configure(text=f"DP histogram 完成，bins={len(hist)}", text_color="green")
            if hasattr(self, "result_panel"):
                self.result_panel.update_result(payload, text, source_df=self.current_df)
        else:
            self.status_label.configure(text="差分隱私運算完成（未知的 query 類型）", text_color="green")
            if hasattr(self, "result_panel"):
                self.result_panel.update_result(payload, base_info + "\n(未知的 query 類型)", source_df=self.current_df)

    def handle_ai_suggestion(self):
        if self.current_df is None:
            self.status_label.configure(text="請先上傳檔案才能獲取建議", text_color="red")
            return

        target_col = dp_settings.get_all().get("column")
        if not target_col:
            self.status_label.configure(text="請先選擇目標欄位", text_color="red")
            return

        try:
            series = pd.to_numeric(self.current_df[target_col], errors='coerce').dropna()
            if series.empty: raise ValueError("欄位無有效數值")
            
            stats = {
                "count": len(series), "mean": float(series.mean()),
                "std": float(series.std()), "min": float(series.min()), "max": float(series.max())
            }
            
            self.status_label.configure(text=f"AI 正在分析 '{target_col}' 的隱私需求...", text_color="orange")
            
            def _task():
                res = suggest_dp_parameters(target_col, stats, log_func=print)
                if res:
                    self.after(0, lambda: self.status_label.configure(text=f"AI 建議 ε={res['suggested_epsilon']}: {res['reason']}", text_color="#3B8ED0"))
                    
                    # 1. 更新 Epsilon 滑桿與標籤
                    self.after(0, lambda: self.settings_panel.slider_epsilon.set(res['suggested_epsilon']))
                    self.after(0, lambda: self.settings_panel.update_epsilon_label(res['suggested_epsilon']))
                    
                    # 2. 【新增】更新 Min / Max 邊界輸入框
                    if "suggested_min" in res and "suggested_max" in res:
                        self.after(0, lambda: self.settings_panel.update_bounds(
                            res['suggested_min'], 
                            res['suggested_max']
                        ))
            
            threading.Thread(target=_task, daemon=True).start()
            
        except Exception as e:
            self.status_label.configure(text=f"建議失敗: {str(e)}", text_color="red")
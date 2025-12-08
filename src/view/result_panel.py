import customtkinter as ctk
import tkinter as tk

class ResultPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 設定邊框與背景，讓它在介面上突出顯示
        self.configure(fg_color=("gray90", "gray20"), corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        # 1. 標題列
        self.lbl_title = ctk.CTkLabel(self, text="運算結果", font=("Arial", 18, "bold"))
        self.lbl_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        # 2. 數值結果顯示區 (顯示 Mean, Sum, Count 等文字結果)
        self.lbl_result_text = ctk.CTkLabel(
            self, 
            text="等待執行...", 
            font=("Arial", 16), 
            text_color="gray",
            wraplength=600,
            justify="left"
        )
        self.lbl_result_text.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        # 3. 圖表顯示容器 (Matplotlib 圖表將放在這裡)
        # 預設隱藏，只有畫圖時才打開
        self.chart_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.chart_frame.grid_remove() # 預設隱藏

        # 4. 操作按鈕區 (下載 & 清除)
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, sticky="e", padx=20, pady=(10, 15))

        self.btn_download = ctk.CTkButton(
            self.btn_frame, 
            text="下載結果 (.csv)", 
            state="disabled", # 預設停用，有結果才能按
            fg_color="#3B8ED0",
            width=120
        )
        self.btn_download.pack(side="right", padx=(10, 0))

    def show_loading(self):
        """顯示處理中狀態"""
        self.lbl_result_text.configure(text="正在進行差分隱私運算... (請稍候)", text_color="#E67E22") # 橘色
        self.chart_frame.grid_remove()
        self.btn_download.configure(state="disabled")
        self.update_idletasks() # 強制刷新 UI

    def show_result_value(self, result_text):
        """顯示純文字/數值結果"""
        self.lbl_result_text.configure(text=result_text, text_color=("black", "white"))
        self.chart_frame.grid_remove() # 如果是純數值，隱藏圖表區
        self.btn_download.configure(state="normal")

    def get_chart_frame(self):
        """回傳圖表容器，讓外部 (Member A/C) 可以把 Matplotlib 放進來"""
        self.chart_frame.grid() # 顯示圖表區
        return self.chart_frame

    def reset(self):
        """重置回初始狀態"""
        self.lbl_result_text.configure(text="等待執行...", text_color="gray")
        self.chart_frame.grid_remove()
        self.btn_download.configure(state="disabled")
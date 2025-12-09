import customtkinter as ctk
from src.view.components import CTkToolTip # 引入剛剛寫的 Tooltip
from src.core.elements import dp_settings

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        self.on_run = kwargs.pop("on_run", None)
        
        super().__init__(master, **kwargs)

        # 標題
        self.label_title = ctk.CTkLabel(self, text="隱私參數設定", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=(20, 10), padx=10, anchor="w")

        # --- 1. 隱私預算 (Epsilon) ---
        self.create_info_label(
            text="隱私預算 (ε): 1.0", 
            tooltip_text="ε (Epsilon) 控制隱私保護程度：\n• 值越小：隱私越高，但數據雜訊越大 (準確度低)。\n• 值越大：數據越準確，但隱私風險較高。\n通常設定在 0.1 到 10 之間。"
        )
        self.lbl_epsilon = self.last_label # 保存引用以便更新數值
        
        self.slider_epsilon = ctk.CTkSlider(self, from_=0.1, to=10.0, number_of_steps=99, command=self.update_epsilon_label)
        self.slider_epsilon.set(1.0)
        self.slider_epsilon.pack(pady=(5, 10), padx=10, fill="x")

        # --- 2. 差分隱私機制 ---
        self.create_info_label(
            text="使用算法 (Mechanism):", 
            tooltip_text="選擇要加入雜訊的數學機制：\n• Laplace：適用於數值型查詢 (如平均、總和)。\n• Exponential：適用於從集合中選擇最佳項目。"
        )
        
        self.opt_algo = ctk.CTkOptionMenu(self, values=["Laplace 機制", "Gaussian 機制"])

        self.opt_algo.pack(pady=(5, 10), padx=10, fill="x")
        self.opt_algo.configure(command=lambda v: dp_settings.set_mechanism(v))


        # --- 3. 統計操作類型 ---
        self.create_info_label(
            text="統計操作 (Query):", 
            tooltip_text="選擇要對資料執行的分析類型：\n• 平均值/總和/計數：單一數值統計。\n• 直方圖：顯示資料的分佈情況。"
        )
        
        self.opt_query = ctk.CTkOptionMenu(self, values=["平均值 (Mean)", "總和 (Sum)", "計數 (Count)", "直方圖 (Histogram)"])
        self.opt_query.pack(pady=(5, 10), padx=10, fill="x")
        self.opt_query.configure(command=lambda v: dp_settings.set_query(v))


        # --- 4. 目標欄位 ---
        self.create_info_label(
            text="目標欄位 (Column):", 
            tooltip_text="選擇要進行隱私保護處理的資料欄位。\n請先上傳檔案以載入欄位列表。"
        )
        
        self.opt_col = ctk.CTkOptionMenu(self, values=["(請先載入檔案)"])
        self.opt_col.pack(pady=(5, 10), padx=10, fill="x")

        self.opt_col.configure(command=lambda v: dp_settings.set_column(v))

        # --- 5. 資料邊界 ---
        self.create_info_label(
            text="資料邊界 (敏感度):", 
            tooltip_text="設定該欄位合理的數值範圍 (如年齡 0-100)：\n此設定用於計算「敏感度」，\n以確保雜訊量的數學正確性。"
        )

        self.frame_bounds = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bounds.pack(pady=5, padx=10, fill="x")
        
        self.entry_min = ctk.CTkEntry(self.frame_bounds, placeholder_text="Min", width=60)
        self.entry_min.pack(side="left", padx=(0, 5), expand=True, fill="x")
        
        self.entry_max = ctk.CTkEntry(self.frame_bounds, placeholder_text="Max", width=60)
        self.entry_max.pack(side="left", padx=(5, 0), expand=True, fill="x")

        # # --- 執行按鈕 ---
        # self.btn_run = ctk.CTkButton(self, text="執行差分隱私運算", fg_color="#2CC985", hover_color="#229A65", height=40)
        # self.btn_run.pack(pady=(30, 20), padx=10, fill="x", side="bottom")

        # --- 執行按鈕 ---
        self.btn_run = ctk.CTkButton(
            self,
            text="執行差分隱私運算",
            fg_color="#2CC985",
            hover_color="#229A65",
            height=40,
            command=self._on_run_clicked  # 按鈕綁到內部方法
        )
        self.btn_run.pack(pady=(30, 20), padx=10, fill="x", side="bottom")


    def create_info_label(self, text, tooltip_text):
        """建立一個帶有 (i) Tooltip 的標題列"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=(10, 0), padx=10, fill="x")
        
        # 標題文字
        label = ctk.CTkLabel(frame, text=text, font=("Arial", 14))
        label.pack(side="left")
        self.last_label = label # 暫存引用
        
        # 資訊圖示 (圓形小按鈕)
        info_btn = ctk.CTkButton(
            frame, 
            text="?", 
            width=20, 
            height=20, 
            corner_radius=10,
            fg_color="gray", 
            hover_color="gray70",
            font=("Arial", 12, "bold")
        )
        info_btn.pack(side="right")
        
        # 綁定 Tooltip
        CTkToolTip(info_btn, tooltip_text)

    def update_epsilon_label(self, value):
        self.lbl_epsilon.configure(text=f"隱私預算 (ε): {float(value):.1f}")

        dp_settings.set_epsilon(value)

    def update_columns(self, columns):
        if columns:
            self.opt_col.configure(values=columns)
            self.opt_col.set(columns[0])
        else:
            self.opt_col.configure(values=["(無可用欄位)"])

    def _on_run_clicked(self):
        # 先把敏感度寫回 dp_settings
        dp_settings.set_sensitivity(
            self.entry_min.get(),
            self.entry_max.get()
        )
        # 然後如果有外部 callback，就呼叫它（交給 MainWindow 處理真的 DP 運算）
        if self.on_run is not None:
            self.on_run()

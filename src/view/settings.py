import customtkinter as ctk
from src.view.components import CTkToolTip
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
            tooltip_text="ε (Epsilon) 控制隱私保護程度：\n• 值越小：隱私越高，但雜訊越大。\n• 值越大：數據越準確，隱私風險較高。"
        )
        self.lbl_epsilon = self.last_label
        
        self.slider_epsilon = ctk.CTkSlider(self, from_=0.1, to=10.0, number_of_steps=99, command=self.update_epsilon_label)
        self.slider_epsilon.set(1.0)
        self.slider_epsilon.pack(pady=(5, 10), padx=10, fill="x")

        # --- 2. 差分隱私機制 (包含 Delta 設定) ---
        # 【修改】建立一個專門的 Frame 來包裝機制選單與 Delta 設定
        # 這樣當 Delta 隱藏/顯示時，不會打亂下方元件的順序
        self.mech_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mech_frame.pack(pady=(5, 10), padx=10, fill="x")

        # 2-1. 機制標題與選單
        self.create_info_label(
            parent=self.mech_frame, # 注意這裡 parent 改為 mech_frame
            text="使用算法 (Mechanism):", 
            tooltip_text="• Laplace：純差分隱私，適用一般數值。\n• Gaussian：(ε, δ)-近似差分隱私，適用高維度或向量。"
        )
        
        self.opt_algo = ctk.CTkOptionMenu(
            self.mech_frame, # parent 改為 mech_frame
            values=["Laplace 機制", "Gaussian 機制"],
            command=self._on_mech_change # 綁定切換事件
        )
        self.opt_algo.pack(pady=(5, 5), fill="x")

        # 2-2. Delta 設定區域 (預設隱藏)
        self.frame_delta = ctk.CTkFrame(self.mech_frame, fg_color="transparent")
        # 這裡不 .pack()，等到切換到 Gaussian 時才顯示
        
        # Delta 標籤
        self.lbl_delta = ctk.CTkLabel(self.frame_delta, text="失敗機率 (δ):", font=("Arial", 14))
        self.lbl_delta.pack(side="left", padx=(0, 5))
        
        # Delta 輸入框
        self.entry_delta = ctk.CTkEntry(self.frame_delta, placeholder_text="1e-5", width=100)
        self.entry_delta.pack(side="right", expand=True, fill="x")
        self.entry_delta.insert(0, "1e-5") # 預設值

        # Tooltip for Delta
        CTkToolTip(self.lbl_delta, "δ (Delta) 代表隱私保證失效的極小機率。\n通常設定為遠小於 1/N (例如 1e-5)。")


        # --- 3. 統計操作類型 ---
        self.create_info_label(
            text="統計操作 (Query):", 
            tooltip_text="選擇要對資料執行的分析類型：\n• 平均值/總和/計數：單一數值統計。\n• 直方圖：顯示資料的分佈情況。")
        self.opt_query = ctk.CTkOptionMenu(self, values=["平均值 (Mean)", "總和 (Sum)", "計數 (Count)", "直方圖 (Histogram)"])
        self.opt_query.pack(pady=(5, 10), padx=10, fill="x")
        self.opt_query.configure(command=lambda v: dp_settings.set_query(v))

        # --- 4. 目標欄位 ---
        self.create_info_label(
            text="目標欄位 (Column):", 
            tooltip_text="選擇要進行隱私保護處理的資料欄位。"
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

        # --- 執行按鈕 ---
        self.btn_run = ctk.CTkButton(
            self,
            text="執行差分隱私運算",
            fg_color="#2CC985",
            hover_color="#229A65",
            height=40,
            command=self._on_run_clicked
        )
        self.btn_run.pack(pady=(30, 20), padx=10, fill="x", side="bottom")

    def create_info_label(self, text, tooltip_text, parent=None):
        """
        建立一個帶有 (i) Tooltip 的標題列
        parent: 指定父容器，若無則預設為 self
        """
        target = parent if parent else self
        
        frame = ctk.CTkFrame(target, fg_color="transparent")
        frame.pack(pady=(10, 0), padx=0 if parent else 10, fill="x") # parent 內部已有 padding
        
        label = ctk.CTkLabel(frame, text=text, font=("Arial", 14))
        label.pack(side="left")
        self.last_label = label 
        
        info_btn = ctk.CTkButton(
            frame, text="?", width=20, height=20, corner_radius=10,
            fg_color="gray", hover_color="gray70", font=("Arial", 12, "bold")
        )
        info_btn.pack(side="right")
        CTkToolTip(info_btn, tooltip_text)

    def update_epsilon_label(self, value):
        self.lbl_epsilon.configure(text=f"隱私預算 (ε): {float(value):.1f}")
        dp_settings.set_epsilon(value)

    def _on_mech_change(self, value):
        """當機制改變時，決定是否顯示 Delta 設定"""
        dp_settings.set_mechanism(value)
        
        if "Gaussian" in value or "高斯" in value:
            # 顯示 Delta
            self.frame_delta.pack(pady=(5, 0), fill="x")
        else:
            # 隱藏 Delta
            self.frame_delta.pack_forget()

    def update_columns(self, columns):
        if columns:
            self.opt_col.configure(values=columns)
            self.opt_col.set(columns[0])
            dp_settings.set_column(columns[0]) # 自動選第一個
        else:
            self.opt_col.configure(values=["(無可用欄位)"])

    def _on_run_clicked(self):
        # 1. 寫回敏感度
        dp_settings.set_sensitivity(self.entry_min.get(), self.entry_max.get())
        
        # 2. 【新增】寫回 Delta (如果是 Gaussian)
        if "Gaussian" in dp_settings.mechanism:
            delta_val = self.entry_delta.get()
            # 簡單驗證或預設值處理交給 Engine，這裡只負責傳值
            if not delta_val: delta_val = "1e-5"
            dp_settings.set_delta(delta_val)

        # 3. 執行
        if self.on_run is not None:
            self.on_run()
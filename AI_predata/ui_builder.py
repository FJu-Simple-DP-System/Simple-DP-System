
import customtkinter as ctk

class UILayoutMixin:
    def build_ui(self):
            # --- 【新增/修改】AI 模型與 API Key 設定區塊 ---
            self.frame_left = ctk.CTkFrame(self, width=300)
            self.frame_left.pack(side="left", fill="y", padx=10, pady=10)
            self.frame_api = ctk.CTkFrame(self.frame_left, fg_color="transparent")
            self.frame_api.pack(pady=(5, 10), fill="x", padx=10)
            
            ctk.CTkLabel(self.frame_api, text="🤖 AI 模型與金鑰", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
            
            # 1. 供應商下拉選單
            self.opt_ai_provider = ctk.CTkOptionMenu(
                self.frame_api, 
                values=["Gemini", "OpenAI", "Claude", "Ollama (本地端)"],
                command=self.on_provider_change
            )
            self.opt_ai_provider.pack(fill="x", pady=(5, 5))

            # 2. 金鑰輸入區塊
            self.frame_key_input = ctk.CTkFrame(self.frame_api, fg_color="transparent")
            self.frame_key_input.pack(fill="x")

            self.entry_api_key = ctk.CTkEntry(self.frame_key_input, placeholder_text="輸入對應的 API Key...")
            self.entry_api_key.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.entry_api_key.bind("<FocusIn>", self.on_api_key_focus_in)
            self.entry_api_key.bind("<FocusOut>", self.on_api_key_focus_out)
            
            self.btn_save_api = ctk.CTkButton(self.frame_key_input, text="儲存", width=40, command=self.save_api_key)
            self.btn_save_api.pack(side="right")
            
            # 記憶體中的 Key 暫存字典
            self.api_keys_cache = {"Gemini": "", "OpenAI": "", "Claude": "", "Ollama (本地端)": "llama3"}
            # -----------------------------
            
            ctk.CTkLabel(self.frame_left, text="📂 資料載入", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
            
            # --- 資料檔載入區塊 (包含清除按鈕) ---
            self.frame_data_btns = ctk.CTkFrame(self.frame_left, fg_color="transparent")
            self.frame_data_btns.pack(pady=5, fill="x", padx=10)
            
            self.btn_load_data = ctk.CTkButton(self.frame_data_btns, text="1. 載入資料檔 (.csv/.data)", command=self.load_data_files)
            self.btn_load_data.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            self.btn_clear_data = ctk.CTkButton(self.frame_data_btns, text="✖", width=35, fg_color="#d9534f", hover_color="#c9302c", command=self.clear_data_files)
            self.btn_clear_data.pack(side="right")

            # --- 描述檔載入區塊 (包含清除按鈕) ---
            self.frame_desc_btns = ctk.CTkFrame(self.frame_left, fg_color="transparent")
            self.frame_desc_btns.pack(pady=5, fill="x", padx=10)
            
            self.btn_load_desc = ctk.CTkButton(self.frame_desc_btns, text="2. 載入描述檔 (.names/.txt)", command=self.load_desc_file)
            self.btn_load_desc.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            self.btn_clear_desc = ctk.CTkButton(self.frame_desc_btns, text="✖", width=35, fg_color="#d9534f", hover_color="#c9302c", command=self.clear_desc_file)
            self.btn_clear_desc.pack(side="right")

            # --- 預處理開關區 ---
            ctk.CTkLabel(self.frame_left, text="⚙️ 預處理步驟控制", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
            
            self.chk_ai_profile = ctk.CTkCheckBox(self.frame_left, text="Step 1: AI 預判斷表頭與類別")
            self.chk_ai_profile.pack(pady=3, anchor="w", padx=10)
            self.chk_ai_profile.select()

            self.chk_merge = ctk.CTkCheckBox(self.frame_left, text="Step 2: 合併多資料表 (Concat)")
            self.chk_merge.pack(pady=3, anchor="w", padx=10)
            self.chk_merge.select()

            self.chk_fill_cols = ctk.CTkCheckBox(self.frame_left, text="Step 3: AI 自動補齊缺失欄位名")
            self.chk_fill_cols.pack(pady=3, anchor="w", padx=10)
            self.chk_fill_cols.select()

            self.chk_cat_encode = ctk.CTkCheckBox(self.frame_left, text="Step 4: AI 類別欄位轉換數值")
            self.chk_cat_encode.pack(pady=3, anchor="w", padx=10)
            self.chk_cat_encode.select()

            self.chk_clean_summary = ctk.CTkCheckBox(self.frame_left, text="Step 5: 清除多餘總和/統計列")
            self.chk_clean_summary.pack(pady=3, anchor="w", padx=10)
            self.chk_clean_summary.select()

            self.chk_handle_nan = ctk.CTkCheckBox(self.frame_left, text="Step 6: 處理空值 (填補0)")
            self.chk_handle_nan.pack(pady=3, anchor="w", padx=10)
            self.chk_handle_nan.select()

            self.chk_dp_clip = ctk.CTkCheckBox(self.frame_left, text="Step 7: DP 異常值截斷 (AI批次)")
            self.chk_dp_clip.pack(pady=3, anchor="w", padx=10)
            self.chk_dp_clip.select()

            self.btn_process = ctk.CTkButton(self.frame_left, text="▶ 執行 Pipeline", fg_color="green", hover_color="darkgreen", command=self.start_processing)
            self.btn_process.pack(pady=15, fill="x", padx=10)

            self.btn_save = ctk.CTkButton(self.frame_left, text="💾 儲存預處理資料", command=self.save_data, state="disabled")
            self.btn_save.pack(pady=5, fill="x", padx=10)

            # 右側日誌區
            self.frame_right = ctk.CTkFrame(self)
            self.frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
            self.log_box = ctk.CTkTextbox(self.frame_right, width=500, height=300)
            self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
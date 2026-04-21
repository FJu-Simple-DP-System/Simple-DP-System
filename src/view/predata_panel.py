# src/view/predata_panel.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import json
import sys

# 引入原有的 AI 預處理邏輯
from AI_predata import config
from AI_predata.data_processor import DataPipeline

def get_app_dir():
    """取得程式執行當下的目錄"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.getcwd()  # 回傳專案根目錄

class PreDataPanel(ctk.CTkFrame):
    def __init__(self, master, on_data_ready=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.on_data_ready = on_data_ready # 用於將處理完的資料拋轉給 DP 面板的 Callback
        self.data_files = []
        self.desc_file = ""
        self.processed_df = None
        
        self.build_ui()
        self.load_api_key()

    def build_ui(self):
        """將原先 ui_builder.py 的內容整合至此"""
        # --- 左側控制區 ---
        self.frame_left = ctk.CTkFrame(self, width=300)
        self.frame_left.pack(side="left", fill="y", padx=10, pady=10)
        
        # 1. AI 模型與金鑰
        self.frame_api = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_api.pack(pady=(5, 10), fill="x", padx=10)
        ctk.CTkLabel(self.frame_api, text="🤖 AI 模型與金鑰", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        
        self.opt_ai_provider = ctk.CTkOptionMenu(
            self.frame_api, 
            values=["Gemini", "OpenAI", "Claude", "Ollama (本地端)"],
            command=self.on_provider_change
        )
        self.opt_ai_provider.pack(fill="x", pady=(5, 5))

        self.frame_key_input = ctk.CTkFrame(self.frame_api, fg_color="transparent")
        self.frame_key_input.pack(fill="x")
        self.entry_api_key = ctk.CTkEntry(self.frame_key_input, placeholder_text="輸入對應的 API Key...")
        self.entry_api_key.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_api_key.bind("<FocusIn>", self.on_api_key_focus_in)
        self.entry_api_key.bind("<FocusOut>", self.on_api_key_focus_out)
        
        self.btn_save_api = ctk.CTkButton(self.frame_key_input, text="儲存", width=40, command=self.save_api_key)
        self.btn_save_api.pack(side="right")
        self.api_keys_cache = {"Gemini": "", "OpenAI": "", "Claude": "", "Ollama (本地端)": "llama3"}

        # 2. 資料載入區
        ctk.CTkLabel(self.frame_left, text="📂 資料載入", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.frame_data_btns = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_data_btns.pack(pady=5, fill="x", padx=10)
        self.btn_load_data = ctk.CTkButton(self.frame_data_btns, text="1. 載入資料檔 (.csv/.data)", command=self.load_data_files)
        self.btn_load_data.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_clear_data = ctk.CTkButton(self.frame_data_btns, text="✖", width=35, fg_color="#d9534f", hover_color="#c9302c", command=self.clear_data_files)
        self.btn_clear_data.pack(side="right")

        self.frame_desc_btns = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_desc_btns.pack(pady=5, fill="x", padx=10)
        self.btn_load_desc = ctk.CTkButton(self.frame_desc_btns, text="2. 載入描述檔 (.names/.txt)", command=self.load_desc_file)
        self.btn_load_desc.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_clear_desc = ctk.CTkButton(self.frame_desc_btns, text="✖", width=35, fg_color="#d9534f", hover_color="#c9302c", command=self.clear_desc_file)
        self.btn_clear_desc.pack(side="right")

        # 3. 預處理開關區
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

        # 4. 執行與儲存按鈕
        self.btn_process = ctk.CTkButton(self.frame_left, text="▶ 執行 Pipeline", fg_color="green", hover_color="darkgreen", command=self.start_processing)
        self.btn_process.pack(pady=15, fill="x", padx=10)
        
        self.btn_send_to_dp = ctk.CTkButton(self.frame_left, text="🚀 直接送至 DP 模組", fg_color="#E67E22", hover_color="#D35400", command=self.send_to_dp, state="disabled")
        self.btn_send_to_dp.pack(pady=(0, 5), fill="x", padx=10)

        self.btn_save = ctk.CTkButton(self.frame_left, text="💾 儲存預處理資料", command=self.save_data, state="disabled")
        self.btn_save.pack(pady=5, fill="x", padx=10)

        # --- 右側日誌區 ---
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.log_box = ctk.CTkTextbox(self.frame_right)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    # ================= 原本的邏輯函式 =================
    def on_provider_change(self, selected_provider):
        self.entry_api_key.delete(0, "end")
        saved_val = self.api_keys_cache.get(selected_provider, "")
        if "Ollama" in selected_provider:
            self.entry_api_key.configure(placeholder_text="輸入 Ollama 模型名稱 (例: llama3)", show="")
            if saved_val: self.entry_api_key.insert(0, saved_val)
        else:
            self.entry_api_key.configure(placeholder_text="輸入對應的 API Key...")
            if saved_val:
                self.entry_api_key.insert(0, saved_val)
                self.entry_api_key.configure(show="*")
            else:
                self.entry_api_key.configure(show="")

    def sync_to_config(self):
        """將目前 UI 快取的 API Key 同步到 AI 邏輯使用的 config 模組"""
        current_provider = self.opt_ai_provider.get()
        current_key = self.api_keys_cache.get(current_provider, "")
        
        # 強制寫入 config 模組
        config.ACTIVE_AI = current_provider
        if current_provider == "Gemini":
            config.API_KEY = current_key
        elif current_provider == "OpenAI":
            config.OPENAI_API_KEY = current_key
        elif current_provider == "Claude":
            config.CLAUDE_API_KEY = current_key
        elif "Ollama" in current_provider:
            config.OLLAMA_MODEL = current_key

    def load_api_key(self):
        settings_path = os.path.join(get_app_dir(), "AI_predata", "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_keys_cache = data.get("keys", {"Gemini": "", "OpenAI": "", "Claude": ""})
                    last_ai = data.get("active_ai", "Gemini")
                    self.opt_ai_provider.set(last_ai)
                    self.on_provider_change(last_ai)
                    self.sync_to_config()
            except Exception as e:
                self.log(f"[警告] 無法讀取本地設定: {e}")

    def save_api_key(self):
        current_provider = self.opt_ai_provider.get()
        key = self.entry_api_key.get().strip()
        self.api_keys_cache[current_provider] = key
        
        # 確保 AI_predata 資料夾存在
        save_dir = os.path.join(get_app_dir(), "AI_predata")
        os.makedirs(save_dir, exist_ok=True)
        settings_path = os.path.join(save_dir, "settings.json")
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump({"active_ai": current_provider, "keys": self.api_keys_cache}, f)
            self.sync_to_config()
            self.log(f"[系統] {current_provider} 的設定已成功儲存。")
            if "Ollama" not in current_provider:
                self.entry_api_key.configure(show="*")
        except Exception as e:
            self.log(f"[錯誤] 儲存設定失敗: {e}")

    def on_api_key_focus_in(self, event):
        self.entry_api_key.configure(show="")
    def on_api_key_focus_out(self, event):
        if self.entry_api_key.get().strip():
            self.entry_api_key.configure(show="*")

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def load_data_files(self):
        files = filedialog.askopenfilenames(title="選擇資料檔", filetypes=[("Data & CSV Files", "*.csv *.data"), ("All Files", "*.*")])
        if files:
            new_files = [f for f in files if f not in self.data_files]
            self.data_files.extend(new_files)
            if new_files:
                self.log(f"[載入] 成功加入，目前總共已選擇 {len(self.data_files)} 個資料檔。")
            else:
                self.log(f"[提示] 檔案已在清單裡！維持 {len(self.data_files)} 個。")

    def clear_data_files(self):
        self.data_files = []
        self.log("[清理] 已清空所選的「資料檔」。")

    def load_desc_file(self):
        file = filedialog.askopenfilename(title="選擇描述檔", filetypes=[("Description Files", "*.names *.txt"), ("All Files", "*.*")])
        if file:
            self.desc_file = file
            self.log(f"[載入] 已選擇描述檔: {os.path.basename(file)}")

    def clear_desc_file(self):
        self.desc_file = ""
        self.log("[清理] 已清空所選的「描述檔」。")

    def start_processing(self):
        if not self.data_files:
            messagebox.showerror("錯誤", "請先載入至少一個資料檔！")
            return
            
        provider = self.opt_ai_provider.get()
        current_key = self.api_keys_cache.get(provider, "")
        if not current_key:
            err_msg = "模型名稱" if "Ollama" in provider else "API Key"
            messagebox.showerror("錯誤", f"請先輸入並儲存 {provider} 的 {err_msg}！")
            return
        
        config.ACTIVE_AI = provider
        if provider == "Gemini": config.API_KEY = current_key
        elif provider == "OpenAI": config.OPENAI_API_KEY = current_key
        elif provider == "Claude": config.CLAUDE_API_KEY = current_key
        elif "Ollama" in provider: config.OLLAMA_MODEL = current_key
        
        options = {
            "ai_profile": self.chk_ai_profile.get(),
            "merge": self.chk_merge.get(),
            "fill_cols": self.chk_fill_cols.get(),
            "cat_encode": self.chk_cat_encode.get(),
            "clean_summary": self.chk_clean_summary.get(),
            "handle_nan": self.chk_handle_nan.get(),
            "dp_clip": self.chk_dp_clip.get()
        }

        threading.Thread(target=self.run_pipeline_thread, args=(options,), daemon=True).start()

    def run_pipeline_thread(self, options):
        self.btn_process.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self.btn_send_to_dp.configure(state="disabled")
        
        pipeline = DataPipeline(log_callback=lambda m: self.after(0, self.log, m))
        success, df = pipeline.run(self.data_files, self.desc_file, options)
        
        if success and df is not None:
            self.processed_df = df
            self.after(0, lambda: self.btn_save.configure(state="normal"))
            self.after(0, lambda: self.btn_send_to_dp.configure(state="normal"))
            self.after(0, lambda: self.log("\n提示：您可以儲存檔案，或直接點擊『🚀 直接送至 DP 模組』！"))
            
        self.after(0, lambda: self.btn_process.configure(state="normal"))

    def send_to_dp(self):
        """將處理好的 DataFrame 直接送到主程式的 DP 模組"""
        if self.processed_df is not None and self.on_data_ready:
            self.on_data_ready(self.processed_df)

    def save_data(self):
        if self.processed_df is not None:
            save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if save_path:
                self.processed_df.to_csv(save_path, index=False)
                self.log(f"[儲存] 檔案已存至: {save_path}")
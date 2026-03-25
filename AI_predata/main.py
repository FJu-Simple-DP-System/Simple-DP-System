# main.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import json      # <--- 新增：用於本地儲存設定檔
import config    # <--- 新增：為了在執行時覆寫記憶體中的 API Key
import sys

# 引入我們拆分出來的模組
from data_processor import DataPipeline
from ai_helper import setup_genai

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
def get_app_dir():
    """取得程式執行當下的目錄 (相容 PyInstaller 打包與原始碼執行)"""
    if getattr(sys, 'frozen', False):
        # 如果是被打包成執行檔，取得 .exe 所在的實體資料夾
        return os.path.dirname(sys.executable)
    else:
        # 如果是直接執行 .py 腳本，取得腳本所在的資料夾
        return os.path.dirname(os.path.abspath(__file__))

class DPDataProcessorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SimpleDPSystem - 資料預處理模組")
        self.geometry("1000x750")
        
        # 狀態變數
        self.data_files = []
        self.desc_file = ""
        self.processed_df = None
        
        self.build_ui()
        self.load_api_key()

    # --- 【新增】API Key 本地儲存邏輯 ---
    def load_api_key(self):
        """啟動時從本地讀取 API Key"""
        settings_path = os.path.join(get_app_dir(), "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    key = data.get("api_key", "")
                    if key:
                        self.entry_api_key.insert(0, key)
                        
                        # 【新增】讀取到已儲存的密鑰時，直接顯示為密文
                        self.entry_api_key.configure(show="*")
                        
            except Exception as e:
                self.log(f"[警告] 無法讀取本地 API Key: {e}")

    def save_api_key(self):
        """儲存 API Key 到本地 json 檔"""
        key = self.entry_api_key.get().strip()
        if key:
            settings_path = os.path.join(get_app_dir(), "settings.json")
            try:
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump({"api_key": key}, f)
                self.log("[系統] API Key 已成功儲存至本地。")
                messagebox.showinfo("成功", "API Key 已儲存！")
                
                # 【新增】儲存成功後，將輸入框轉換為密文
                self.entry_api_key.configure(show="*")
                
            except Exception as e:
                self.log(f"[錯誤] 儲存 API Key 失敗: {e}")
        else:
            messagebox.showwarning("警告", "API Key 不能為空！")

    def build_ui(self):
        # 左側控制面板
        self.frame_left = ctk.CTkFrame(self, width=300)
        self.frame_left.pack(side="left", fill="y", padx=10, pady=10)
        # --- 【新增】API Key 設定區塊 ---
        self.frame_api = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_api.pack(pady=(5, 10), fill="x", padx=10)
        
        ctk.CTkLabel(self.frame_api, text="🔑 Gemini API Key", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        
        # 建立輸入框 (預設明文)
        self.entry_api_key = ctk.CTkEntry(self.frame_api, placeholder_text="輸入 API Key...")
        self.entry_api_key.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 【新增】綁定焦點事件
        self.entry_api_key.bind("<FocusIn>", self.on_api_key_focus_in)
        self.entry_api_key.bind("<FocusOut>", self.on_api_key_focus_out)
        
        self.btn_save_api = ctk.CTkButton(self.frame_api, text="儲存", width=40, command=self.save_api_key)
        self.btn_save_api.pack(side="right")
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

    def on_api_key_focus_in(self, event):
        """當滑鼠點擊或對焦輸入框時，暫時恢復為明文以便編輯"""
        self.entry_api_key.configure(show="")

    def on_api_key_focus_out(self, event):
        """當游標離開輸入框時，若裡面有字串則轉為密文"""
        if self.entry_api_key.get().strip():
            self.entry_api_key.configure(show="*")

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    # --- 檔案載入與清除邏輯 ---
    def load_data_files(self):
        files = filedialog.askopenfilenames(title="選擇資料檔", filetypes=[("Data & CSV Files", "*.csv *.data"), ("All Files", "*.*")])
        
        if files:
            new_files = []
            for f in files:
                # 檢查是否已經在清單中，避免重複疊加
                if f not in self.data_files:
                    self.data_files.append(f)
                    new_files.append(f)
            
            # 判斷這次有沒有真正新增的檔案
            if new_files:
                self.log(f"[載入] 成功加入，目前總共已選擇 {len(self.data_files)} 個資料檔。")
                self.log("本次新增的檔案：")
                for file_path in new_files:
                    self.log(f"  - {os.path.basename(file_path)}")
            else:
                self.log(f"[提示] 剛剛選的檔案都已經在清單裡囉！目前總計維持 {len(self.data_files)} 個資料檔。")

    def clear_data_files(self):
        if self.data_files:
            self.data_files = []
            self.log("[清理] 已清空所選的「資料檔」。")
        else:
            self.log("[提示] 目前沒有載入任何資料檔。")

    def load_desc_file(self):
        file = filedialog.askopenfilename(title="選擇描述檔", filetypes=[("Description Files", "*.names *.txt"), ("All Files", "*.*")])
        if file:
            self.desc_file = file
            self.log(f"[載入] 已選擇描述檔: {os.path.basename(file)}")

    def clear_desc_file(self):
        if self.desc_file:
            self.desc_file = ""
            self.log("[清理] 已清空所選的「描述檔」。")
        else:
            self.log("[提示] 目前沒有載入任何描述檔。")

    # --- 執行與儲存邏輯 ---
    def start_processing(self):
        if not self.data_files:
            messagebox.showerror("錯誤", "請先載入至少一個資料檔！")
            return
            
        # --- 【新增】將 GUI 上的 API Key 寫入 config 記憶體中 ---
        current_key = self.entry_api_key.get().strip()
        if not current_key:
            messagebox.showerror("錯誤", "請先輸入並儲存 API Key！")
            return
        
        config.API_KEY = current_key
        # ----------------------------------------------------

        try:
            setup_genai()
        except Exception as e:
            messagebox.showerror("API 錯誤", str(e))
            self.log(f"[錯誤] {str(e)}")
            return
        
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
        
        pipeline = DataPipeline(log_callback=self.log)
        success, df = pipeline.run(self.data_files, self.desc_file, options)
        
        if success and df is not None:
            self.processed_df = df
            self.btn_save.configure(state="normal")
            self.log("提示：您可以點擊左下角儲存處理完畢的資料，準備進入加雜訊模組！")
            
        self.btn_process.configure(state="normal")

    def save_data(self):
        if self.processed_df is not None:
            save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if save_path:
                self.processed_df.to_csv(save_path, index=False)
                self.log(f"[儲存] 檔案已存至: {save_path}")

if __name__ == "__main__":
    app = DPDataProcessorApp()
    app.mainloop()
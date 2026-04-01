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
from ui_builder import UILayoutMixin

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

class DPDataProcessorApp(ctk.CTk, UILayoutMixin):
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
    
    def on_provider_change(self, selected_provider):
        self.entry_api_key.delete(0, "end")
        saved_val = self.api_keys_cache.get(selected_provider, "")
        
        if "Ollama" in selected_provider:
            # 本地端：提示文字改為模型名稱，且永不隱藏文字
            self.entry_api_key.configure(placeholder_text="輸入 Ollama 模型名稱 (例: llama3)", show="")
            if saved_val:
                self.entry_api_key.insert(0, saved_val)
        else:
            # 雲端端：提示輸入 API Key
            self.entry_api_key.configure(placeholder_text="輸入對應的 API Key...")
            if saved_val:
                self.entry_api_key.insert(0, saved_val)
                self.entry_api_key.configure(show="*")
            else:
                self.entry_api_key.configure(show="")

    # --- 【新增】API Key 本地儲存邏輯 ---
    def load_api_key(self):
        """啟動時從本地讀取設定檔"""
        settings_path = os.path.join(get_app_dir(), "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 讀取快取
                    self.api_keys_cache = data.get("keys", {"Gemini": "", "OpenAI": "", "Claude": ""})
                    # 還原上次使用的供應商
                    last_ai = data.get("active_ai", "Gemini")
                    self.opt_ai_provider.set(last_ai)
                    self.on_provider_change(last_ai)
            except Exception as e:
                self.log(f"[警告] 無法讀取本地設定: {e}")

    def save_api_key(self):
        current_provider = self.opt_ai_provider.get()
        key = self.entry_api_key.get().strip()
        
        self.api_keys_cache[current_provider] = key
        
        settings_path = os.path.join(get_app_dir(), "settings.json")
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump({
                    "active_ai": current_provider,
                    "keys": self.api_keys_cache
                }, f)
            self.log(f"[系統] {current_provider} 的設定已成功儲存。")
            
            # 只有非 Ollama 的雲端 API 才需要在儲存後轉成密文
            if "Ollama" not in current_provider:
                self.entry_api_key.configure(show="*")
                
        except Exception as e:
            self.log(f"[錯誤] 儲存設定失敗: {e}")

    

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
            
        # --- 【新增】將當前選擇的 AI 與 Key 寫入 config ---
        provider = self.opt_ai_provider.get()
        current_key = self.api_keys_cache.get(provider, "")
        
        if not current_key:
            err_msg = "模型名稱" if "Ollama" in provider else "API Key"
            messagebox.showerror("錯誤", f"請先輸入並儲存 {provider} 的 {err_msg}！")
            return
        
        config.ACTIVE_AI = provider
        if provider == "Gemini":
            config.API_KEY = current_key
        elif provider == "OpenAI":
            config.OPENAI_API_KEY = current_key
        elif provider == "Claude":
            config.CLAUDE_API_KEY = current_key
        elif "Ollama" in provider:
            config.OLLAMA_MODEL = current_key # Ollama 的欄位填入的是模型名稱
        # ---------------------------------------------------

        
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
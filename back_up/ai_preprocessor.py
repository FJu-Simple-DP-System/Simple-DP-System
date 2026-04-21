import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import os
import threading

# ==========================================
# 1. 全域與 API 設定
# ==========================================
API_KEY = "YOUR_API_KEY_HERE"  # 【請務必填寫您的 API Key】
MODEL_NAME = "gemini-2.5-flash"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ==========================================
# 2. AI 核心邏輯 (包含批次處理)
# ==========================================
def setup_genai():
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        raise ValueError("請先在程式碼最上方設定有效的 Google API Key！")
    genai.configure(api_key=API_KEY)

def analyze_data_structure_with_gemini(sample_csv_text: str):
    setup_genai()
    generation_config = {"temperature": 0.0, "response_mime_type": "application/json"}
    model = genai.GenerativeModel(MODEL_NAME, generation_config=generation_config)
    prompt = f"""
    任務：分析以下 CSV 資料的前 5 筆紀錄，判斷其結構。
    CSV 內容：\n---\n{sample_csv_text}\n---\n
    請回傳嚴格的 JSON 格式：
    1. "has_header": true 或 false (第一列是否為欄位名稱)。
    2. "categorical_mappings": 若有字串類別欄位(如性別)，請建立轉數字(0,1,2...)的字典。如 {{"Gender": {{"M": 0, "F": 1}}}}。沒有則回傳 {{}}。
    """
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result.get("has_header", False), result.get("categorical_mappings", {})
    except Exception as e:
        print(f"[ERROR] AI 結構解析失敗: {e}")
        return True, {} # 失敗時預設有表頭，保護資料

def extract_columns_with_gemini(names_content: str):
    setup_genai()
    generation_config = {"temperature": 0.1, "response_mime_type": "application/json"}
    model = genai.GenerativeModel(MODEL_NAME, generation_config=generation_config)
    prompt = f"""
    任務：從以下的資料集描述文件中提取所有的「欄位名稱 (Column Names)」。
    文件內容：\n---\n{names_content}\n---\n
    規則：回傳 JSON Array (List of strings)。例如: ["id", "age", "target"]
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception:
        return []

def infer_bounds_batch_with_gemini(stats_dict):
    """一次性讓 AI 推算多個欄位的 Clipping 上下限 (批次處理優化)"""
    setup_genai()
    generation_config = {"temperature": 0.1, "response_mime_type": "application/json"}
    model = genai.GenerativeModel(MODEL_NAME, generation_config=generation_config)
    
    prompt = f"""
    任務：為了差分隱私 (Differential Privacy)，需要對以下數值欄位進行異常值截斷 (Clipping)。
    統計分佈 (JSON)：
    {json.dumps(stats_dict, ensure_ascii=False, indent=2)}
    
    請為每個欄位推算合理的 [下限, 上限] 範圍。回傳嚴格 JSON，以欄位名稱為 key：
    {{ "欄位A": {{"lower": 數值, "upper": 數值}} }}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"[ERROR] AI 批次推算失敗: {e}")
        return {}

# ==========================================
# 3. GUI 應用程式類別
# ==========================================
class DPDataProcessorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI 賦能 - 差分隱私資料預處理工具")
        self.geometry("1000x750")
        self.data_files = []
        self.desc_file = ""
        self.df = None
        self.build_ui()

    def build_ui(self):
        # 左側控制面板 (加寬以容納更多選項)
        self.frame_left = ctk.CTkFrame(self, width=300)
        self.frame_left.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_left, text="📂 資料載入", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.btn_load_data = ctk.CTkButton(self.frame_left, text="1. 載入資料檔 (多選CSV)", command=self.load_data_files)
        self.btn_load_data.pack(pady=5, fill="x", padx=10)
        self.btn_load_desc = ctk.CTkButton(self.frame_left, text="2. 載入描述檔 (.names)", command=self.load_desc_file)
        self.btn_load_desc.pack(pady=5, fill="x", padx=10)

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

        self.btn_save = ctk.CTkButton(self.frame_left, text="💾 儲存輸出資料", command=self.save_data, state="disabled")
        self.btn_save.pack(pady=5, fill="x", padx=10)

        # 右側日誌區
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.log_box = ctk.CTkTextbox(self.frame_right, width=500, height=300)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    def load_data_files(self):
        files = filedialog.askopenfilenames(title="選擇資料檔")
        if files:
            self.data_files = list(files)
            self.log(f"[載入] 已選擇 {len(self.data_files)} 個資料檔。")

    def load_desc_file(self):
        file = filedialog.askopenfilename(title="選擇描述檔")
        if file:
            self.desc_file = file
            self.log(f"[載入] 已選擇描述檔: {os.path.basename(file)}")

    def start_processing(self):
        if not self.data_files:
            messagebox.showerror("錯誤", "請先載入至少一個資料檔！")
            return
        # 測試 API Key 是否有效
        try:
            setup_genai()
        except Exception as e:
            messagebox.showerror("API 錯誤", str(e))
            self.log(f"[錯誤] {str(e)}")
            return
        threading.Thread(target=self.process_pipeline, daemon=True).start()

    def process_pipeline(self):
        try:
            self.btn_process.configure(state="disabled")
            self.log("=" * 50)
            self.log("[開始] 啟動客製化預處理 Pipeline...")

            # 初始化預設狀態
            has_header = True # 預設假設有表頭
            cat_mappings = {}

            # --- Step 1: AI 預判斷表頭與類別 ---
            if self.chk_ai_profile.get():
                first_file = self.data_files[0]
                self.log(f"[Step 1] 執行 AI 探勘: {os.path.basename(first_file)}")
                sample_df = pd.read_csv(first_file, header=None, nrows=5)
                sample_csv_text = sample_df.to_csv(index=False, header=False)
                
                has_header, cat_mappings = analyze_data_structure_with_gemini(sample_csv_text)
                self.log(f"  -> 判斷是否有表頭: {has_header}")
                if cat_mappings: self.log(f"  -> 發現類別對應: {cat_mappings}")
            else:
                self.log("[跳過 Step 1] 未啟用 AI 探勘，預設當作『有表頭』處理。")

            # --- Step 2: 讀取與合併 ---
            if self.chk_merge.get():
                self.log("[Step 2] 執行資料讀取與合併...")
                df_list = []
                for f in self.data_files:
                    read_header = 0 if has_header else None
                    df_list.append(pd.read_csv(f, header=read_header, skipinitialspace=True))
                
                if len(df_list) > 1:
                    self.df = pd.concat(df_list, ignore_index=True)
                    self.log(f"  -> 成功合併 {len(df_list)} 個檔案，總筆數: {len(self.df)}")
                else:
                    self.df = df_list[0]
            else:
                self.log("[Step 2] 僅讀取首個檔案 (未啟用合併)。")
                read_header = 0 if has_header else None
                self.df = pd.read_csv(self.data_files[0], header=read_header, skipinitialspace=True)

            # --- Step 3: AI 補齊缺失欄位名 ---
            if self.chk_fill_cols.get():
                if not has_header:
                    self.log("[Step 3] 執行 AI 補齊欄位名...")
                    if self.desc_file:
                        with open(self.desc_file, 'r', encoding='utf-8', errors='ignore') as f:
                            columns = extract_columns_with_gemini(f.read())
                        if columns and len(columns) == len(self.df.columns):
                            self.df.columns = columns
                            self.log(f"  -> 成功套用: {columns}")
                        elif columns and len(self.df.columns) - len(columns) == 1:
                            columns.append("target_label")
                            self.df.columns = columns
                            self.log("  -> 欄位差1，自動補上 'target_label'。")
                    else:
                        self.log("  -> 未提供描述檔，使用預設流水號 col_0, col_1...")
                        self.df.columns = [f"col_{i}" for i in range(len(self.df.columns))]
                else:
                    self.log("[跳過 Step 3] 資料已有表頭，無需補齊。")
            else:
                self.log("[跳過 Step 3] 未啟用自動補齊欄位名。")

            # --- Step 4: AI 類別欄位轉換數值 ---
            if self.chk_cat_encode.get():
                if cat_mappings:
                    self.log("[Step 4] 執行類別欄位轉換數值...")
                    for col_key, mapping in cat_mappings.items():
                        target_col = col_key
                        if not has_header:
                            try: target_col = self.df.columns[int(col_key)]
                            except: pass
                        
                        if target_col in self.df.columns:
                            self.df[target_col] = self.df[target_col].map(mapping).fillna(self.df[target_col])
                            self.log(f"  -> 成功轉換欄位: '{target_col}'")
                else:
                    self.log("[跳過 Step 4] 無需要轉換的類別欄位。")
            else:
                self.log("[跳過 Step 4] 未啟用類別轉換。")

            # --- Step 5: 清除多餘總和/統計列 ---
            if self.chk_clean_summary.get():
                self.log("[Step 5] 執行清除多餘統計列...")
                initial_len = len(self.df)
                mask = self.df.astype(str).apply(lambda x: x.str.contains('total|總計|summary', case=False, na=False)).any(axis=1)
                self.df = self.df[~mask]
                self.log(f"  -> 移除了 {initial_len - len(self.df)} 筆可疑資料。")
            else:
                self.log("[跳過 Step 5] 未啟用清除多餘資料。")

            # --- Step 6: 處理空值 ---
            if self.chk_handle_nan.get():
                nan_count = self.df.isna().sum().sum()
                if nan_count > 0:
                    self.log(f"[Step 6] 填補了 {nan_count} 個空值為 0。")
                    self.df = self.df.fillna(0)
                else:
                    self.log("[跳過 Step 6] 資料無空值。")
            else:
                self.log("[跳過 Step 6] 未啟用空值處理。")

            # --- Step 7: DP 異常值截斷 (AI批次) ---
            if self.chk_dp_clip.get():
                self.log("[Step 7] 執行 DP 異常值截斷 (準備批次分析)...")
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns
                cols_to_infer = {}

                for col in numeric_cols:
                    q25, q75 = self.df[col].quantile(0.25), self.df[col].quantile(0.75)
                    iqr = q75 - q25
                    max_val, min_val = self.df[col].max(), self.df[col].min()
                    
                    if max_val > q75 + 1.5 * iqr and iqr > 0:
                        cols_to_infer[col] = {
                            'min': float(min_val), 'max': float(max_val),
                            'mean': float(self.df[col].mean()), 
                            'q25': float(q25), 'q75': float(q75)
                        }

                if cols_to_infer:
                    self.log(f"  -> 批次發送 {len(cols_to_infer)} 個欄位給 AI 推算上下限...")
                    batch_bounds = infer_bounds_batch_with_gemini(cols_to_infer)
                    for col, bounds in batch_bounds.items():
                        if col in self.df.columns and "lower" in bounds and "upper" in bounds:
                            self.df[col] = self.df[col].clip(lower=bounds["lower"], upper=bounds["upper"])
                            self.log(f"  -> [截斷] '{col}' 範圍限制在 [{bounds['lower']}, {bounds['upper']}]")
                else:
                    self.log("  -> 資料分佈平穩，無需進行截斷。")
            else:
                self.log("[跳過 Step 7] 未啟用 DP 截斷。")

            self.log("=" * 50)
            self.log("[完成] Pipeline 執行完畢！可點擊儲存。")
            self.btn_save.configure(state="normal")
            
        except Exception as e:
            self.log(f"[嚴重錯誤] Pipeline 中斷: {str(e)}")
        finally:
            self.btn_process.configure(state="normal")

    def save_data(self):
        if self.df is not None:
            save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if save_path:
                self.df.to_csv(save_path, index=False)
                self.log(f"[儲存] 檔案已存至: {save_path}")

if __name__ == "__main__":
    app = DPDataProcessorApp()
    app.mainloop()
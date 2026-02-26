# data_processor.py
import pandas as pd
import numpy as np
import os
from ai_helper import (
    analyze_data_structure_with_gemini, 
    extract_columns_with_gemini, 
    infer_bounds_batch_with_gemini
)

class DataPipeline:
    def __init__(self, log_callback):
        self.log = log_callback
        self.df = None

    def run(self, data_files, desc_file, options):
        """執行資料預處理流程"""
        try:
            self.log("=" * 50)
            self.log("[開始] 啟動客製化預處理 Pipeline...")

            # --- Step 0: 檢查並轉換 .data 檔案 ---
            processed_data_files = []
            for f in data_files:
                if f.lower().endswith('.data'):
                    self.log(f"[轉檔] 偵測到 .data 檔案: {os.path.basename(f)}，轉換中...")
                    try:
                        temp_df = pd.read_csv(f, header=None, skipinitialspace=True)
                        new_path = f.rsplit('.', 1)[0] + "_converted.csv"
                        temp_df.to_csv(new_path, index=False, header=False)
                        processed_data_files.append(new_path)
                        self.log(f"  -> 轉換成功: {os.path.basename(new_path)}")
                    except Exception as e:
                        self.log(f"  -> 轉換失敗 ({e})，嘗試直接讀取原檔。")
                        processed_data_files.append(f)
                else:
                    processed_data_files.append(f)
            
            data_files = processed_data_files

            has_header = True
            cat_mappings = {}

            # --- Step 1: AI 預判斷表頭與類別 ---
            if options.get("ai_profile"):
                first_file = data_files[0]
                self.log(f"[Step 1] 執行 AI 探勘: {os.path.basename(first_file)}")
                sample_df = pd.read_csv(first_file, header=None, nrows=5)
                sample_csv_text = sample_df.to_csv(index=False, header=False)
                
                has_header, cat_mappings = analyze_data_structure_with_gemini(sample_csv_text)
                self.log(f"  -> 判斷是否有表頭: {has_header}")
                if cat_mappings: self.log(f"  -> 發現類別對應: {cat_mappings}")
            else:
                self.log("[跳過 Step 1] 未啟用 AI 探勘，預設當作『有表頭』。")

            # --- Step 2: 讀取與合併 ---
            if options.get("merge"):
                self.log("[Step 2] 執行資料讀取與合併...")
                df_list = []
                for f in data_files:
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
                self.df = pd.read_csv(data_files[0], header=read_header, skipinitialspace=True)

            # --- Step 3: AI 補齊缺失欄位名 ---
            if options.get("fill_cols"):
                if not has_header:
                    self.log("[Step 3] 執行 AI 補齊欄位名...")
                    if desc_file:
                        with open(desc_file, 'r', encoding='utf-8', errors='ignore') as f:
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
            if options.get("cat_encode"):
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
            if options.get("clean_summary"):
                self.log("[Step 5] 執行清除多餘統計列...")
                initial_len = len(self.df)
                mask = self.df.astype(str).apply(lambda x: x.str.contains('total|總計|summary', case=False, na=False)).any(axis=1)
                self.df = self.df[~mask]
                self.log(f"  -> 移除了 {initial_len - len(self.df)} 筆資料。")
            else:
                self.log("[跳過 Step 5] 未啟用清除多餘資料。")

            # --- Step 6: 處理空值 ---
            if options.get("handle_nan"):
                nan_count = self.df.isna().sum().sum()
                if nan_count > 0:
                    self.log(f"[Step 6] 填補了 {nan_count} 個空值為 0。")
                    self.df = self.df.fillna(0)
                else:
                    self.log("[跳過 Step 6] 資料無空值。")
            else:
                self.log("[跳過 Step 6] 未啟用空值處理。")

            # --- Step 7: DP 異常值截斷 (AI批次) ---
            if options.get("dp_clip"):
                self.log("[Step 7] 執行 DP 異常值截斷 (批次分析)...")
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
                            self.log(f"  -> [截斷] '{col}' 限制在 [{bounds['lower']}, {bounds['upper']}]")
                else:
                    self.log("  -> 資料分佈平穩，無需截斷。")
            else:
                self.log("[跳過 Step 7] 未啟用 DP 截斷。")

            self.log("=" * 50)
            self.log("[完成] Pipeline 執行完畢！")
            return True, self.df

        except Exception as e:
            self.log(f"[嚴重錯誤] Pipeline 中斷: {str(e)}")
            return False, None
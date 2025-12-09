import customtkinter as ctk
from tkinter import ttk
import pandas as pd

class DataPreviewTable(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # 設定 Grid 佈局權重，讓表格(row=0, col=0)可以跟著視窗縮放
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. 建立 Treeview (表格本體)
        self.tree = ttk.Treeview(self, selectmode="none")
        
        # 2. 建立垂直捲軸 (Vertical Scrollbar)
        self.v_scroll = ctk.CTkScrollbar(self, orientation="vertical", command=self.tree.yview)
        
        # 3. 【新增】建立水平捲軸 (Horizontal Scrollbar)
        self.h_scroll = ctk.CTkScrollbar(self, orientation="horizontal", command=self.tree.xview)

        # 4. 連結捲軸到表格
        self.tree.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        # 5. 使用 Grid 進行精準排版
        # 表格放在 (0, 0)，佔滿空間
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=(5, 0))
        # 垂直捲軸放在右邊 (0, 1)
        self.v_scroll.grid(row=0, column=1, sticky="ns", padx=5, pady=(5, 0))
        # 水平捲軸放在下面 (1, 0)
        self.h_scroll.grid(row=1, column=0, sticky="ew", padx=(5, 0), pady=5)

        # 6. 設定表格樣式
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview", 
                             background="#2b2b2b", 
                             foreground="white", 
                             fieldbackground="#2b2b2b", 
                             rowheight=25)
        self.style.configure("Treeview.Heading", 
                             background="#1f538d", 
                             foreground="white", 
                             font=('Arial', 10, 'bold'))
        self.style.map("Treeview", background=[('selected', '#1f538d')])

    def update_data(self, file_path):
        """
        讀取檔案並更新表格內容
        """
        try:
            # 根據副檔名讀取
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            else:
                return False, "不支援的檔案格式"

            # 【新增】檢查是否為空資料
            if df.empty:
                return False, "錯誤：檔案內沒有資料 (Empty DataFrame)"

            # 清空舊資料
            self.tree.delete(*self.tree.get_children())

            # 設定欄位 (Columns)
            columns = list(df.columns)
            self.tree["columns"] = columns
            self.tree["show"] = "headings"

            # 設定欄位寬度：這裡設定 minwidth 避免縮太小，並給一個預設寬度
            for col in columns:
                self.tree.heading(col, text=col)
                # minwidth=100 保證不會被壓扁到看不到字
                self.tree.column(col, width=120, minwidth=100, anchor="center")

            # 插入資料 (Rows) - 取前 15 筆
            # Pandas 的 head(n) 很安全，如果資料只有 5 筆，它就只會回傳 5 筆，不會報錯
            preview_df = df.head(15)
            for index, row in preview_df.iterrows():
                # 處理可能的空值 (NaN)，轉成空字串顯示，比較美觀
                safe_values = ["" if pd.isna(x) else x for x in list(row)]
                self.tree.insert("", "end", values=safe_values)
            
            return True, f"成功載入：{len(df)} 筆資料，欄位：{len(columns)} 個"

        except pd.errors.EmptyDataError:
            return False, "錯誤：檔案完全空白或格式損毀"
        except Exception as e:
            return False, f"讀取錯誤：{str(e)}"
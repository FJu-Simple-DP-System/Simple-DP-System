import customtkinter as ctk
from tkinter import filedialog

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from diffprivlib.mechanisms import Laplace, GaussianAnalytic


class ResultPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # 外觀
        self.configure(fg_color=("gray90", "gray20"), corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # 讓圖表區可以伸縮一點

        # 狀態
        self.current_result = None   # engine 回傳的 payload
        self.source_df = None        # 原始 DataFrame（給下載用）
        self.figure = None
        self.canvas = None
        self.collapsed = False       # 是否為收合狀態

        # 1. 標題 + 收合按鈕列
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            header_frame, text="運算結果", font=("Arial", 18, "bold")
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.btn_toggle = ctk.CTkButton(
            header_frame,
            text="收合",
            width=70,
            height=26,
            fg_color="#555555",
            hover_color="#777777",
            command=self._toggle_collapse,
        )
        self.btn_toggle.grid(row=0, column=1, sticky="e")

        # 2. 數值 / 說明文字
        self.lbl_result_text = ctk.CTkLabel(
            self,
            text="等待執行...",
            font=("Arial", 16),
            text_color="gray",
            wraplength=600,
            justify="left",
        )
        self.lbl_result_text.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        # 3. 圖表顯示區（可捲動）
        self.chart_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=220,  # 固定高度；超過就用捲軸捲
        )
        self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.chart_frame.grid_remove()  # 預設先隱藏，直到有圖表

        # 4. 按鈕列（下載）
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, sticky="e", padx=20, pady=(10, 15))

        self.btn_download = ctk.CTkButton(
            self.btn_frame,
            text="下載結果 (.csv)",
            state="disabled",  # 有結果才能按
            fg_color="#3B8ED0",
            width=120,
            command=self._on_download_click,
        )
        self.btn_download.pack(side="right", padx=(10, 0))

    # ----------------- 對外 API -----------------

    def show_loading(self):
        """顯示處理中狀態"""
        self.current_result = None
        self.lbl_result_text.configure(
            text="正在進行差分隱私運算... (請稍候)", text_color="#E67E22"
        )
        self._clear_chart()
        self.chart_frame.grid_remove()
        self.btn_download.configure(state="disabled")
        # 若之前是收合狀態，可以選擇自動展開
        if self.collapsed:
            self._toggle_collapse(force_expand=True)
        self.update_idletasks()

    def update_result(self, payload: dict, result_text: str, source_df: pd.DataFrame | None = None):
        """
        從 MainWindow 呼叫：
        - payload: engine 回傳的 result['result']
        - result_text: 要顯示在文字區的說明文字
        - source_df: 原始完整 DataFrame（用來做「整欄加噪後下載」）
        """
        self.current_result = payload
        if source_df is not None:
            self.source_df = source_df

        # 顯示文字
        self.lbl_result_text.configure(text=result_text, text_color=("black", "white"))

        # 若是 histogram 則畫圖
        query = payload.get("query")
        if query == "histogram":
            hist = payload.get("hist")
            bin_edges = payload.get("bin_edges")
            if hist is not None and bin_edges is not None:
                self._plot_histogram(hist, bin_edges)
        else:
            self._clear_chart()
            self.chart_frame.grid_remove()

        # 有結果就可以下載
        self.btn_download.configure(state="normal")

        # 若之前是收合，可以選擇自動展開
        if self.collapsed:
            self._toggle_collapse(force_expand=True)

    def set_source_df(self, df: pd.DataFrame):
        """如需先單獨設定 DataFrame 也可以用這個"""
        self.source_df = df

    def reset(self):
        """重置回初始狀態"""
        self.current_result = None
        self.source_df = None
        self.lbl_result_text.configure(text="等待執行...", text_color="gray")
        self._clear_chart()
        self.chart_frame.grid_remove()
        self.btn_download.configure(state="disabled")

        # 收合與否保留原狀；如果你想 reset 時也順便收合，可以取消註解：
        # if not self.collapsed:
        #     self._toggle_collapse()

    # ----------------- 收合 / 展開 -----------------

    def _toggle_collapse(self, force_expand: bool = False):
        """切換收合 / 展開結果內容"""
        if force_expand:
            target_collapsed = False
        else:
            target_collapsed = not self.collapsed

        self.collapsed = target_collapsed

        if self.collapsed:
            # 收合：只留標題列，隱藏文字 + 圖表
            self.lbl_result_text.grid_remove()
            self.chart_frame.grid_remove()
            self.btn_toggle.configure(text="展開")
        else:
            # 展開：把元件都顯示回來
            self.lbl_result_text.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
            # 有圖才顯示圖表區
            if self.canvas is not None:
                self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
            # self.btn_frame.grid(row=3, column=0, sticky="e", padx=20, pady=(10, 15))
            # self.btn_toggle.configure(text="收合")

    # ----------------- 畫圖相關 -----------------

    def _clear_chart(self):
        """清除舊的 Matplotlib 圖"""
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        self.figure = None

    def _plot_histogram(self, hist, bin_edges):
        """用 Matplotlib 畫出 DP noisy histogram"""
        self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # 先清除舊圖
        self._clear_chart()

        hist = list(hist)
        bin_edges = list(bin_edges)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        if len(bin_edges) == len(hist) + 1:
            centers = []
            widths = []
            for i in range(len(hist)):
                left = bin_edges[i]
                right = bin_edges[i + 1]
                centers.append((left + right) / 2)
                widths.append(right - left)
        else:
            centers = list(range(len(hist)))
            widths = 0.8

        ax.bar(centers, hist, width=widths)
        ax.set_xlabel("Value")
        ax.set_ylabel("Noisy count")
        ax.set_title("Differentially Private Histogram")
        fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.figure = fig

    # ----------------- 下載整欄加噪後的資料集 -----------------

    def _on_download_click(self):
        """
        將目前設定下「加了雜訊的完整資料集」輸出成 .csv：
        - 只針對 current_result['column'] 那一欄加噪
        - 覆蓋原欄位（不加 *_dp）
        """
        if self.current_result is None or self.source_df is None:
            return

        file_path = filedialog.asksaveasfilename(
            title="儲存加噪後資料集為 CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not file_path:
            return  # 使用者取消

        query = self.current_result.get("query")
        eps = self.current_result.get("epsilon")
        mech = self.current_result.get("mechanism")
        bounds = self.current_result.get("bounds")
        col = self.current_result.get("column")

        if col is None or bounds is None:
            return

        lower, upper = bounds
        df = self.source_df.copy()

        # 只處理選定欄位，其他欄原封不動
        series = pd.to_numeric(df[col], errors="coerce")
        clipped = series.clip(lower, upper)

        # 對單一值的敏感度（這裡用 max-min）
        sensitivity = float(upper) - float(lower)
        mech_key = (mech or "").lower()

        if "laplace" in mech_key:
            mechanism = Laplace(epsilon=float(eps), sensitivity=sensitivity)
        elif "gaussian" in mech_key or "高斯" in mech_key:
            delta = self.current_result.get("delta", 1e-5)
            mechanism = GaussianAnalytic(
                epsilon=float(eps),
                delta=float(delta),
                sensitivity=sensitivity,
            )
        else:
            return

        noisy_values = clipped.copy()

        for idx, val in clipped.items():
            if pd.isna(val):
                noisy_values.at[idx] = pd.NA
            else:
                noised = mechanism.randomise(float(val))
                # 若你希望結果被夾在 bounds 內，就保留下面這行：
                # noised = max(lower, min(upper, noised))
                noisy_values.at[idx] = noised

        # 覆蓋原欄位（不新增 *_dp）
        df[col] = noisy_values

        df.to_csv(file_path, index=False)

# 用於集中管理 GUI 的所有使用者設定參數

class DPSettings:
    """
    統一記錄使用者在 GUI 選擇的差分隱私相關設定。
    MainWindow 與其他模組都可以從這裡讀取或更新參數，不用互相耦合。
    """

    def __init__(self):
        # 初始預設值（也與 GUI 預設同步）
        self.epsilon = 1.0
        self.mechanism = "Laplace 機制"
        self.delta = 1e-5  # 【新增】預設 Delta 值
        self.query = "平均值 (Mean)"
        self.column = None   # 需檔案載入後才能填入
        self.sensitivity_min = None
        self.sensitivity_max = None

    # ============
    # Setter 區段
    # ============

    def set_epsilon(self, value: float):
        self.epsilon = float(value)

    def set_mechanism(self, mech: str):
        self.mechanism = mech

    def set_delta(self, value: float):  # 【新增】
        self.delta = float(value)

    def set_query(self, query: str):
        self.query = query

    def set_column(self, col: str):
        self.column = col

    def set_sensitivity(self, min_val: str, max_val: str):
        self.sensitivity_min = min_val
        self.sensitivity_max = max_val

    # ============
    # Getter 區段
    # ============

    def get_all(self):
        """一次回傳所有設定（給 DP 運算用）"""
        return {
            "epsilon": self.epsilon,
            "mechanism": self.mechanism,
            "delta": self.delta,        # 【新增】
            "query": self.query,
            "column": self.column,
            "sensitivity_min": self.sensitivity_min,
            "sensitivity_max": self.sensitivity_max
        }

    def __repr__(self):
        return f"<DPSettings {self.get_all()}>"



# 單例化：全系統共用一份設定
dp_settings = DPSettings()

import numpy as np
import pandas as pd
import diffprivlib.tools as dpt
from diffprivlib.mechanisms import GaussianAnalytic
from src.core.elements import dp_settings


def _normalize_mechanism_name(mech_text: str) -> str:
    """
    把 GUI 裡顯示的文字 (例如 'Laplace 機制', '高斯機制', 'Gaussian') 
    轉成內部統一使用的 key：'laplace' 或 'gaussian'
    """
    text = (mech_text or "").lower()
    if "laplace" in text:
        return "laplace"
    if "gaussian" in text or "高斯" in text:
        return "gaussian"
    # 預設用 laplace
    return "laplace"


def _normalize_query_name(query_text: str) -> str:
    """
    把 GUI 裡顯示的文字 (例如 '平均值 (Mean)', '總和 (Sum)') 
    轉成內部統一使用的 key：'mean' / 'sum' / 'count' / 'histogram'
    """
    text = (query_text or "").lower()
    if "mean" in text or "平均" in text:
        return "mean"
    if "sum" in text or "總和" in text:
        return "sum"
    if "count" in text or "計數" in text:
        return "count"
    if "hist" in text or "直方圖" in text:
        return "histogram"
    # 預設
    return "mean"


def run_dp_from_settings(df: pd.DataFrame):
    """
    使用目前 dp_settings 裡的設定，對 df 做差分隱私統計。
    
    回傳格式：
        {
            "ok": True/False,
            "message": "說明文字",
            "result":  {... 差分隱私結果 ...} 或 None
        }
    """
    # 1. 讀取設定
    cfg = dp_settings.get_all()
    epsilon = float(cfg["epsilon"])
    mech_key = _normalize_mechanism_name(cfg["mechanism"])
    query_key = _normalize_query_name(cfg["query"])
    column = cfg["column"]
    min_str = cfg["sensitivity_min"]
    max_str = cfg["sensitivity_max"]
    try:
        delta = float(cfg.get("delta", 1e-5))
    except (ValueError, TypeError):
        delta = 1e-5

    # 2. 基本檢查
    if column is None:
        return {
            "ok": False,
            "message": "請先在左側選擇目標欄位 (Column)",
            "result": None
        }

    if column not in df.columns:
        return {
            "ok": False,
            "message": f"找不到欄位：{column}",
            "result": None
        }

    try:
        data_min = float(min_str)
        data_max = float(max_str)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "message": "請正確輸入資料邊界 Min / Max（需為數值）",
            "result": None
        }

    if data_min >= data_max:
        return {
            "ok": False,
            "message": f"資料邊界不合法：Min({data_min}) 需小於 Max({data_max})",
            "result": None
        }

    # 3. 取出欄位資料，轉成數值並 clip 在 [min, max] 範圍內
    try:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
    except Exception as e:
        return {
            "ok": False,
            "message": f"欄位轉換數值失敗：{e}",
            "result": None
        }

    if series.empty:
        return {
            "ok": False,
            "message": "目標欄位沒有有效的數值資料",
            "result": None
        }

    arr = series.to_numpy()
    clipped = np.clip(arr, data_min, data_max)

    # 4. 決定要使用的機制與統計操作
    # ----------------------------------------------------
    # Laplace：用 diffprivlib.tools
    # Gaussian：先算非 DP 統計，再用 Gaussian 機制加噪
    # ----------------------------------------------------

    # 統一回傳的結果容器
    result_payload = {
        "epsilon": epsilon,
        "mechanism": mech_key,
        "query": query_key,
        "column": column,
        "bounds": (data_min, data_max)
    }

    # ========== Laplace 機制 ==========
    if mech_key == "laplace":
        try:
            if query_key == "mean":
                value = dpt.mean(
                    clipped,
                    epsilon=epsilon,
                    bounds=(data_min, data_max)
                )
                result_payload["value"] = float(value)

            elif query_key == "sum":
                value = dpt.sum(
                    clipped,
                    epsilon=epsilon,
                    bounds=(data_min, data_max)
                )
                result_payload["value"] = float(value)

            elif query_key == "count":
                # 計數可以用全為 1 的陣列配合 count_nonzero
                ones = np.ones_like(clipped)
                value = dpt.count_nonzero(
                    ones,
                    epsilon=epsilon
                )
                result_payload["value"] = float(value)

            elif query_key == "histogram":
                # bins 這裡先寫死 10，之後你可以改成由 GUI 設定
                bins = 10
                hist, bin_edges = dpt.histogram(
                    clipped,
                    epsilon=epsilon,
                    bins=bins,
                    range=(data_min, data_max)
                )
                result_payload["hist"] = hist
                result_payload["bin_edges"] = bin_edges
            else:
                return {
                    "ok": False,
                    "message": f"不支援的統計操作：{query_key}",
                    "result": None
                }

        except Exception as e:
            return {
                "ok": False,
                "message": f"差分隱私運算失敗（Laplace）：{e}",
                "result": None
            }

    # ========== Gaussian 機制 ==========
    elif mech_key == "gaussian":
        result_payload["delta"] = delta

        try:
            if query_key == "mean":
                # mean 的 sensitivity = (max - min) / n
                n = clipped.size
                sensitivity = (data_max - data_min) / n
                base_value = float(clipped.mean())

            elif query_key == "sum":
                # sum 的 sensitivity = (max - min)
                sensitivity = (data_max - data_min)
                base_value = float(clipped.sum())

            elif query_key == "count":
                sensitivity = 1.0
                base_value = float(clipped.size)

            elif query_key == "histogram":
                # 先算一般 histogram，再對每個 bin 的 count 加 Gaussian 雜訊
                bins = 10
                counts, bin_edges = np.histogram(
                    clipped,
                    bins=bins,
                    range=(data_min, data_max)
                )
                sensitivity = 1.0

                mech = GaussianAnalytic(
                    epsilon=epsilon,
                    delta=delta,
                    sensitivity=sensitivity
                )

                noisy_counts = np.array([
                    mech.randomise(float(c)) for c in counts
                ])

                result_payload["hist"] = noisy_counts
                result_payload["bin_edges"] = bin_edges

                return {
                    "ok": True,
                    "message": "Gaussian 機制直方圖運算完成",
                    "result": result_payload
                }

            else:
                return {
                    "ok": False,
                    "message": f"不支援的統計操作：{query_key}",
                    "result": None
                }

            mech = GaussianAnalytic(
                epsilon=epsilon,
                delta=delta,
                sensitivity=sensitivity
            )
            noisy_value = mech.randomise(base_value)
            result_payload["value"] = float(noisy_value)

        except Exception as e:
            return {
                "ok": False,
                "message": f"差分隱私運算失敗（Gaussian）：{e}",
                "result": None
            }

    else:
        return {
            "ok": False,
            "message": f"不支援的機制：{mech_key}",
            "result": None
        }

    # 正常結束
    return {
        "ok": True,
        "message": "差分隱私運算完成",
        "result": result_payload
    }

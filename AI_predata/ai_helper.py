# ai_helper.py
import google.generativeai as genai
import json
import config

def setup_genai():
    """初始化並驗證 Gemini API"""
    if not config.API_KEY or config.API_KEY == "YOUR_API_KEY_HERE":
        raise ValueError("請先在 config.py 中設定有效的 Google API Key！")
    genai.configure(api_key=config.API_KEY)

def analyze_data_structure_with_gemini(sample_csv_text: str):
    """分析 CSV 前 5 筆紀錄，判斷表頭與類別"""
    setup_genai()
    generation_config = {"temperature": 0.0, "response_mime_type": "application/json"}
    model = genai.GenerativeModel(config.MODEL_NAME, generation_config=generation_config)
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
        return True, {} 

def extract_columns_with_gemini(names_content: str):
    """依照描述檔提取欄位名稱"""
    setup_genai()
    generation_config = {"temperature": 0.1, "response_mime_type": "application/json"}
    model = genai.GenerativeModel(config.MODEL_NAME, generation_config=generation_config)
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
    """一次性讓 AI 推算多個欄位的 Clipping 上下限"""
    setup_genai()
    generation_config = {"temperature": 0.1, "response_mime_type": "application/json"}
    model = genai.GenerativeModel(config.MODEL_NAME, generation_config=generation_config)
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
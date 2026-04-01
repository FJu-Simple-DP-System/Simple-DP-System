# ai_helper.py
import json
import config

# ==========================================
# 1. 錯誤翻譯與字串處理工具
# ==========================================
def _simplify_error(e: Exception) -> str:
    """將冗長或英文的 API 錯誤轉換為簡潔的中文提示 (供 GUI 顯示)"""
    err_msg = str(e).lower()
    if "api_key_invalid" in err_msg or "api key" in err_msg or "authentication" in err_msg or "incorrect api key" in err_msg:
        return "API 金鑰無效或未設定，請檢查您的設定。"
    elif "quota" in err_msg or "429" in err_msg or "exhausted" in err_msg or "insufficient_quota" in err_msg:
        return "API 請求次數達上限，或免費額度已耗盡。"
    elif "timeout" in err_msg or "deadline" in err_msg:
        return "網路連線逾時，請檢查連線狀態。"
    elif "503" in err_msg or "500" in err_msg or "overloaded" in err_msg:
        return "AI 伺服器暫時無法回應，請稍後再試。"
    elif "connection refused" in err_msg or "target machine actively refused it" in err_msg:
        return "無法連線到本地模型，請確認 Ollama 是否已啟動。" # <--- 新增
    elif "not found" in err_msg or "404" in err_msg:
        return "找不到指定的模型，請確認該模型是否已下載 (例如: ollama pull llama3)。"
    else:
        return f"連線或解析錯誤 ({type(e).__name__})，請確認網路或 API 狀態。"

def _clean_json_string(raw_text: str) -> str:
    """清理 AI 回傳可能帶有的 Markdown 標籤 (例如 ```json ... ```)"""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# ==========================================
# 2. 定義統一的 AI 策略介面與實作 (多模型支援)
# ==========================================
class BaseAIProvider:
    def generate_json(self, prompt: str, temperature: float = 0.1) -> str:
        """所有 AI 模型都必須實作這個方法，並回傳 JSON 格式的字串"""
        raise NotImplementedError

class GeminiProvider(BaseAIProvider):
    def generate_json(self, prompt: str, temperature: float = 0.1) -> str:
        # 將 import 放在內部，避免使用者沒裝套件時整個程式崩潰
        import google.generativeai as genai
        
        api_key = getattr(config, "API_KEY", "")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("API_KEY_INVALID: Gemini API 金鑰未設定。")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            getattr(config, "MODEL_NAME", "gemini-2.5-flash"), 
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        return response.text

class OpenAIProvider(BaseAIProvider):
    def generate_json(self, prompt: str, temperature: float = 0.1) -> str:
        import openai
        
        api_key = getattr(config, "OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("API_KEY_INVALID: OpenAI API 金鑰未設定。")
            
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 預設使用 OpenAI 輕量級模型
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a helpful data processing assistant. Always output strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

class ClaudeProvider(BaseAIProvider):
    def generate_json(self, prompt: str, temperature: float = 0.1) -> str:
        import anthropic
        
        api_key = getattr(config, "CLAUDE_API_KEY", "")
        if not api_key:
            raise ValueError("API_KEY_INVALID: Claude API 金鑰未設定。")
            
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307", # 預設使用 Claude 輕量級模型
            max_tokens=1024,
            temperature=temperature,
            system="You are a data processing assistant. You MUST output ONLY valid JSON without any markdown formatting or explanations.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class OllamaProvider(BaseAIProvider):
    def generate_json(self, prompt: str, temperature: float = 0.1) -> str:
        import openai
        
        model_name = getattr(config, "OLLAMA_MODEL", "llama3")
        if not model_name:
            model_name = "llama3"
            
        # 關鍵：將 Base URL 指向本地 Ollama 服務的 OpenAI 相容端點
        client = openai.OpenAI(
            base_url="http://localhost:11434/v1", 
            api_key="ollama"  # 本地不需要真 Key，但 SDK 規定不能為空
        )
        response = client.chat.completions.create(
            model=model_name,
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a helpful data processing assistant. Always output strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

def get_ai_provider() -> BaseAIProvider:
    """根據 config 的設定，實例化對應的 AI 供應商"""
    active_ai = getattr(config, "ACTIVE_AI", "Gemini")
    
    if active_ai == "OpenAI":
        return OpenAIProvider()
    elif active_ai == "Claude":
        return ClaudeProvider()
    elif active_ai == "Ollama (本地端)":  # <--- 新增
        return OllamaProvider()
    else:
        return GeminiProvider()

# ==========================================
# 3. 業務邏輯 (資料預處理呼叫點)
# ==========================================
def analyze_data_structure_with_gemini(sample_csv_text: str, log_func=print):
    """分析 CSV 前 5 筆紀錄，判斷表頭與類別"""
    prompt = f"""
    任務：分析以下 CSV 資料的前 5 筆紀錄，判斷其結構。
    CSV 內容：\n---\n{sample_csv_text}\n---\n
    請回傳嚴格的 JSON 格式：
    1. "has_header": true 或 false (第一列是否為欄位名稱)。
    2. "categorical_mappings": 若有字串類別欄位(如性別)，請建立轉數字(0,1,2...)的字典。如 {{"Gender": {{"M": 0, "F": 1}}}}。沒有則回傳 {{}}。
    """
    try:
        provider = get_ai_provider()
        response_text = provider.generate_json(prompt, temperature=0.0)
        clean_json = _clean_json_string(response_text)
        result = json.loads(clean_json)
        return result.get("has_header", False), result.get("categorical_mappings", {})
    except Exception as e:
        print(f"========== [終端機詳細錯誤] AI 結構解析 ==========\n{str(e)}\n================================================")
        log_func(f"[錯誤] AI 判斷表頭失敗：{_simplify_error(e)}")
        return True, {} 

def extract_columns_with_gemini(names_content: str, log_func=print):
    """依照描述檔提取欄位名稱"""
    prompt = f"""
    任務：從以下的資料集描述文件中提取所有的「欄位名稱 (Column Names)」。
    文件內容：\n---\n{names_content}\n---\n
    規則：回傳 JSON Array (List of strings)。例如: ["id", "age", "target"]
    """
    try:
        provider = get_ai_provider()
        response_text = provider.generate_json(prompt, temperature=0.1)
        clean_json = _clean_json_string(response_text)
        return json.loads(clean_json)
    except Exception as e:
        print(f"========== [終端機詳細錯誤] AI 欄位提取 ==========\n{str(e)}\n================================================")
        log_func(f"[錯誤] AI 提取欄位名稱失敗：{_simplify_error(e)}")
        return []

def infer_bounds_batch_with_gemini(stats_dict, log_func=print):
    """一次性讓 AI 推算多個欄位的 Clipping 上下限"""
    prompt = f"""
    任務：為了差分隱私 (Differential Privacy)，需要對以下數值欄位進行異常值截斷 (Clipping)。
    統計分佈 (JSON)：
    {json.dumps(stats_dict, ensure_ascii=False, indent=2)}
    
    請為每個欄位推算合理的 [下限, 上限] 範圍。回傳嚴格 JSON，以欄位名稱為 key：
    {{ "欄位A": {{"lower": 數值, "upper": 數值}} }}
    """
    try:
        provider = get_ai_provider()
        response_text = provider.generate_json(prompt, temperature=0.1)
        clean_json = _clean_json_string(response_text)
        return json.loads(clean_json)
    except Exception as e:
        print(f"========== [終端機詳細錯誤] AI 批次推算 ==========\n{str(e)}\n================================================")
        log_func(f"[錯誤] AI 批次推算邊界失敗：{_simplify_error(e)}")
        return {}
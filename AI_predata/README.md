# SimpleDPSystem - AI 賦能資料預處理模組 🛡️

這是一個專為「差分隱私 (Differential Privacy)」設計的智能資料預處理圖形化介面 (GUI) 工具的分離測試版。

在將資料送入拉普拉斯 (Laplace) 或指數 (Exponential) 機制加入雜訊之前，資料必須是乾淨、無空值、純數值，且極端值必須被截斷 (Clipping) 以控制敏感度 (Sensitivity)。本模組結合了 `customtkinter` 的現代化介面與 **Google Gemini API** 的強大推論能力，將繁瑣的資料清理工作完全自動化。

## ✨ 核心特色 (Features)

* **支援開源資料集格式**：無縫讀取 `.csv` 與常見於 UCI 機器學習資料庫的 `.data` 檔案（自動背景轉檔）。
* **AI 智能探勘 (Data Profiling)**：自動取樣分析資料結構，判斷是否有表頭，並聰明地找出可轉換數值的類別欄位（例如：Gender -> 0/1）。
* **AI 欄位自動補齊**：當資料缺少表頭時，能讀取 `.names` 或 `.txt` 描述檔，讓 AI 自動提取並精準套用欄位名稱。
* **多檔無縫合併 (Concat)**：支援一鍵合併多個月份/批次的資料表，並自動處理後續檔案多餘的表頭。
* **自動化髒資料清理**：一鍵清除報表常見的「總計/Summary」列，並自動填補缺失值 (NaN)。
* **DP 異常值截斷 (AI 批次推算) 🔥**：差分隱私預處理的靈魂！系統會使用 IQR 演算法自動抓出具備極端離群值的數值欄位，並將統計特徵打包，透過單次 AI 呼叫批次推算出最佳的截斷上下限 (Clipping Bounds)，完美平衡隱私保護與資料實用性。

## 📂 專案架構 (Project Structure)

為了遵循關注點分離原則 (Separation of Concerns)，本模組拆分為 4 個獨立檔案：

```text
SimpleDPSystem\AI_predata
│
├── config.py           # 全域設定檔 (API Key, 模型參數設定)
├── ai_helper.py        # 負責與 Google Gemini API 溝通與提示詞 (Prompt) 邏輯
├── data_processor.py   # 核心處理管線 (Pipeline)，負責所有 Pandas 資料轉換
├── main.py             # GUI 應用程式進入點與使用者互動邏輯
└── README.md           # 專案說明文件
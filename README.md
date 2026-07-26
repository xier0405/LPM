## 📦 LPM （Linux套件管理工具)

這個工具可以方便管理你的Linux套件和git clone下來的檔案

適用於新手剛熟悉linux時不太熟悉指令或套件拿來做什麼方便的幫手！！

*AI需要使用自己的API key 

## 目前支持系統
debian系(ubuntu,kali)

其他派別的系統還在測試,敬請期待><


## 用到的Python套件

```text
requirements.txt (相依套件技術棧總覽)
├── 🖥️ TUI 視覺與終端機渲染引擎
│   ├── textual==0.83.0          # 核心現代化非同步 TUI 介面框架 (全鍵盤控制與彈窗中樞)
│   ├── rich==15.0.0             # 終端機色彩、表格排序與高亮渲染核心
│   ├── markdown-it-py==4.2.0    # 終端機 Markdown 語法解析器 (用於系統除錯報告渲染)
│   ├── mdit-py-plugins==0.6.1   # Markdown 擴充語法插件庫
│   ├── mdurl==0.1.2             # URL 連結解析與編碼處理
│   ├── linkify-it-py==2.1.0     # 自動識別並高亮純文字網址
│   ├── uc-micro-py==2.0.0       # 微型 Unicode 字元與特殊符號處理庫
│   └── Pygments==2.20.0         # 程式碼與日誌高亮顯示引擎
│
├── 🤖 AI 智能整合與雲端通訊
│   ├── google-genai==2.8.0      # Google Gemini AI 官方 SDK (智慧套件推薦與分析)
│   └── google-auth==2.53.0      # Google 雲端服務安全身份驗證機制
│
├── 🌐 現代非同步 HTTP 與網路底層
│   ├── httpx==0.28.1            # 下一代非同步 HTTP 客戶端 (支援 HTTP/2 高速下載)
│   ├── httpcore==1.0.9          # HTTP 底層連線池與通訊控制
│   ├── h11==0.16.0              # 純 Python 實作的 HTTP/1.1 協議層
│   ├── websockets==16.0         # 即時非同步 WebSocket 雙向通訊協議
│   ├── anyio==4.13.0            # 非同步 I/O 跨引擎底層相容層 (asyncio)
│   ├── sniffio==1.3.1           # 非同步函式庫運行時環境偵測器
│   ├── requests==2.34.2         # 標準 HTTP 同步請求後備庫 (用於 GitHub 自檢腳本)
│   ├── urllib3==2.7.0           # 底層 HTTP 連線池與網路安全防護
│   ├── certifi==2026.5.20       # Mozilla SSL/TLS 權威根憑證庫
│   ├── idna==3.18               # 國際化網域名稱 (IDNA) 轉換與解析
│   └── charset-normalizer==3.4.7# 智能字元集編碼自動偵測引擎
│
├── 🔐 底層資訊安全與加密防禦
│   ├── cryptography==48.0.0     # 現代化資訊安全與加解密演算法引擎
│   ├── cffi==2.0.0              # C 語言外部函式庫底層介面 (CFFI)
│   ├── pycparser==3.0           # C 程式碼語法樹解析器 (協助編譯加密底層)
│   ├── pyasn1==0.6.3            # ASN.1 資料結構嚴格解析 (X.509 憑證安全防護)
│   └── pyasn1_modules==0.4.2    # 標準 ASN.1 加密協定模組庫
│
└── 🛠️ 資料驗證、系統偵測與強固重試機制
    ├── pydantic==2.13.4         # 現代化嚴格型別提示與資料驗證引擎
    ├── pydantic_core==2.46.4    # Rust 實作的 Pydantic 極速運算底層核心
    ├── annotated-types==0.7.0   # 型別註解 Metadata 封裝標準
    ├── typing_extensions==4.15.0# 最新版 Python 型別系統擴充支援
    ├── typing-inspection==0.4.2 # 型別結構運行時檢視工具
    ├── tenacity==9.1.4          # 強固型自動重試機制 (防止網路不穩導致 TUI 中斷)
    ├── distro==1.9.0            # Linux 發行版底層環境精準辨識 (協助分流 12 種管理器)
    └── platformdirs==4.10.0     # 跨平台設定檔與快取目錄物理路徑定位
```

## 說明書
會慢慢更新東西上去><

https://hackmd.io/@Xier/rJxvr3ImGl

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


## 設定保存與 AI Token 保護

在「Esc → 系統設定」按下儲存後，SSH 模式與 AI 選擇會保留至下次啟動。
欄位大小、套件清單排序與優先套件庫也會在調整時自動保存。
目前 AI 查詢後端只有 Gemini，因此選單只提供 Gemini。

一般設定儲存在 `$XDG_CONFIG_HOME/lpm/config.json`；若未設定絕對路徑的
`XDG_CONFIG_HOME`，則使用 `~/.config/lpm/config.json`。設定目錄權限為 `0700`，
檔案為 `0600`，使用同目錄暫存檔與原子替換寫入。設定檔只保存允許的非機密欄位，
不會保存 API Token。損壞、過大或不支援版本的檔案會保留原樣，啟動時使用預設值並提示；
請修復或移走該檔案，再重新啟動。符號連結、硬連結與非本人擁有的設定檔會被拒絕。

### Token 的操作方式

- 輸入框以密碼樣式顯示，重新開啟設定時不會回填已存在的 Token。
- 留空代表保留本次使用的 Token；輸入新值代表更換。
- 勾選「使用系統金鑰圈記住新輸入的 Token」，會將新值交給 Linux
  [Secret Service 金鑰圈](https://keyring.readthedocs.io/en/stable/#using-keyring-on-headless-linux-systems)
  保存，供之後啟動時讀取。LPM 明確使用 `keyring.backends.SecretService.Keyring`，
  不會自動選用明文檔案後端。
- 金鑰圈不存在、鎖定或寫入失敗時，會提示 Token 僅本次有效；一般設定仍會保存。
  寫入失敗時，金鑰圈可能仍保留先前的 Token，請解鎖後重新輸入並儲存。
- 取消「記住」會嘗試移除金鑰圈內的 Token，並保留本次執行中的值。
  勾選「刪除已儲存的 Token 並停用本次 AI」則同時清空本次使用的值。
  若刪除失敗會明確提示，且設定會禁止下次自動載入；請解鎖後再次刪除。
- 啟動時，非空白的 `GEMINI_API_KEY` 環境變數優先於金鑰圈。
  環境變數中的 Token 不會自動保存。刪除金鑰圈內的 Token 不會移除外部環境變數，
  若要持續停用 AI，請同時移除該環境變數。
- AI 與金鑰圈錯誤不顯示原始例外內容，避免回應中的 URL 或憑證被帶入介面。
  Token 輸入框也不會發出帶完整內容的 `Input.Changed` / `Input.Submitted` 訊息。

更新後請在虛擬環境執行 `python -m pip install -r requirements.txt`。
若使用 SSH / 無桌面的主機，仍可只在本次輸入 Token；要跨次保存，需先準備可用的
Secret Service、D-Bus 工作階段與已解鎖的金鑰圈。相關設定請參考上述官方文件。

這些保護針對明文落盤與意外顯示；執行時 Token 仍存在程式記憶體中，
無法抵擋已控制同一帳號或 root 的程式。不要將真實 Token 放進程式碼、測試資料或除錯紀錄。

### 驗證

測試不使用真實 Token、不呼叫 AI，也不修改系統套件或真實金鑰圈。
在安裝相依套件後執行：

```bash
python -m pip install pytest
python -m pytest -q
```

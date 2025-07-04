# APMemory MapIN map import tool

- 需求編號: 25061201 (舊單號 24071801)
- 需求者: Yy Chen
- 原作者: Esther Yang
- **Last updated by Esther Yang 2025/07/02**

---

### 注意事項

1. 目前已盡量將 magic number 或其他使用者所定義的資訊都歸納到 `cfg.json`, 並由 `config.py` 統一讀取, 如果未來有需要擴充, 可以參考這兩個檔案
2. `download path`, `dl_path` 等字眼都是表示檔案被下載後的 `存放路徑`
3. `target path` 等字眼是表示要去下載該檔案的 `原始遠端路徑`
4. 個人認為未來可能會因為客戶需求, 需要更改 Map XML 的配置, 此部分邏輯可以查看 `xml.py`
5. 承第 4 點, 如果真的遇到這類需求, 建議可以改成讓 user 可以手動修改 config 的方式去修改 XML 配置 (參考上方第 1 點), 以增進此工具的可活用性
6. 【給開發人員】`cfg.dev.json` 與 `cfg.prod.json` 只是提供開發人員參考用, 請注意開發時不要將上傳路徑設置成 AWMS, 會直接被吃進對方系統, 打咩爹斯

---

### 使用步驟

1. 開啟主程式 (main.py / main.exe)
2. 輸入要處理的 Lot ID, 例如: AADZHS000, MWD053000
3. 點擊 "Execute" 按鈕, 或者按 "Enter" 按鍵
4. 此程式會進行以下動作:

- 從 SFTP 下載 SINF map 檔案, 檔案名稱格式為 {lot_id}.{wafer_id}, 例如: MWD053000.01
- 從 B2B folder 下載工單 (WO file), 檔案會是 .csv, 檔案名稱與 Lot ID 無關
- 從 SINF map 中取得 die size X 與 die size Y
- 從 WO file 中取得 target device 與 quantity
- 比對 SINF map 檔案數量與 WO file 紀錄的 quantity 是否一致
- 比對轉置前後 "\_\_" (對應 "F"), "00" (對應 "1"), 其他 (對應 "X") 的數量是否一致
- 將 map 輸出成 XML 格式, 檔案名稱為 {LotId}.xml (此處的 LotId 對應 XML 中的 LotId 欄位值)
- 將 XML map 檔案上傳到 AWMS MapIN 路徑

5. 期間有任何錯誤, 會透過彈窗提示 user
6. `Log` 文字框內會顯示部分資訊, 提供 user 查看
7. 其他詳細資訊, 無論是成功或失敗的訊息, 都會記錄在 `logs` 資料夾中的 `.log` 檔案中以供偵錯

---

### 配置檔案

1. 此程式有配置檔 `cfg.json`, 也就是以下參數是**採讀取檔案內容輸入, 並非寫在程式碼中**
2. **請記得每次修改 config 後要重開程式, 確保讀取的配置內容是最新的**
3. 各個欄位說明如下, 請注意路徑的部分要加上跳脫字元 `\`:

- env: 環境變數, 請填入 "dev" 或 "prod"
- app_title: 應用程式名稱
- log_path: 本地 log 路徑
- xml_export_dir: 本地 XML 匯出的路徑
- dl_basic_dir: 下載資料夾路徑, 存放下載複製來的 SINF map files 與 WO files
- sftp_host: SFTP address
- sftp_port: SFTP port number, 在此設置為 22
- sftp_user: SFTP 使用者名稱
- sftp_pwd: SFTP 使用者密碼
- sinf_target_path: SINF map 的原路徑, 在此應設置為 "\\1stDM(eMap)"
- wo_target_path: WO file 的原路徑, 在此應設置為 "\\\\10.185.30.51\\api\\B2B\\APM\\Backup"
- wo_month_cnt: 要尋找幾個月以前 (含當前月份) 的 WO file, 在此設置為 2
- xml_bak_path: XML map file 的備份路徑, 在此應設置為 "\\\\t6qnap05-a\\PTE_share\\By_Customer\\CP_portion\\AP_Memory\\MAPIN\\G85 map"
- upload_path: XML map file 的上傳路徑, 在此應設置為 "\\\\10.185.56.37\\awms\\Process\\MapIN\\APMemory\\G85"

---

### 開發者步驟

```
# 請在命令列中輸入以下指令, 建立虛擬環境
$ python -m venv venv

# 啟用 venv (如果你的作業系統為 Windows)
$ venv/Scripts/activate
# 啟用 venv (如果你的作業系統為 Linux / macOS)
$ source venv/bin/activate

# 安裝依賴套件
$ pip install -r requirements.txt

# (如果你有安裝 / 解除依賴套件)
$ pip freeze > requirements.txt

# 啟用程式
$ python main.py

# 打包程式 (請記得先安裝 PyInstaller)
$ .\venv\Scripts\pyinstaller --onefile --icon=icons/app.ico --add-data "icons;icons" main.py
# --onefile: 產生單一 .exe 檔案
# --icon: 指定要嵌入 .exe 的 icon, 必須要是 .ico 檔
# --add-data: 將 icons 資料夾一併打包, 注意 Windows 用分號;, Linux/macOS 用冒號:
# 有多個要一併打包的資料夾或檔案可以重複使用 --add-data
# 如果你不希望執行 .exe 時出現命令列, 請加上 --noconsole (或 -w)

```

---

### 主要程式

- main.py (main.exe)

---

### 需求內容

- 建立一個客製化工具, 僅需要輸入 Lot ID 即可將 G85 XML map 導進 AWMS
- 原材料為: 客戶工單 (WO file), SINF map files
- 輸出檔案為: XML 格式的 map

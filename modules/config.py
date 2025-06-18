def get_sftp_config(env="dev") -> dict:
  """
  取得 SFTP 連線設定

  Arguments:
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    dict: SFTP 連線設定, 包含以下內容:
      - host (str): SFTP 伺服器位址
      - port (int): SFTP 伺服器連接埠, 預設為 22
      - user (str): SFTP 使用者名稱
      - pwd (str): SFTP 使用者密碼
  """
  match env:
    case _:
      return {
        "host": "attsftp01.amkor.com.tw",
        "port": 22,
        "user": "att21070800",
        "pwd": "4Pmem0R#"
      }


def get_sinf_dl_path(lot_id: str, folder_name: str, env="dev") -> str:
  """
  取得 SINF map 下載檔案的存放路徑

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"
    folder_name (str): 資料夾名稱, 由 lot_id 組成, 例如 f"APC_AADZHS000"
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    str: 下載後的 SINF map file 的存放路徑
  """
  match env:
    case "prod":
      return rf"\\t6qnap05-a\PTE_share\By_Customer\CP_portion\AP_Memory\MAPIN\source map\{lot_id}\{folder_name}"
    case _:
      return rf"download\{lot_id}\{folder_name}"


def get_wo_dl_path(lot_id: str, env="dev") -> str:
  """
  取得 WO file 下載檔案的存放路徑

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    str: 下載後的 WO file 的存放路徑
  """
  match env:
    case "prod":
      return rf"\\t6qnap05-a\PTE_share\By_Customer\CP_portion\AP_Memory\MAPIN\source map\{lot_id}"
    case _:
      return rf"download\{lot_id}"


def get_sinf_target_path(env="dev") -> str:
  """
  取得下載 SINF map file 的遠端目標路徑

  Arguments:
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    str: SINF map file 的遠端路徑
  """
  match env:
    case _:
      return "/1stDM(eMap)"


def get_wo_target_path(env="dev") -> str:
  """
  取得下載 WO file 的遠端目標路徑

  Arguments:
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    str: WO file 的遠端路徑
  """
  match env:
    case _:
      return r"\\10.185.30.51\api\B2B\APM\Backup"


def get_export_path(lot_id: str, env="dev") -> str:
  """
  取得 XML 匯出的路徑

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    str: XML 匯出的路徑
  """
  match env:
    case _:
      return rf"export/{lot_id}.xml"


def get_upload_path(env="dev") -> str:
  """
  取得上傳檔案的路徑 (AWMS)

  Arguments:
    env (str): 環境變數, 預設為 "dev", 表示開發環境, "prod" 則表示生產環境

  Returns:
    str: 上傳檔案的 AWMS 路徑
  """
  match env:
    case "prod":
      return r"\\10.185.56.37\MapIN\APMemory\G85"
    case _:
      return r"\\t6qnap05-a\PTE_share\By_Engineering\Esther_Yang\Test"
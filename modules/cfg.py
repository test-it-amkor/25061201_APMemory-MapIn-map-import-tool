import os, json


def load_cfg():
  cfg_filename = "cfg.json"
  if os.path.exists(cfg_filename) and os.path.isfile(cfg_filename):
    with open(cfg_filename) as f:
      return json.load(f)
  else:
    print(f"Oops! {cfg_filename} not found")

cfg = load_cfg()


def get_app_title() -> str:
  """取得 GUI 程式標題"""
  return cfg["app_title"].strip()


def get_log_path() -> str:
  """取得 log directory path"""
  return rf"{cfg['log_path']}".strip()


def get_sftp_cfg() -> dict:
  """
  取得 SFTP 連線設定

  Returns:
    dict: SFTP 連線設定, 包含以下內容:
      - host (str): SFTP 伺服器位址
      - port (int): SFTP 伺服器連接埠, 預設為 22
      - user (str): SFTP 使用者名稱
      - pwd (str): SFTP 使用者密碼
  """
  return {
    "host": cfg["sftp_host"].strip(),
    "port": cfg["sftp_port"],
    "user": cfg["sftp_user"].strip(),
    "pwd": cfg["sftp_pwd"].strip()
  }


def get_sinf_dl_path(lot_id: str, folder_name: str) -> str:
  """
  取得 SINF map 下載檔案的存放路徑

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"
    folder_name (str): 資料夾名稱, 由 lot_id 組成, 例如 f"APC_AADZHS000"
  """
  return rf"{cfg['dl_basic_dir']}\{lot_id}\{folder_name}".strip()


def get_wo_month_cnt() -> int:
  """
  取得下載 WO 時要遍歷幾個月份的資料夾
  詳細可以見 modules.wo 的 getLatestMonths() 與 download_wo_file()
  """
  return int(cfg["wo_month_cnt"])


def get_wo_dl_path(lot_id: str) -> str:
  """
  取得 WO file 下載檔案的存放路徑

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"
  """
  return rf"{cfg['dl_basic_dir']}\{lot_id}".strip()


def get_sinf_target_path() -> str:
  """取得下載 SINF map file 的遠端目標路徑"""
  return rf"{cfg['sinf_target_path']}".strip()


def get_wo_target_path() -> str:
  """取得下載 WO file 的遠端目標路徑"""
  return rf"{cfg['wo_target_path']}".strip()


def get_export_path() -> str:
  """取得 XML 匯出的路徑"""
  return rf"{cfg['xml_export_dir']}".strip()


def get_xml_bak_path() -> str:
  """取得 XML 的備份路徑"""
  return rf"{cfg['xml_bak_path']}".strip()


def get_upload_path() -> str:
  """取得上傳檔案的路徑 (AWMS)"""
  return rf"{cfg['upload_path']}".strip()
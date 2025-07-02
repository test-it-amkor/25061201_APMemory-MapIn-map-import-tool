import os, re
import paramiko
from stat import S_ISREG
from modules.cfg import get_sftp_cfg, get_sinf_dl_path, get_sinf_target_path
from modules.log import write_log


class SftpConnection:
  def __init__(self, host: str, port: int, user: str, pwd: str):
    self.host = host
    self.port = port
    self.user = user
    self.pwd = pwd
    self.sftp = None
    self.transport = None


  def connect(self):
    """建立 SFTP 連線"""
    try:
      self.transport = paramiko.Transport((self.host, self.port))
      self.transport.connect(username=self.user, password=self.pwd)
      self.sftp = paramiko.SFTPClient.from_transport(self.transport)
      write_log("SFTP connection established", "success")
    except Exception as e:
      write_log(f"Failed to connect to SFTP server: {e}", "error")
      return "ConnectionError"


  def close(self):
    """關閉 SFTP 連線"""
    if self.sftp:
      self.sftp.close()
    if self.transport:
      self.transport.close()


  def listdir_attr(self, path):
    """
    取得遠端資料夾下的檔案列表
    此為二次包裝 paramiko.SFTPClient.listdir_attr()

    Arguments:
      path (str): 遠端資料夾路徑

    Returns:
      list: 檔案列表
    """
    if self.sftp:
      return self.sftp.listdir_attr(path)
    else:
      raise Exception("SFTP connection not established")


  def get(self, remote_path, local_path):
    """
    下載遠端檔案到本地
    此為二次包裝 paramiko.SFTPClient.get()
    """
    if self.sftp:
      self.sftp.get(remote_path, local_path)
    else:
      raise Exception("SFTP connection not established")


def download_sinf_map(lot_id: str) -> str:
  """
  依照 lot_id 從 SFTP server 下載對應的 SINF map file

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"

  Returns:
    str: 下載成功, 會回傳下載的資料夾路徑 (dl_path)
    "SinfNotFoundError": 下載失敗, 在 SFTP server 沒有找到 lot_id 所對應的 SINF map 檔案
    "DownloadTooManyTimes": 下載失敗, 在 SFTP server 下載 SINF map 檔案失敗超過 3 次
    "SinfDownloadError": 下載失敗, 其他錯誤
  """

  try:
    folder_name = f"APC_{lot_id}"

    #1. 建立 SFTP 連線
    sftp_cfg = get_sftp_cfg()
    sftp_addr = sftp_cfg["host"]
    sftp_port = sftp_cfg["port"]
    sftp_user = sftp_cfg["user"]
    sftp_pwd = sftp_cfg["pwd"]
    sftp = SftpConnection(sftp_addr, sftp_port, sftp_user, sftp_pwd)
    sftp.connect()

    #2. 列出遠端資料夾下的目標檔案
    try:
      target_path = get_sinf_target_path()
      remote_folder = os.path.join(target_path, folder_name)
      file_attrs = sftp.listdir_attr(remote_folder)
    except (IOError, FileNotFoundError, OSError) as e:
      #如果 lot_id 對應的資料夾中沒有 SINF file, 回傳 SinfNotFoundError
      write_log(f"Remote folder not found: {remote_folder}", "warning")
      return "SinfNotFoundError"

    #3. 只處理 {lot_id}.nn 的檔案 (例如 AADZHS000.01, AADZHS000.09)
    valid_pattern = re.compile(rf"^{lot_id}\.\d{{2}}$")
    valid_attrs = [f for f in file_attrs if valid_pattern.match(f.filename)]

    #4: 組裝下載資料夾路徑, 並建立資料夾 APC_{lot_id}
    dl_path = get_sinf_dl_path(lot_id, folder_name)
    os.makedirs(dl_path, exist_ok=True)

    #5. 開始下載
    download_attempt = 0  #記錄嘗試下載次數
    downloaded_files = [] #記錄已下載的檔案

    #最多嘗試下載 3 次
    while download_attempt < 3:
      downloaded_files.clear()  #清空已下載檔案列表

      for file_attr in valid_attrs:
        if S_ISREG(file_attr.st_mode):
          remote_file = os.path.join(remote_folder, file_attr.filename)
          local_file = os.path.join(dl_path, file_attr.filename)
          sftp.get(remote_file, local_file)
          downloaded_files.append(file_attr.filename)
          write_log(f"Downloaded SINF file: {file_attr.filename}", "debug")

      #檢查下載的檔案數量是否與 SFTP 上的檔案數量一致
      if len(downloaded_files) == len(valid_attrs):
        write_log("All files downloaded successfully", "success")
        break
      else:
        download_attempt += 1
        write_log(f"Downloaded {len(downloaded_files)} files, expected {len(valid_attrs)}. Retrying... (Attempt {download_attempt})", "warning")

    #6-1. 如果嘗試下載超過 3 次仍未成功, 拋出異常
    if download_attempt == 3:
      return "DownloadTooManyTimes"

    #6-2. 如果下載成功, 回傳 None 並關閉 SFTP 連線
    write_log("Download SINF map file completed successfully", "success")
    #關閉 SFTP 連線
    sftp.close()
    return dl_path

  except Exception as e:
    write_log(f"Download SINF failed: {e}", "error")
    return "SinfDownloadError"


def get_sinf_info(sinf_path: str) -> dict | str:
  """
  從 SINF map 檔案中讀取 XDIES 與 YDIES 的數值

  Arguments:
    sinf_path (str): SINF map 檔案的路徑

  Returns:
    dict: 成功讀取 SINF map, 回傳一個字典, 包含以下內容:
      - dieSizeX (float): Die size X, 例如 2.1
      - dieSizeY (float): Die size Y, 例如 2.1
    "SinfNotFoundError": 如果在 sinf_path 資料夾下沒有找到任何檔案, 回傳 "SinfNotFoundError"
    "SinfReadError": 如果讀取失敗, 回傳 "SinfReadError"
  """

  try:
    #取得 sinf_path 資料夾下的第一個檔案
    files = [f for f in os.listdir(sinf_path) if os.path.isfile(os.path.join(sinf_path, f))]
    if not files:
      return "SinfNotFoundError"
    sinf_file = os.path.join(sinf_path, files[0])

    dieSizeX = None
    dieSizeY = None

    #讀取 SINF map 檔案內容, 取得 XDIES 與 YDIES 的數值
    with open(sinf_file, "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line.startswith("XDIES:"):
          try:
            dieSizeX = float(line.split(":", 1)[1].strip())
          except Exception as e:
            raise e
        elif line.startswith("YDIES:"):
          try:
            dieSizeY = float(line.split(":", 1)[1].strip())
          except Exception as e:
            raise e
        if dieSizeX is not None and dieSizeY is not None:
          break

    if dieSizeX is not None and dieSizeY is not None:
      return {"dieSizeX": dieSizeX, "dieSizeY": dieSizeY}
    else:
      raise f"Die size X or Y not found in SINF file: {sinf_file}"

  except Exception as e:
    write_log(f"Read SINF file failed: {e}", "error")
    return "SinfReadError"
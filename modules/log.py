import os, logging
from datetime import datetime
from modules.cfg import get_log_path


#配置日誌
log_dir = get_log_path()
os.makedirs(log_dir, exist_ok=True)
curr_date = datetime.now().strftime("%Y%m%d")
LOG_FILE = os.path.join(log_dir, f"exec_log_{curr_date}.log")
logging.basicConfig(
  filename=LOG_FILE,    #日誌檔案名稱
  level=logging.INFO,   #設定日誌等級
  filemode="a",         #追加模式
  encoding="utf-8",     #指定編碼為 UTF-8
  format="%(asctime)s - %(message)s"  #日誌格式
)

def write_log(msg: str, status="info"):
  title = "Information"
  match status:
    case "success":
      title = "Success"
    case "warning":
      title = "Warning"
    case "error":
      title = "Error"
    case "about":
      title = "About"
    case _:
      title = "Information"

  print(f"[{title}] {msg}")
  logging.info(f"[{title}] {msg}")
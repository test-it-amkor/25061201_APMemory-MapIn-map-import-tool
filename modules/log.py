import os, logging
from datetime import datetime
from modules.cfg import get_log_path


#配置 logging
log_dir = get_log_path()
curr_date = datetime.now().strftime('%Y%m%d')
LOG_FILE = os.path.join(log_dir, f"execution_log_{curr_date}.log")
logging.basicConfig(
  filename=LOG_FILE,    #日誌檔案名稱
  level=logging.INFO,   #設定日誌等級
  filemode="a",         #追加模式
  encoding="utf-8",     #指定編碼為UTF-8
  format="%(asctime)s - %(levelname)s - %(message)s"  #日誌格式
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
  return logging.info(f"[{title}] {msg}")
import os, shutil
import pandas as pd
from datetime import datetime
from modules.cfg import get_wo_dl_path, get_wo_target_path
from modules.log import write_log

def getLatestMonths(num=2) -> list:
  """
  取得最近 num 個月的月份字串列表

  Arguments:
    num (int): 要取得的最近幾個月份的字串, 預設為 2

  Returns:
    list: 最近 num 個月的月份字串列表, 例如 ["WO2024/Dec", "WO2025/Jan"]
  """

  month_map = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
  }
  result = []
  today = datetime.today()
  year = today.year
  month = today.month

  for _ in range(num):
    month_str = month_map[month]
    result.append(f"WO{year}\{month_str}")
    #回推一個月
    month -= 1
    if month == 0:
      month = 12
      year -= 1

  return result


def download_wo_file(lot_id: str) -> str:
  """
  遍歷 B2B folder 上的工單 (WO file) 資料夾內容,
  讀取 WO 檔案 (.csv), 比對其內容 LOT NO 欄位是否與 lot_id 相符,
  如果相符則下載此 WO 檔案到指定的資料夾中

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"

  Returns:
    str: 下載成功, 會回傳下載的資料夾路徑 (dl_path)
    "WoReadError": 讀取 WO 檔案 (.csv) 失敗
    "WoNotFoundError": 在 B2B folder 沒有找到符合的 WO 檔案
  """

  try:
    monthStrs = getLatestMonths(2)

    for month in monthStrs:
      #1. 組裝下載資料夾路徑
      dl_path = get_wo_dl_path(lot_id)
      os.makedirs(dl_path, exist_ok=True)

      #2. 取得要遍歷的資料夾路徑
      target_path = get_wo_target_path()
      folder_path = rf"{target_path}\{month}"
      #如果資料夾不存在, 跳過此月份
      if not os.path.exists(folder_path):
        continue
      #找出所有 .csv 檔案, 如果沒有 .csv 檔案, 跳過此月份
      csv_fs = [f for f in os.listdir(folder_path) if f.lower().endswith('.csv')]
      if not csv_fs:
        continue

      #3. 遍歷所有 WO 檔案, 讀取裡面的 LOT NO 欄位值
      for csv_f in csv_fs:
        csv_path = os.path.join(folder_path, csv_f)
        #取得 dataframe
        try:
          df = pd.read_csv(csv_path)
        except Exception as e:
          write_log(f"Read CSV file {csv_f} failed: {e}", "error")
          return "WoReadError"
        #檢查 LOT NO 欄位是否存在, 不存在則跳過
        if "LOT NO" not in df.columns:
          continue
        #檢查是否有 LOT NO 欄位值與 lot_id 一致的 WO 檔案, 不一致則跳過
        match_rows = df[df["LOT NO"].astype(str).str.strip() == lot_id]
        if match_rows.empty:
          continue
        #找到符合的 csv, 將其下載複製到 dl_path
        download_full_path = os.path.join(dl_path, csv_f)
        shutil.copy2(csv_path, download_full_path)
        write_log(f"Downloaded WO file: {download_full_path}", "info")
        return download_full_path
      #若此月份資料夾沒找到符合的 WO file, 繼續往前一個月檢查
    #若所有月份資料夾都沒找到
    return "WoNotFoundError"

  except Exception as e:
    write_log(f"Download WO failed: {e}", "error")


def get_wo_info(wo_path: str) -> dict | str:
  """
  讀取 WO file, 組成 Target Device 字串內容, 回傳 targetDevice 與 quantity 值

  Arguments:
    wo_path (str): 下載後的 WO 檔案路徑

  Returns:
    dict: 成功讀取 WO 檔案, 回傳一個字典, 包含以下內容:
      - targetDevice (str): 由 OUTPUT P/N、MASK、SUFFIX 三個欄位組成, 例如 "ACIPC50K0AA111"
      - quantity (int): 片數, 例如 22
    "WoReadError": 讀取 WO 檔案 (.csv) 失敗
  """
  #取得 dataframe
  try:
    df = pd.read_csv(wo_path)
  except Exception as e:
    write_log(f"Read CSV file {wo_path} failed: {e}", "error")
    return "WoReadError"

  #取得 OUTPUT P/N、MASK、SUFFIX 欄位的值
  try:
    #只取第一行資料
    row = df.iloc[0]

    try:
      output_p_n = str(row.get("OUTPUT P/N", "")).strip()
      mask = str(row.get("MASK", "")).strip()
      suffix = str(row.get("SUFFIX", "")).strip()
      if not output_p_n or not mask or not suffix:
        ve = ValueError("OUTPUT P/N, MASK, or SUFFIX is empty")
        write_log(ve, "error")
        raise ve
      target_device = f"{output_p_n}{mask}{suffix}"
    except Exception:
      ve = ValueError("Failed to parse OUTPUT P/N, MASK, or SUFFIX")
      write_log(ve, "error")
      raise ValueError(ve)

    quantity = row.get("QUANTITY", 0)
    try:
      quantity = int(quantity)
    except Exception:
      raise ValueError(f"Quantity value is not an integer: {quantity}")

    return {"targetDevice": target_device, "quantity": quantity}
  except Exception as e:
    write_log(f"Parse WO file info failed, file path: {wo_path}, error: {e}", "error")
    return "WoReadError"
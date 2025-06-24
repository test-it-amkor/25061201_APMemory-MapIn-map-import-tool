import os
from PyQt5.QtCore import QThread, pyqtSignal
from modules.log import write_log
from modules.cfg import get_export_path, get_sinf_dl_path, get_upload_path
from modules.sinf import download_sinf_map, get_sinf_info
from modules.upload import upload_xml
from modules.wo import download_wo_file, get_wo_info
from modules.xml import export_xml


class Worker(QThread):
  """使用 QThread 執行長時間運行的操作, 避免阻塞 GUI 主執行緒"""
  progress = pyqtSignal(int)
  message = pyqtSignal(str, str, bool)  #status, msg, skip_log
  log_text = pyqtSignal(str)
  finished = pyqtSignal()
  result = pyqtSignal(dict)


  def __init__(self, lot_id):
    super().__init__()
    self.lot_id = lot_id


  def get_error_msg(self, key: str, custom_info=None) -> str:
    """
    根據 error 的 key 取得對應的 message 內容

    Arguments:
      key (str): error key, 例如 "ConnectionError", "SinfNotFoundError" 等
      custom_info (str | dict, optional): 自訂訊息內容, 例如 Lot ID 或 SINF map 檔案名稱

    Returns:
      str: 對應的 error message 內容, 如果沒有對應的 key, 則回傳 "Unknown error occurred"
    """
    if key == "NumberMismatchError":
      if isinstance(custom_info, dict):
        return f"SINF map file count {custom_info['sinf']} does not match WO QUANTITY value {custom_info['wo']}"
      else:
        return f"SINF map file count does not match WO QUANTITY value"
    else:
      error_messages = {
        "ConnectionError": "Failed to connect to SFTP server",
        "SinfNotFoundError": f"Lot ID '{custom_info}' SINF map not found from FTP",
        "DownloadTooManyTimes": f"Failed to download {custom_info} file after 3 attempts",
        "SinfDownloadError": "Failed to download SINF map file",
        "SinfReadError": "Failed to read SINF map file",
        "WoReadError": "Failed to read .csv (WO file)",
        "WoNotFoundError": f"Lot ID '{custom_info}' WO file not found from B2B folder",
        "RemoveExportError": f"Failed to remove existed export/{custom_info}.xml file",
        "ExportXmlError": f"Failed to export XML file for lot ID '{custom_info}'",
        "XmlNotFoundError": f"XML file for lot ID '{custom_info}' not found in export folder",
        "UploadError": f"Error uploading XML to AWMS for lot '{custom_info}'"
      }
      return error_messages.get(key, f"Unknown error occurred: {key}")


  def run(self):
    """
    1. 取得 Lot ID, 並檢查 Lot ID 是否為空
    2. 如果 Lot ID 不為空, 開始處理
    3. 下載 SINF map 檔案, 取得 dieSizeX 與 dieSizeY
    4. 下載工單 (WO file), 取得 targetDevice 與 quantity
    5. 比對 SINF map 的檔案數量與 WO 所記錄的 quantity 是否一致
    6. 將 map 輸出成 XML 格式
    7. 將 XML 檔案上傳到 AWMS MapIN 路徑
    8. 如果有任何錯誤, 使用 QMessageBox 顯示警告訊息
    9. 如果成功, 印出相關資訊, 並使用 QMessageBox 顯示成功訊息
    """
    try:
      write_log("=" * 60, "info")

      lot_id = self.lot_id
      self.progress.emit(0)
      self.log_text.emit(f"Processing lot ID: {lot_id}")

      #Lot ID 不為空, 開始處理
      if lot_id and len(lot_id) != 0:
        write_log(f"Processing Lot ID: {lot_id}")
        self.progress.emit(10)

      ################################################################################
      #1. 下載 SINF map 檔案, 取得 die_size_x 與 die_size_y
      sinf_result = download_sinf_map(lot_id)
      self.progress.emit(35)

      #如果在 SFTP server 沒有找到 lot_id 所對應的 SINF map 檔案
      if sinf_result == "SinfNotFoundError":
        self.message.emit("warning", self.get_error_msg(sinf_result, lot_id), False)
        return
      #如果在 SFTP server 下載 SINF map 檔案失敗超過 3 次
      elif sinf_result == "DownloadTooManyTimes":
        self.message.emit("warning", self.get_error_msg(sinf_result, "SINF map"), False)
        return
      #如果在 SFTP server 下載 SINF map 檔案遇到其他失敗
      elif sinf_result == "SinfDownloadError":
        self.message.emit("warning", self.get_error_msg(sinf_result), False)
        return

      #如果成功下載 SINF map 檔案, sinf_result 會是其下載路徑
      if sinf_result != None and sinf_result.strip() != "":
        self.log_text.emit(f"SINF map download folder: {sinf_result}")
        sinf_info = get_sinf_info(sinf_result)
        #如果是字串, 代表讀取 SINF map 檔案失敗
        if isinstance(sinf_info, str):
          self.message.emit("warning", self.get_error_msg(sinf_info), False)
          return
        #如果是 dict, 代表成功讀取 SINF map, 取得 dieSizeX 與 dieSizeY
        elif isinstance(sinf_info, dict):
          die_size_x = sinf_info.get("dieSizeX")
          die_size_y = sinf_info.get("dieSizeY")
          die_size_msg = f"Die Size X: {die_size_x}, Die Size Y: {die_size_y}"
          self.log_text.emit(die_size_msg)
          write_log(die_size_msg)
          self.progress.emit(45)

      ################################################################################
      #2. 下載工單 (WO file), 取得 target_device 與 quantity
      wo_result = download_wo_file(lot_id)

      #如果讀取 WO 檔案 (.csv) 失敗
      if wo_result == "WoReadError":
        self.message.emit("warning", self.get_error_msg(wo_result), False)
        return
      #如果在 B2B folder 沒有找到符合的 WO 檔案
      elif wo_result == "WoNotFoundError":
        self.message.emit("warning", self.get_error_msg(wo_result, lot_id), False)
        return
      #如果成功下載 WO 檔案, wo_result 會是其下載路徑
      elif wo_result and wo_result.strip() != "":
        self.log_text.emit(f"WO file download folder: {wo_result}")
        wo_info = get_wo_info(wo_result)
        #如果是字串, 代表讀取 WO file 失敗
        if isinstance(wo_info, str):
          self.message.emit("warning", self.get_error_msg(wo_info), False)
          return
        #如果是 dict, 代表成功讀取 WO file, 取得 targetDevice 與 quantity
        elif isinstance(wo_info, dict):
          target_device = wo_info.get("targetDevice")
          quantity = wo_info.get("quantity")
          wo_info_msg = f"Target device: {target_device}, Quantity: {quantity}"
          self.log_text.emit(wo_info_msg)
          write_log(wo_info_msg)
          self.progress.emit(65)

      ################################################################################
      #3. 比對 SINF map 的檔案數量與 WO 所記錄的 quantity 是否一致
      sinf_dl_path = get_sinf_dl_path(lot_id, f"APC_{lot_id}")
      sinf_file_cnt = len(os.listdir(sinf_dl_path))
      if sinf_file_cnt != quantity:
        self.message.emit("warning", self.get_error_msg("NumberMismatchError", {"sinf": sinf_file_cnt, "wo": quantity}), False)
        return
      self.log_text.emit(f"SINF map file count: {sinf_file_cnt}, WO QUANTITY: {quantity}")
      self.progress.emit(70)

      ################################################################################
      #4. 如果數量一致, 開始輸出 XML 檔案
      export_result = export_xml(lot_id, target_device, die_size_x, die_size_y)
      if isinstance(export_result, str):
        self.message.emit("warning", self.get_error_msg(export_result, lot_id), False)
        return
      self.log_text.emit(f"Map XML file path: {get_export_path(lot_id)}")
      self.progress.emit(85)

      ################################################################################
      #5. 將 XML 檔案上傳到 AWMS MapIN 路徑
      upload_result = upload_xml(lot_id)

      #如果找不到匯出的 XML 檔案, 或者上傳至 AWMS 時發生錯誤
      if upload_result == "XmlNotFoundError" or upload_result == "UploadError":
        self.message.emit("warning", self.get_error_msg(upload_result, lot_id), False)
        return
      self.progress.emit(95)
      self.log_text.emit(f"Uploaded map XML file path: {rf"{get_upload_path()}\{lot_id}.xml"}")

      ################################################################################
      #6. 顯示成功訊息
      self.message.emit("success", f"Success! Processed lot ID: {lot_id}", False)
      self.progress.emit(100)
      self.log_text.emit(f"Success!")
      self.finished.emit()

    except Exception as e:
      self.message.emit("error", self.get_error_msg(e), False)
      self.progress.emit(0)
      self.finished.emit()


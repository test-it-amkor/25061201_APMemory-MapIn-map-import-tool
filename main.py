import sys, os
from modules.log import write_log
from modules.cfg import get_app_title, get_sinf_dl_path
from modules.sinf import download_sinf_map, get_sinf_info
from modules.upload import upload_xml
from modules.wo import download_wo_file, get_wo_info
from modules.xml import export_xml
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QFormLayout, QMessageBox, QProgressBar


class MyWidget(QWidget):
  """
  主視窗, 包含以下元件:
    - Lot ID 單行輸入框
    - Execute 按鈕
    - Exit 按鈕
  """

  def __init__(self):
    super().__init__()
    self.setWindowTitle(get_app_title())
    self.resize(500, 300)
    self.ui_setup()


  def ui_setup(self):
    self.form_layout = QFormLayout()
    #Lot ID 單行輸入框
    self.lot_id = QLineEdit(self)
    self.form_layout.addRow("Lot ID", self.lot_id)
    #Execute 按鈕
    self.exec_btn = QPushButton("Execute", self)
    self.exec_btn.clicked.connect(self.on_execute)
    self.form_layout.addRow(self.exec_btn)
    #Exit 按鈕
    self.exit_btn = QPushButton("Exit", self)
    self.exit_btn.clicked.connect(self.close)
    self.form_layout.addRow(self.exit_btn)
    #進度條
    self.progress_bar = QProgressBar(self)
    self.progress_bar.setValue(0)
    self.progress_bar.setMaximum(100)
    self.progress_bar.setVisible(False)  #初始隱藏進度條
    self.form_layout.addRow(self.progress_bar)

    #設置 main layout
    self.setLayout(self.form_layout)

  def get_error_msg(key: str, custom_info=None) -> str:
    """
    根據 error 的 key 取得對應的 message 內容

    Arguments:
      key (str): error key, 例如 "ConnectionError", "SinfNotFoundError" 等
      custom_info (str, optional): 自訂訊息內容, 例如 Lot ID 或 SINF map 檔案名稱

    Returns:
      str: 對應的 error message 內容, 如果沒有對應的 key, 則回傳 "Unknown error occurred"
    """
    error_messages = {
      "ConnectionError": "Failed to connect to SFTP server",
      "SinfNotFoundError": f"Lot ID {custom_info} SINF map not found from FTP",
      "DownloadTooManyTimes": f"Failed to download {custom_info} file after 3 attempts",
      "SinfDownloadError": "Failed to download SINF map file",
      "SinfReadError": "Failed to read SINF map file",
      "WoReadError": "Failed to read .csv (WO file)",
      "WoNotFoundError": f"Lot ID {custom_info} WO file not found from B2B folder",
      "NumberMismatchError": f"SINF map file number {custom_info["sinf"]} does not match WO QUANTITY value {custom_info["wo"]}",
      "RemoveExportError": f"Failed to remove existed export/{custom_info}.xml file",
      "ExportXmlError": f"Failed to export XML file for lot ID {custom_info}",
      "XmlNotFoundError": f"XML file for lot ID {custom_info} not found in export folder",
      "UploadError": f"Error uploading XML to AWMS for lot {custom_info}"
    }
    return error_messages.get(key, f"Unknown error occurred: {key}")


  def show_msg_box(self, status: str, msg: str, skip_log=False):
    """
    二次包裝 QMessageBox 顯示文字功能, 並將內容紀錄進 log 中

    Arguments:
      status (str): 僅支援以下幾種狀態, 若輸入以下狀態以外的字串, 會預設使用 QMessageBox.information()
        - "success": 成功通知, 使用 QMessageBox.information()
        - "warning": 警告通知, 使用 QMessageBox.warning()
        - "error": 錯誤通知, 使用 QMessageBox.critical()
        - "about": 關於應用程式的資訊, 例如 版本資訊, 作者資訊, 使用 QMessageBox.about()
      msg (str): 消息框文字內容
      skip_log (bool): 是否要略過將 log 文字內容記錄進 log 中? 預設為 False, 也就是啟用記錄功能
    """
    box_title = "Information"
    match status:
      case "success":
        box_title = "Success"
        QMessageBox.information(self, box_title, msg)
      case "warning":
        box_title = "Warning"
        QMessageBox.warning(self, box_title, msg)
      case "error":
        box_title = "Error"
        QMessageBox.critical(self, box_title, msg)
      case "about":
        box_title = "About"
        QMessageBox.about(self, box_title, msg)
      case _:
        QMessageBox.information(self, box_title, msg)

    if skip_log is False:
      write_log(msg, status)


  def set_progress(self, num: int):
    """
    設置 QProgressBar 的進度值

    Arguments:
      num (int): 進度值, 0-100
    """
    self.progress_bar.setValue(num) #設置進度值
    QApplication.processEvents()    #更新 UI


  def on_execute(self):
    """
    按下 Execute 按鈕後的處理函式, 主要流程:
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
      #顯示進度條
      self.progress_bar.setVisible(True)
      #重置進度條進度為 0
      self.set_progress(0)

      lot_id = self.lot_id.text().strip()

      #檢查 Lot ID 是否為空
      if not lot_id:
        self.show_msg_box("warning", "Please enter Lot ID", True)
        return

      #Lot ID 不為空, 開始處理
      write_log(f"Processing Lot ID: {lot_id}")
      self.set_progress(10)

      ################################################################################
      #1. 下載 SINF map 檔案, 取得 die_size_x 與 die_size_y
      sinf_result = download_sinf_map(lot_id)
      self.set_progress(35)

      #如果在 SFTP server 沒有找到 lot_id 所對應的 SINF map 檔案
      if sinf_result == "SinfNotFoundError":
        self.show_msg_box("warning", self.get_error_msg(sinf_result, lot_id), False)
        return

      #如果在 SFTP server 下載 SINF map 檔案失敗超過 3 次
      elif sinf_result == "DownloadTooManyTimes":
        self.show_msg_box("warning", self.get_error_msg(sinf_result, "SINF map"), False)
        return

      #如果在 SFTP server 下載 SINF map 檔案遇到其他失敗
      elif sinf_result == "SinfDownloadError":
        self.show_msg_box("warning", self.get_error_msg(sinf_result), False)
        return

      #如果成功下載 SINF map 檔案, sinf_result 會是其下載路徑
      elif sinf_result != None and sinf_result.strip() != "":
        sinf_info = get_sinf_info(sinf_result)
        #檢查 sinf_info 的型別
        #如果是字串, 代表讀取 SINF map 檔案失敗
        if isinstance(sinf_info, str):
          self.show_msg_box("warning", self.get_error_msg(sinf_info), False)
          return
        #如果是 dict, 代表成功讀取 SINF map, 取得 dieSizeX 與 dieSizeY
        elif isinstance(sinf_info, dict):
          die_size_x = sinf_info.get("dieSizeX")
          die_size_y = sinf_info.get("dieSizeY")
          write_log(f"Die Size X: {die_size_x}, Die Size Y: {die_size_y}")
          self.set_progress(45)

      ################################################################################
      #2. 下載工單 (WO file), 取得 target_device 與 quantity
      wo_result = download_wo_file(lot_id)

      #如果讀取 WO 檔案 (.csv) 失敗
      if wo_result == "WoReadError":
        self.show_msg_box("warning", self.get_error_msg(wo_result), False)
        return

      #如果在 B2B folder 沒有找到符合的 WO 檔案
      elif wo_result == "WoNotFoundError":
        self.show_msg_box("warning", self.get_error_msg(wo_result, lot_id), False)
        return

      #如果成功下載 WO 檔案, wo_result 會是其下載路徑
      elif wo_result != None and wo_result.strip() != "":
        wo_info = get_wo_info(wo_result)
        #檢查 wo_info 的型別
        #如果是字串, 代表讀取 WO file 失敗
        if isinstance(wo_info, str):
          self.show_msg_box("warning", self.get_error_msg(wo_info), False)
          return
        #如果是 dict, 代表成功讀取 WO file, 取得 targetDevice 與 quantity
        elif isinstance(wo_info, dict):
          target_device = wo_info.get("targetDevice")
          quantity = wo_info.get("quantity")
          write_log(f"Target device: {target_device}, Quantity: {quantity}")
          self.set_progress(65)

      ################################################################################
      #3. 比對 SINF map 的檔案數量與 WO 所記錄的 quantity 是否一致
      sinf_dl_path = get_sinf_dl_path()
      sinf_file_cnt = len(os.listdir(sinf_dl_path))
      if sinf_file_cnt != quantity:
        self.show_msg_box("warning", self.get_error_msg(wo_result, {"sinf": sinf_file_cnt, "wo": quantity}), False)
        return
      self.set_progress(70)

      ################################################################################
      #4. 如果數量一致, 開始輸出 XML 檔案
      export_result = export_xml(lot_id, target_device, die_size_x, die_size_y)
      if isinstance(export_result, str):
        self.show_msg_box("warning", self.get_error_msg(export_result, lot_id), False)
        return
      self.set_progress(85)

      ################################################################################
      #5. 將 XML 檔案上傳到 AWMS MapIN 路徑
      upload_result = upload_xml(lot_id)

      #如果找不到匯出的 XML 檔案, 或者上傳至 AWMS 時發生錯誤
      if upload_result == "XmlNotFoundError" or upload_result == "UploadError":
        self.show_msg_box("warning", self.get_error_msg(upload_result, lot_id), False)
        return
      self.set_progress(95)

      ################################################################################
      #6. 顯示成功訊息
      self.show_msg_box("success", f"Success! Processed lot ID: {lot_id}", False)
      self.set_progress(100)

    except Exception as e:
      #觸發 Unknown error occurred
      self.show_msg_box("error", self.get_error_msg(e), False)
      self.set_progress(0)


if __name__ == '__main__':
  app = QApplication(sys.argv)
  main = MyWidget()
  main.show()
  sys.exit(app.exec_())
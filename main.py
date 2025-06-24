import sys, os, subprocess
from datetime import datetime
from modules.log import write_log
from modules.cfg import get_app_title
from modules.worker import Worker
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox, QProgressBar
from PyQt5.QtGui import QFont, QIcon


class MainWidget(QWidget):
  """
  主視窗, 包含以下元件:
    - Lot ID 單行輸入框
    - Execute 按鈕
    - Exit 按鈕
  """

  def __init__(self):
    super().__init__()
    self.setWindowTitle(get_app_title())
    self.setMinimumSize(700, 400)
    self.resize(700, 400)
    self.ui_setup()


  def ui_setup(self):
    #main layout, 垂直置中
    main_layout = QVBoxLayout()
    main_layout.setAlignment(Qt.AlignCenter)
    main_layout.addStretch(1)

    ################################################################################
    #1. 第一列: Main Operation 群組, 包含 Lot ID label & 單行輸入框 & Execute 按鈕
    self.grp_box_1 = QGroupBox("Main Operation")
    v_layout_1 = QVBoxLayout()
    h_layout_1 = QHBoxLayout()
    h_layout_1.setAlignment(Qt.AlignCenter)
    #Lot ID Label
    h_layout_1.addWidget(QLabel("Lot ID"))
    #Lot ID 單行輸入框
    self.lot_id = QLineEdit(self)
    self.lot_id.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    h_layout_1.addWidget(self.lot_id)
    #Execute 按鈕
    self.exec_btn = QPushButton("Execute", self)
    self.exec_btn.setIcon(QIcon("icons/exec.png"))
    self.exec_btn.clicked.connect(self.on_execute)
    self.exec_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    h_layout_1.addWidget(self.exec_btn)
    v_layout_1.addLayout(h_layout_1)
    self.grp_box_1.setLayout(v_layout_1)
    main_layout.addWidget(self.grp_box_1)

    ################################################################################
    #2. 第二列: 僅包含進度條
    h_layout_2 = QHBoxLayout()
    h_layout_2.setAlignment(Qt.AlignCenter)
    h_layout_2.setContentsMargins(20, 10, 20, 10)
    self.prog_bar = QProgressBar(self)
    self.prog_bar.setValue(0)
    self.prog_bar.setMaximum(100)
    self.prog_bar.setMinimumWidth(1)
    self.prog_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    h_layout_2.addWidget(self.prog_bar)
    main_layout.addLayout(h_layout_2)

    ################################################################################
    #3. 第三列: Log 群組, 僅包含一個唯讀多行文字輸入框
    self.grp_box_3 = QGroupBox("Log")
    v_layout_3 = QVBoxLayout()
    self.log_text = QTextEdit(self)
    self.log_text.setReadOnly(True)
    v_layout_3.addWidget(self.log_text)
    self.grp_box_3.setLayout(v_layout_3)
    main_layout.addWidget(self.grp_box_3)

    ################################################################################
    #4. 第四列: 包含 Info, Open Directory, Exit 三個按鈕
    h_layout_4 = QHBoxLayout()
    h_layout_4.setAlignment(Qt.AlignCenter)
    #Info 按鈕
    self.info_btn = QPushButton("Info", self)
    self.info_btn.setIcon(QIcon("icons/info.png"))
    self.info_btn.clicked.connect(self.show_app_info)
    h_layout_4.addWidget(self.info_btn)
    #Open Directory 按鈕
    self.open_btn = QPushButton("Open Directory", self)
    self.open_btn.setIcon(QIcon("icons/folder.png"))
    self.open_btn.clicked.connect(self.open_curr_dir)
    h_layout_4.addWidget(self.open_btn)
    #Exit 按鈕
    self.exit_btn = QPushButton("Exit", self)
    self.exit_btn.setIcon(QIcon("icons/exit.png"))
    self.exit_btn.clicked.connect(self.close)
    h_layout_4.addWidget(self.exit_btn)

    main_layout.addLayout(h_layout_4)
    main_layout.addStretch(1)
    self.setLayout(main_layout)


  def show_app_info(self):
    title_texts = get_app_title()
    info_text = "\n".join([
      title_texts,
      "-" * 40,
      "Author: ATT Test IT",
      "Last updated on 2025.06.23"
    ])
    self.show_msg_box("about", info_text, True)


  def open_curr_dir(self):
    """使用檔案總管開啟當前資料夾"""
    curr_dir = os.getcwd()
    subprocess.Popen(f'explorer "{curr_dir}"')


  def show_log_text(self, text: str="Default message"):
    """更新 log_text 要顯示的文字內容"""
    curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self.log_text.append(f"{curr_time} {text}")


  def keyPressEvent(self, event):
    """
    檢查是否按下 Enter 鍵
    Warning: 覆寫類別 virtual method, 請不要修改此函式名稱
    """
    if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
      self.on_execute()  #觸發按鈕的 click 事件


  def show_msg_box(self, status: str, msg: str, skip_log=False):
    """
    二次包裝 QMessageBox (QMessageBox) 顯示文字功能, 並將內容紀錄進 log 中

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
        self.on_finished()
      case "warning":
        box_title = "Warning"
        QMessageBox.warning(self, box_title, msg)
        self.on_finished()
      case "error":
        box_title = "Error"
        QMessageBox.critical(self, box_title, msg)
        self.on_finished()
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
    self.prog_bar.setValue(num) #設置進度值
    QApplication.processEvents()    #更新 UI


  def on_finished(self):
    self.exec_btn.setEnabled(True)
    self.exit_btn.setEnabled(True)
    # self.prog_bar.setVisible(True)  #在此手動設定是否隱藏進度條


  def on_execute(self):
    """
    按下 Execute 按鈕後的處理函式, 主要流程包裝在 Worker.run() 中
    """
    lot_id = self.lot_id.text().strip()
    #檢查 Lot ID 是否為空
    if not lot_id:
      self.show_msg_box("warning", "Please enter Lot ID", True)
      return

    # self.prog_bar.setVisible(True)  #在此手動設定是否隱藏進度條
    self.set_progress(0)                #重置進度條進度為 0
    self.exec_btn.setEnabled(False)
    self.exit_btn.setEnabled(False)

    self.worker = Worker(lot_id)
    self.worker.progress.connect(self.set_progress)
    self.worker.message.connect(self.show_msg_box)
    self.worker.log_text.connect(self.show_log_text)
    self.worker.finished.connect(self.on_finished)
    self.worker.start()


if __name__ == "__main__":
  #建立 QApplication instance
  app = QApplication(sys.argv)
  app.setStyleSheet("""
    QPushButton {
      padding: 4px 8px;
      min-width: 60px;
    }
  """)

  #全域設定字型為 微軟正黑體, 12pt
  app.setFont(QFont("Microsoft JhengHei", 10))

  #為 app 設置 icon
  app.setWindowIcon(QIcon("icons/app.png"))

  main = MainWidget()
  main.show()
  sys.exit(app.exec_())
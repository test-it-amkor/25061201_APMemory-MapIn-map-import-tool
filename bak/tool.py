from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QFormLayout, QDialogButtonBox, QFileDialog
from PyQt5.QtCore import Qt
from datetime import datetime
import os
import re

class SelectionDialog(QDialog):   #選擇single/multiple
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(200,100)
        self.setWindowTitle('Selection Dialog')
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Please select the type of operation:")
        self.layout.addWidget(self.label)

        self.singleButton = QPushButton("Single")
        self.multipleButton = QPushButton("Multiple")
        self.multipleButton.clicked.connect(self.multipleSelected)
        self.layout.addWidget(self.singleButton)
        self.layout.addWidget(self.multipleButton)

    def multipleSelected(self):
        self.selection = "multiple"
        self.accept()

class InputMultiDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(400,300)
        self.setWindowTitle('Input Mutiple Dialog')
        self.layout = QVBoxLayout(self)
        self.productIdLabel = QLabel('ProductId', self)
        self.productId = QLineEdit(self)
        self.layout.addWidget(self.productIdLabel)
        self.layout.addWidget(self.productId)
        # self.productIdLabel.setFont(QFont('Arial', 8))
        self.deviceSizeXLabel = QLabel('DeviceSizeX', self)
        self.deviceSizeX = QLineEdit(self)
        self.layout.addWidget(self.deviceSizeXLabel)
        self.layout.addWidget(self.deviceSizeX)
        self.deviceSizeYLabel = QLabel('DeviceSizeY', self)
        self.deviceSizeY = QLineEdit(self)
        self.layout.addWidget(self.deviceSizeYLabel)
        self.layout.addWidget(self.deviceSizeY)
        self.selectDirectoryButton = QPushButton('Select Directory', self)
        self.selectDirectoryButton.clicked.connect(self.openDirectoryDialog)
        self.layout.addWidget(self.selectDirectoryButton)
        self.doneButton = QPushButton('Done', self)
        self.doneButton.clicked.connect(self.accept)
        self.layout.addWidget(self.doneButton)
        self.cancelButton = QPushButton('Cancel', self)
        self.cancelButton.clicked.connect(self.close)  
        self.layout.addWidget(self.cancelButton)

    def openDirectoryDialog(self):
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()", "", options=options)
        if directory:
            self.selectDirectoryButton.setText(directory) 

    def accept(self):
        try:
            productId = self.productId
            deviceSizeX = self.deviceSizeX
            deviceSizeY = self.deviceSizeY
            current_time = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-4]  # Format as year, month, day, hour, minute, second, millisecond
            directory = self.selectDirectoryButton.text()
            print(f"Processing Directory: {directory}")
            # 獲取資料夾中的所有 .bak 文件
            bak_files = [f for f in os.listdir(directory)] # if f.endswith('.bak')
            for i, filename in enumerate(bak_files):
                print(f"Processing File {i+1}: {filename}")
                filepath = os.path.join(directory, filename)
                row_data_lines, wafer_number, rowct, colct, lot = read_bak_file(filepath)
                converted_data, count_F, count_1, count_X = convert_row_data(row_data_lines)
                # 如果當前文件是第一個文件，則調用 self.update_xml，否則，調用 self.update_multi_xml
                if i == 0:
                    update_xml(productId, deviceSizeX, deviceSizeY, converted_data, wafer_number, rowct, colct, lot, current_time, count_F, count_1, count_X)
                    smallest_wafer_number = wafer_number 
                else:
                    update_multi_xml(productId, deviceSizeX, deviceSizeY, converted_data, wafer_number, rowct, colct, lot, current_time, smallest_wafer_number, count_F, count_1, count_X)
            super().accept()
        except:
            import logging
            logging.basicConfig(filename='ParsingError.log', level=logging.DEBUG)
            logging.exception('Unexcepted Error')
            self.close()

def read_bak_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    row_data_lines = [line.split(':')[1].strip() for line in lines if line.startswith('RowData')]
    wafer_number = [line.split(':')[1].strip() for line in lines if line.startswith('WAFER')][0]
    rowct = [line.split(':')[1].strip() for line in lines if line.startswith('ROWCT')][0]
    colct = [line.split(':')[1].strip() for line in lines if line.startswith('COLCT')][0]
    lot = [line.split(':')[1].strip() for line in lines if line.startswith('LOT')][0]
    return row_data_lines, wafer_number, rowct, colct, lot

def convert_row_data(row_data_lines):
    converted_data = []
    count_F = 0
    count_1 = 0
    count_X = 0
    for line in row_data_lines:
        line = line.replace('__', 'F')
        line = line.replace('00', '1')
        line = line.replace('DF','X')
        # line = line.replace(' ', '')
        # print('line',line)
        line = re.sub(r'[^F1 ]', 'X', line)
        # print('line',line)
        # print('------------------------------------')
        line = line.replace('XX', 'X')
        line = line.replace(' ', '')
        converted_data.append(line)
        count_F += line.count('F')
        count_1 += line.count('1')
        count_X += line.count('X')
    return converted_data, count_F, count_1, count_X

def calculate_checksum(input_string):
        sum_ = 0
        input_string += 'A'
        input_string += '0'
        for char in input_string:
            sum_ = (sum_ * 8) % 59
            sum_ += ord(char)
            sum_ -= 32
            if sum_ > 59:
                sum_ -= 59
        print('sum',sum_)
        checksum = 59 - sum_
        print(checksum)
        binary_checksum = format(checksum, 'b').zfill(6)
        least_significant_three_bits = int(binary_checksum[-3:], 2)
        next_higher_three_bits = int(binary_checksum[-6:-3], 2) if len(binary_checksum) >= 6 else 0
        check_character_1 = chr(ord('A') + next_higher_three_bits)
        check_character_2 = chr(ord('0') + least_significant_three_bits)
        print('ch1',check_character_1)
        print('ch2',check_character_2)
        return check_character_1 + check_character_2

def update_xml(productId, deviceSizeX, deviceSizeY, converted_data, wafer_number, rowct, colct, lot, current_time, count_F, count_1, count_X):
        with open('template.xml', 'r') as file:
            xml_string = file.read()
        xml_string = xml_string.replace('ProductId="ACIPC60K0AA111"', f'ProductId="{productId.text()}"')
        xml_string = xml_string.replace('DeviceSizeX="180"', f'DeviceSizeX="{deviceSizeX.text()}"')
        xml_string = xml_string.replace('DeviceSizeY="240"', f'DeviceSizeY="{deviceSizeY.text()}"')
        # Get current date and time
        xml_string = xml_string.replace('CreateDate="2024071710275518"', f'CreateDate="{current_time}"')
        xml_string = xml_string.replace('LastModified="2024071710275518"', f'LastModified="{current_time}"')
        xml_string = xml_string.replace('SubstrateNumber="23"', f'SubstrateNumber="{wafer_number}"')
        xml_string = xml_string.replace('SlotNumber="23"', f'SlotNumber="{wafer_number}"')
        xml_string = xml_string.replace('Rows="10"', f'Rows="{rowct}"')
        xml_string = xml_string.replace('Columns="16"', f'Columns="{colct}"')
        # Update LotId and SubstrateId
        wafer_letter = chr(ord('A') + int(wafer_number) - 1)  # Convert wafer number to letter
        lot_id = lot + wafer_letter
        xml_string = xml_string.replace('LotId="MBZ289570W"', f'LotId="{lot_id}"')
        xml_string = xml_string.replace('MapName="MBZ289570W.XML"', f'MapName="{lot_id}.XML"')
        substrate_id = lot[:6] + '-' + wafer_number + '-' + calculate_checksum(lot[:6] + '-' + wafer_number + '-')
        xml_string = xml_string.replace('SubstrateId="MBZ289-23-B7"', f'SubstrateId="{substrate_id}"')
        xml_string = xml_string.replace('"Normal Pass" BinCount="100"',f'"Normal Pass" BinCount="{count_1}"')
        xml_string = xml_string.replace('"Normal Fail" BinCount="20"',f'"Normal Fail" BinCount="{count_X}"')
        xml_string = xml_string.replace('"NULL" BinCount="12"',f'"NULL" BinCount="{count_F}"')
        # print('X',count_X)
        # Find the position to replace
        start_index = xml_string.find('<Row><![CDATA[')
        end_index = xml_string.rfind(']]></Row>')  # Use rfind to get the last occurrence of ']]></Row>'
        if start_index != -1 and end_index != -1:
            # Remove the original Row elements
            xml_string = xml_string[:start_index] + xml_string[end_index+9:]
            # Add new Row elements
            # 遍歷每一行
            for i, line in enumerate(reversed(converted_data)):
                # 如果當前行是最後一行，則不添加換行符
                if i == 0:
                    row_string = '<Row><![CDATA[' + line + ']]></Row>'
                else:
                    row_string = '<Row><![CDATA[' + line + ']]></Row>\n'
                xml_string = xml_string[:start_index] + row_string + xml_string[start_index:]
        with open(f'{current_time}_APM_SEMI_MAP.xml', 'w') as file:
            file.write(xml_string)

def update_multi_xml(productId, deviceSizeX, deviceSizeY, converted_data , wafer_number, rowct, colct, lot, current_time, smallest_wafer_number, count_F, count_1, count_X):
    with open('template _multi.xml', 'r') as file:
        xml_template_string = file.read()
    xml_template_string = xml_template_string.replace('ProductId="ACIPC60K0AA111"', f'ProductId="{productId.text()}"')
    xml_template_string = xml_template_string.replace('DeviceSizeX="180"', f'DeviceSizeX="{deviceSizeX.text()}"')
    xml_template_string = xml_template_string.replace('DeviceSizeY="240"', f'DeviceSizeY="{deviceSizeY.text()}"')
    xml_template_string = xml_template_string.replace('CreateDate="2024071710275518"', f'CreateDate="{current_time}"')
    xml_template_string = xml_template_string.replace('LastModified="2024071710275518"', f'LastModified="{current_time}"')
    xml_template_string = xml_template_string.replace('SubstrateNumber="23"', f'SubstrateNumber="{wafer_number}"')
    xml_template_string = xml_template_string.replace('SlotNumber="23"', f'SlotNumber="{wafer_number}"')
    xml_template_string = xml_template_string.replace('Rows="10"', f'Rows="{rowct}"')
    xml_template_string = xml_template_string.replace('Columns="16"', f'Columns="{colct}"')
    # Update LotId and SubstrateId
    wafer_letter = chr(ord('A') + int(smallest_wafer_number) - 1)  # Convert wafer number to letter
    lot_id = lot + wafer_letter
    xml_template_string = xml_template_string.replace('LotId="MBZ289570W"', f'LotId="{lot_id}"')
    xml_template_string = xml_template_string.replace('MapName="MBZ289570W.XML"', f'MapName="{lot_id}.XML"')
    substrate_id = lot[:6] + '-' + wafer_number + '-' + calculate_checksum(lot[:6] + '-' + wafer_number + '-')
    xml_template_string = xml_template_string.replace('SubstrateId="MBZ289-23-B7"', f'SubstrateId="{substrate_id}"')
    xml_template_string =xml_template_string.replace('"Normal Pass" BinCount="100"',f'"Normal Pass" BinCount="{count_1}"')
    xml_template_string =xml_template_string.replace('"Normal Fail" BinCount="20"',f'"Normal Fail" BinCount="{count_X}"')
    xml_template_string =xml_template_string.replace('"NULL" BinCount="12"',f'"NULL" BinCount="{count_F}"')
    # Find the position to replace
    start_index = xml_template_string.find('<Row><![CDATA[')
    end_index = xml_template_string.rfind(']]></Row>')  # Use rfind to get the last occurrence of ']]></Row>'
    if start_index != -1 and end_index != -1:
        # Remove the original Row elements
        xml_template_string = xml_template_string[:start_index] + xml_template_string[end_index+9:]
        # Add new Row elements
        # 獲取行的數量
    for i, line in enumerate(reversed(converted_data)):
        # 如果當前行是最後一行，則不添加換行符
        if i == 0:
            row_string = '<Row><![CDATA[' + line + ']]></Row>'
        else:
            row_string = '<Row><![CDATA[' + line + ']]></Row>\n'
        xml_template_string = xml_template_string[:start_index] + row_string + xml_template_string[start_index:]

    # 讀取文件內容
    with open(f'{current_time}_APM_SEMI_MAP.xml', 'r') as file:
        file_content = file.read()
    # 在指定的位置插入 xml_template_string
    # start_index = file_content.find('</Map>') + len('</Map>')
    end_index = file_content.find('</Maps>')
    # insert_position = 50  # 替換這個值成想要插入的位置
    file_content = file_content[:end_index-1] + '\n' +xml_template_string + '\n' +file_content[end_index:]

    # 將結果寫回文件
    with open(f'{current_time}_APM_SEMI_MAP.xml', 'w') as file:
        file.write(file_content)

if __name__ == '__main__':
    app = QApplication([])
    ex = SelectionDialog()
    if ex.exec_() == QDialog.Accepted:
        if ex.selection == "multiple":
            dialog = InputMultiDialog()
            dialog.exec_()
    # a = calculate_checksum('MBZ252-15-')
    # print(a)
    

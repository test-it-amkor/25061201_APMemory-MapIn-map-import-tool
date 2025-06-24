from PyQt5.QtWidgets import QApplication, QDialog, QInputDialog, QLineEdit, QVBoxLayout, QPushButton, QFormLayout, QDialogButtonBox, QFileDialog
from PyQt5.QtCore import Qt
from datetime import datetime
import os

class InputDialog(QDialog):  # Change QWidget to QDialog
    def __init__(self, converted_data, wafer_number, rowct, colct, lot):
        super().__init__()
        self.converted_data = converted_data
        self.wafer_number = wafer_number
        self.rowct = rowct
        self.colct = colct
        self.lot = lot
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Input Dialog')

        self.layout = QFormLayout(self)

        self.productId = QLineEdit(self)
        self.deviceSizeX = QLineEdit(self)
        self.deviceSizeY = QLineEdit(self)

        self.layout.addRow('ProductId', self.productId)
        self.layout.addRow('DeviceSizeX', self.deviceSizeX)
        self.layout.addRow('DeviceSizeY', self.deviceSizeY)

        self.fileButton = QPushButton('Select File', self)
        self.fileButton.clicked.connect(self.openFileNameDialog)
        self.layout.addRow(self.fileButton)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addRow(self.buttons)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            self.fileName = fileName
            self.fileButton.setText(os.path.basename(fileName))  # Update the button text with the selected file name

    def accept(self):
        self.update_xml()
        super().accept()

    def calculate_checksum(self, input_string):
        # Initialize the sum
        sum_ = 0

        # Iterate over each character in the input string
        for char in input_string:
            # Add the ASCII value of the current character to the sum
            sum_ += ord(char)
            sum_ -=32
            # Multiply the sum by 8 and take the remainder when divided by 59
            sum_ = (sum_ * 8) % 59
            # If the sum is greater than or equal to 59, subtract 59
            if sum_ >= 59:
                sum_ -= 59

        # Calculate the final checksum
        checksum = 59 - sum_

        # Convert the checksum to binary
        binary_checksum = format(checksum, 'b').zfill(6)

        # Calculate the least significant three bits and the next higher three bits
        least_significant_three_bits = int(binary_checksum[-3:], 2)
        next_higher_three_bits = int(binary_checksum[-6:-3], 2) if len(binary_checksum) >= 6 else 0

        # Calculate the ASCII values of the check characters
        check_character_1 = chr(ord('A') + next_higher_three_bits)
        check_character_2 = chr(ord('0') + least_significant_three_bits)

        # Return the check characters
        return check_character_1 + check_character_2

    def update_xml(self):
        with open('template.xml', 'r') as file:
            xml_string = file.read()

        xml_string = xml_string.replace('ProductId="ACIPC60K0AA111"', f'ProductId="{self.productId.text()}"')
        xml_string = xml_string.replace('DeviceSizeX="180"', f'DeviceSizeX="{self.deviceSizeX.text()}"')
        xml_string = xml_string.replace('DeviceSizeY="240"', f'DeviceSizeY="{self.deviceSizeY.text()}"')

        # Get current date and time
        now = datetime.now()
        current_time = now.strftime("%Y%m%d%H%M%S%f")[:-4]  # Format as year, month, day, hour, minute, second, millisecond

        xml_string = xml_string.replace('CreateDate="2024071710275518"', f'CreateDate="{current_time}"')
        xml_string = xml_string.replace('LastModified="2024071710275518"', f'LastModified="{current_time}"')
        xml_string = xml_string.replace('SubstrateNumber="23"', f'SubstrateNumber="{self.wafer_number}"')
        xml_string = xml_string.replace('SlotNumber="23"', f'SlotNumber="{self.wafer_number}"')
        xml_string = xml_string.replace('Rows="10"', f'Rows="{self.rowct}"')
        xml_string = xml_string.replace('Columns="16"', f'Columns="{self.colct}"')

        # Update LotId and SubstrateId
        wafer_letter = chr(ord('A') + int(self.wafer_number) - 1)  # Convert wafer number to letter
        lot_id = self.lot + wafer_letter
        xml_string = xml_string.replace('LotId="MBZ289570W"', f'LotId="{lot_id}"')
        substrate_id = self.lot[:6] + '-' + self.wafer_number + '-' + self.calculate_checksum(self.lot[:6] + '-' + self.wafer_number)
        xml_string = xml_string.replace('SubstrateId="MBZ289-23-B7"', f'SubstrateId="{substrate_id}"')

        # Find the position to replace
        start_index = xml_string.find('<Row><![CDATA[')
        end_index = xml_string.rfind(']]></Row>')  # Use rfind to get the last occurrence of ']]></Row>'

        if start_index != -1 and end_index != -1:
            # Remove the original Row elements
            xml_string = xml_string[:start_index] + xml_string[end_index+9:]
            # Add new Row elements
            for line in reversed(self.converted_data):  # Note that the reversed function is used here to reverse the data order
                row_string = '<Row><![CDATA[' + line + ']]></Row>\n'
                xml_string = xml_string[:start_index] + row_string + xml_string[start_index:]

        with open('output.xml', 'w') as file:
            file.write(xml_string)


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
    for line in row_data_lines:
        line = line.replace('__', 'F')
        line = line.replace('00', '1')
        line = line.replace('PT', 'X')
        line = line.replace('DC', 'X')
        line = line.replace(' ', '')
        converted_data.append(line)
    return converted_data


if __name__ == '__main__':
    # Example usage
    row_data_lines, wafer_number, rowct, colct, lot = read_bak_file('input.bak')
    converted_data = convert_row_data(row_data_lines)
    app = QApplication([])
    ex = InputDialog(converted_data, wafer_number, rowct, colct, lot)
    ex.exec_()

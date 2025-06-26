import os, shutil, re
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
from modules.cfg import get_export_path, get_sinf_dl_path
from modules.log import write_log


class Map:
  """
  用來存放 Map 的資訊, 等待匯入進 XML 檔案內容中
  """

  def __init__(
    self,
    target_device: str,
    die_size_x: float,
    die_size_y: float,
    row_infos: list,
    wafer_id: str,
    row_ct: str,
    col_ct: str,
    lot: str,
    cnt_f: int,
    cnt_1: int,
    cnt_x: int
  ):
    self.target_device = target_device
    self.die_size_x = die_size_x
    self.die_size_y = die_size_y
    self.row_infos = row_infos
    self.wafer_id = wafer_id
    self.row_ct = row_ct
    self.col_ct = col_ct
    self.lot = lot
    self.cnt_f = str(cnt_f)
    self.cnt_1 = str(cnt_1)
    self.cnt_x = str(cnt_x)
    self.substrate_id = self.get_substrate_id()
    self.curr_time = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-4]

  def set_lot_no(self, wafer_letter: str):
    """
    設置 lot_no
    p.s. 此實例的 lot_no 與其他 lot_id 意義不同, 故命名為 let_no 作為區別

    Arguments:
      - wafer_letter (str): 最小刻度轉換而得的英文字母
    """
    self.lot_no = f"{self.lot}{wafer_letter}"

  def get_substrate_id(self):
    """取得 substrate_id"""
    return f"{self.lot[:6]}-{self.wafer_id}-{self.get_checksum()}"

  def get_checksum(self) -> str:
    """計算 checksum"""
    default_str = f"{self.lot[:6]}-{self.wafer_id}-A0"

    num = 0
    for char in default_str:
      num = (num * 8) % 59
      num += ord(char)
      num -= 32
      if num > 59:
        num -= 59
    num = 59 - num

    binary_num = format(num, "b").zfill(6)
    least_significant_three_bits = int(binary_num[-3:], 2)
    next_higher_three_bits = int(binary_num[-6:-3], 2) if len(binary_num) >= 6 else 0

    check_char_1 = chr(ord("A") + next_higher_three_bits)
    check_char_2 = chr(ord("0") + least_significant_three_bits)
    checksum = check_char_1 + check_char_2
    write_log(f"Wafer ID {self.wafer_id} checksum value is: {checksum}", "info")
    return checksum


def rm_export_folder():
  """移除 export 資料夾"""

  export_path = get_export_path()
  if os.path.exists(export_path) and os.path.isdir(export_path):
    try:
      shutil.rmtree(export_path)
      write_log(f"Removed export folder", "info")
    except Exception:
      return "RemoveExportError"


def get_info_from_sinf(dl_path, lot_id, number) -> dict | str:
  """
  從 SINF map 檔案中取得 waferId, lot, rowDataList, rowCt, colCt

  Arguments:
    dl_path (str): SINF map 檔案的下載資料夾路徑
    lot_id (str): Lot ID, 用來取得 SINF map 檔案路徑
    number (str): SINF map 檔案的副檔名, 意義等同於 Wafer ID

  Returns:
    dict: 包含 waferId, lot, rowDataList, rowCt, colCt 的字典
      - waferId (str): Wafer ID
      - lot (str): Lot ID
      - rowDataList (list): RowData 的內容
      - rowCt (str): map 行數
      - colCt (str): map 欄數
    str: 如果讀取失敗則回傳 "SinfReadError"
  """

  try:
    sinf_path = os.path.join(dl_path, f"{lot_id}.{number}")
    with open(sinf_path, "r") as file:
      lines = file.readlines()
      #讀取 WAFER 欄位 (wafer ID)
      wafer_id = [line.split(":")[1].strip() for line in lines if line.startswith("WAFER")][0]
      #讀取 LOT 欄位 (lot ID)
      lot = [line.split(":")[1].strip() for line in lines if line.startswith("LOT")][0]
      #讀取 RowData 欄位 (RowData 就是 map, 有多行)
      row_data_list = [line.split(":")[1].strip() for line in lines if line.startswith("RowData")]
      #讀取 ROWCT 欄位 (map 行數)
      row_ct = [line.split(":")[1].strip() for line in lines if line.startswith("ROWCT")][0]
      #讀取 COLCT 欄位 (map 欄數)
      col_ct = [line.split(":")[1].strip() for line in lines if line.startswith("COLCT")][0]

      return {
        "waferId": wafer_id,
        "lot": lot,
        "rowDataList": row_data_list,
        "rowCt": row_ct,
        "colCt": col_ct
      }

  except Exception as e:
    write_log(f"Error reading SINF map file: {lot_id}.{number}, error: {e}", "error")
    return "SinfReadError"


def handle_row_data(row_data_list: list) -> dict:
  """
  處理 RowData 的內容, 轉置為客製格式

  Arguments:
    row_data_list (list): RowData 的內容

  Returns:
    dict: 包含處理後的結果
    - rowDataResult (list): 處理後的 RowData 列表
    - cntF (int): "F" 的計數
    - cnt1 (int): "1" 的計數
    - cntX (int): "X" 的計數
  """

  result = []
  cnt_f = 0
  cnt_1 = 0
  cnt_x = 0
  for row_data in row_data_list:
    row_data = row_data.strip().replace("__", "F").replace("00", "1").replace("DF","X")
    row_data = re.sub(r"[^F1 ]", "X", row_data)
    row_data = row_data.replace("XX", "X").replace(" ", "")
    result.append(row_data)
    cnt_f += row_data.count("F")
    cnt_1 += row_data.count("1")
    cnt_x += row_data.count("X")
  return {
    "rowDataResult": result,
    "cntF": cnt_f,
    "cnt1": cnt_1,
    "cntX": cnt_x
  }


def generate_xml(map: Map):
  """
  生成 XML 檔案的內容

  Arguments:
    map (Map): Map 實例, 包含所有需要的資訊

  Returns:
    Element: Map 為根元素的 XML 內容
  """

  #Map 元素
  map_el = etree.Element("Map")
  map_el.set("xmlns", "http://www.semi.org")
  map_el.set("SubstrateType", "Wafer")
  map_el.set("SubstrateId", map.substrate_id)
  map_el.set("FormatRevision", "SEMI G85-0703")

  #Device 元素
  device_el = etree.SubElement(map_el, "Device")
  device_el.set("BinType", "Ascii")
  device_el.set("LotId", map.lot_no)
  device_el.set("SubstrateNumber", map.wafer_id)
  device_el.set("SlotNumber", map.wafer_id)
  device_el.set("Status", "")
  device_el.set("DeviceSizeX", str(map.die_size_x))
  device_el.set("DeviceSizeY", str(map.die_size_y))
  device_el.set("FrameId", "")
  device_el.set("NullBin", "")
  device_el.set("ProductId", map.target_device)
  device_el.set("SupplierName", "AMKOR")
  device_el.set("Rows", map.row_ct)
  device_el.set("Columns", map.col_ct)
  device_el.set("MapType", "Array")
  device_el.set("OriginLocation", "2")
  device_el.set("Orientation", "0")
  device_el.set("WaferSize", "300")
  device_el.set("CreateDate", map.curr_time)
  device_el.set("LastModified", map.curr_time)

  #ReferenceDevice 元素
  ref_device_el = etree.SubElement(device_el, "ReferenceDevice")
  ref_device_el.set("ReferenceDeviceX", "1")
  ref_device_el.set("ReferenceDeviceY", "1")
  ref_device_el.set("RefDevicePosX", "")
  ref_device_el.set("RefDevicePosY", "")

  #Bin 1 元素
  bin_el_1 = etree.SubElement(device_el, "Bin")
  bin_el_1.set("BinCode", "1")
  bin_el_1.set("BinQuality", "Pass")
  bin_el_1.set("BinDescription", "Normal Pass")
  bin_el_1.set("BinCount", map.cnt_1)

  #Bin X 元素
  bin_el_x = etree.SubElement(device_el, "Bin")
  bin_el_x.set("BinCode", "X")
  bin_el_x.set("BinQuality", "Fail")
  bin_el_x.set("BinDescription", "Normal Fail")
  bin_el_x.set("BinCount", map.cnt_x)

  #Bin F 元素
  bin_el_x = etree.SubElement(device_el, "Bin")
  bin_el_x.set("BinCode", "F")
  bin_el_x.set("BinQuality", "NULL")
  bin_el_x.set("BinDescription", "NULL")
  bin_el_x.set("BinCount", map.cnt_f)

  #Data 元素
  data_el = etree.SubElement(device_el, "Data")
  data_el.set("MapName", f"{map.lot_no}.XML")
  data_el.set("MapVersion", "")

  #Row 元素
  for row_data in map.row_infos:
    row_el = etree.SubElement(data_el, "Row")
    modified_data = row_data.replace("]]>", "]]]]><![CDATA[>")
    row_el.text = etree.CDATA(modified_data)
  return map_el


def export_xml(lot_id, target_device, die_size_x, die_size_y):
  """
  匯出 XML 檔案到 export 資料夾

  Arguments:
    lot_id (str): 貨批號碼, 例如 "AADZHS000"
    target_device (str): 讀取 WO 資訊組成, 例如 "ACIPCD0K0BA111"
    die_size_x (float): 從 SINF map 中取得
    die_size_y (float): 從 SINF map 中取得

  Returns:
    - str: 如果匯出成功, 則回傳匯出的 XML file path
    - str: 如果失敗則回傳 error key, 例如 "SinfReadError", "ExportXmlError"
  """

  try:
    #取得匯出資料夾路徑
    export_path = get_export_path()
    os.makedirs(export_path, exist_ok=True)

    #生成 XML 根元素 Maps
    maps_el = etree.Element("Maps")

    #遍歷 SINF map 的下載資料夾
    dl_path = get_sinf_dl_path(lot_id, f"APC_{lot_id}")

    #取得最小刻號, 規則為取每批第一片 wafer id, 再轉換為英文字母
    #例如: #2~#25, 取 #2 轉為英文字母 "B"
    wafer_ids = [int(file.split(".")[-1]) for file in os.listdir(dl_path)]
    wafer_ids.sort()
    min_id = wafer_ids[0]
    wafer_letter = chr(ord("A") + int(min_id) - 1)

    for file in os.listdir(dl_path):
      #取得單片 SINF map 檔案資訊
      number = file.split(".")[-1]  #取得副檔名作為 number
      sinf_info = get_info_from_sinf(dl_path, lot_id, number)
      if sinf_info == "SinfReadError":
        return "SinfReadError"
      wafer_id = sinf_info["waferId"]
      lot = sinf_info["lot"]
      row_data_list = sinf_info["rowDataList"]
      row_ct = sinf_info["rowCt"]
      col_ct = sinf_info["colCt"]

      #客製化處理 RowData 內容
      processed_row_data = handle_row_data(row_data_list)
      row_data_result = processed_row_data["rowDataResult"]
      cnt_f = processed_row_data["cntF"]
      cnt_1 = processed_row_data["cnt1"]
      cnt_x = processed_row_data["cntX"]

      #創建 Map 實例, 將 SINF map 資訊存進此實例中
      map_inst = Map(target_device, die_size_x, die_size_y, row_data_result,
                      wafer_id, row_ct, col_ct, lot, cnt_f, cnt_1, cnt_x)
      map_inst.set_lot_no(wafer_letter)

      #生成 XML 內容
      xml_content = generate_xml(map_inst)
      maps_el.append(xml_content)

    #取得待寫入的 XML 內容
    xml_path = rf"{export_path}/{map_inst.lot_no}.xml"
    #產生 XML 並保留 CDATA
    xml_bytes = etree.tostring(maps_el, encoding="utf-8", pretty_print=True, xml_declaration=False)
    #將 XML 內容寫入檔案
    with open(xml_path, "wb") as xml_file:
      xml_file.write(b'<?xml version="1.0" ?>\n')
      xml_file.write(xml_bytes)
      write_log(f"Export to XML successfully, lot ID: {lot_id}", "success")
      return xml_path

  except Exception as e:
    write_log(f"Error exporting XML for lot {lot_id}: {e}", "error")
    return "ExportXmlError"

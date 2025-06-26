import os, shutil
from modules.cfg import get_export_path, get_upload_path, get_xml_bak_path
from modules.log import write_log
from modules.xml import rm_export_folder


def upload_xml(xml_path: str) -> str | None:
  """
  上傳 XML 檔案到 AWMS 的指定路徑

  Arguments:
    xml_path (str): XML 檔案匯出的路徑

  Returns:
    None: 如果上傳成功, 則回傳 None
    str: 如果失敗則回傳 error key, 例如 "XmlNotFoundError", "UploadError" 等
  """

  try:
    #取得 AWMS 上傳路徑
    upload_path = get_upload_path()
    #確保目標上傳資料夾存在
    os.makedirs(upload_path, exist_ok=True)

    #XML 檔案的路徑
    xml_filename = os.path.basename(xml_path)
    #檢查 XML 檔案是否存在
    if not os.path.exists(xml_path) or not os.path.isfile(xml_path):
      return "XmlNotFoundError"

    #複製 XML 檔案到上傳資料夾路徑
    dst_path = os.path.join(upload_path, rf"{xml_filename}")
    with open(xml_path, "rb") as src, open(dst_path, "wb") as dst:
      dst.write(src.read())

    #上傳完成後, 複製一份 XML map 到備份資料夾
    xml_bak_path = get_xml_bak_path()
    #確保備份資料夾存在
    os.makedirs(xml_bak_path, exist_ok=True)
    shutil.copy(xml_path, rf"{xml_bak_path}/{xml_filename}")
    write_log(f"Copy XML backup to: {xml_bak_path}", "info")
    #移除 XML 匯出資料夾
    rm_export_folder()
    write_log(f"XML uploaded to: {dst_path}", "info")
    return None

  except Exception as e:
    write_log(f"Error uploading XML file {xml_filename}: {e}", "error")
    return "UploadError"


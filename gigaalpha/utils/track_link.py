import os, json, logging
from gigaalpha.helpers.system import System

logger = logging.getLogger(__name__)


def update_drive_link_json(json_path: str, new_items: dict):
    '''Ghi đè hoặc cập nhật log link Google Drive vào file JSON.'''
    data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path,'r',encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.warning(f"[LinkTracker] Error reading existing JSON file: {e}")
    data['0_last_update_vn'] = System.get_now_vn().strftime('%d/%m/%Y %H:%M:%S')
    data.update(new_items)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"[LinkTracker] Saved Drive link log to: {json_path}")

def update_html_link_txt(txt_path: str, new_items: dict):
    '''Ghi đè hoặc cập nhật log link HTML (GitHub Pages) vào file TXT dưới dạng Hyperlink.'''
    existing = {}
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    if " : " in line:
                        k, v = line.strip().split(" : ", 1)
                        existing[k] = v
        except Exception as e:
            logger.warning(f"[LinkTracker] Error reading existing txt file: {e}")

    now_str = System.get_now_vn().strftime('%d/%m/%Y %H:%M:%S')
    
    # Format lại link thành Hyperlink cho Google Sheet
    formatted_items = {k: f'=HYPERLINK("{v}", "📊 View 3D chart")' for k, v in new_items.items()}
    existing.update(formatted_items)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"last_update_vn: {now_str}\n")
        f.write("-" * 60 + "\n")
        for key in existing.keys():
            f.write(f"{key} : {existing[key]}\n")
    logger.info(f"[LinkTracker] Saved HTML link log to: {txt_path}")
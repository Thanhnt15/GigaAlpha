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

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"[LinkTracker] Saved Drive link log to: {json_path}")
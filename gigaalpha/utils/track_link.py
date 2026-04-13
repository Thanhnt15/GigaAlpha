import os, json, logging
from gigaalpha.helpers.system import System

logger = logging.getLogger(__name__)

class LinkTracker:
    @staticmethod
    def update_drive_json(json_path: str, new_items: dict):
        '''Overwrite or update the Google Sheet link log when uploading to Google Drive'''
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

    @staticmethod
    def update_github_txt(txt_path: str, new_items: dict):
        '''Overwrite or update the HTML link log when deploying to Github Pages'''
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
        existing.update(new_items)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"last_update_vn: {now_str}\n")
            f.write("-" * 60 + "\n")
            for key in existing.keys():
                f.write(f"{key} : {existing[key]}\n")
        logger.info(f"[LinkTracker] Saved Github link log to: {txt_path}")
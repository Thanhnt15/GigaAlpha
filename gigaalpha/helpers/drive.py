import os, pickle, socket, time, logging, random
from typing import List, Optional, Dict
from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

class GDrive:
    """Google Drive API v3 Interaction Tools - Production Ready."""
    
    SCOPES: List[str] = ['https://www.googleapis.com/auth/drive']

    @staticmethod
    def generate_pickle(json_secret_path: str, output_pickle_path: str) -> None:
        """Generate a .pickle authentication file from a secret .json file."""
        creds = None
        if os.path.exists(output_pickle_path):
            with open(output_pickle_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(json_secret_path, GDrive.SCOPES)
                try:
                    creds = flow.run_local_server(port=0)
                except Exception:
                    creds = flow.run_console()
            
            with open(output_pickle_path, 'wb') as token:
                pickle.dump(creds, token)
            logger.info(f"[GDrive] Successfully created authentication file: {output_pickle_path}")

    @staticmethod
    def _get_service(token_path: str) -> Optional[Resource]:
        """Initialize a universal Service with automatic refresh mechanism."""
        if not os.path.exists(token_path):
            logger.error(f"[GDrive] Token file not found at: {token_path}")
            return None
        
        try:
            creds = None
            # Try to load as authorized user file (json)
            try:
                creds = Credentials.from_authorized_user_file(token_path, GDrive.SCOPES)
            except:
                # If failed, try to load as pickle
                with open(token_path, 'rb') as f:
                    creds = pickle.load(f)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.debug("[GDrive] Token expired, automatically refreshing...")
                    creds.refresh(Request())
                    # Save the refreshed token
                    if token_path.endswith('.json'):
                        with open(token_path, 'w') as f: f.write(creds.to_json())
                    else:
                        with open(token_path, 'wb') as f: pickle.dump(creds, f)

            socket.setdefaulttimeout(600)
            return build('drive', 'v3', credentials=creds, static_discovery=False)
        except Exception as e:
            logger.error(f"[GDrive] Service initialization failed: {e}")
            return None

    @staticmethod
    def sync_file(
        service: Resource, 
        local_path: str, 
        drive_name: str, 
        folder_id: str, 
        convert_to_gsheet: bool = True, 
        max_retries: int = 3
    ) -> Optional[str]:
        """Upload bytes to Drive. Returns file_id on success."""
        for attempt in range(max_retries):
            try:
                media = MediaFileUpload(local_path, resumable=True, chunksize=5*1024*1024)
                query = f"name = '{drive_name}' and '{folder_id}' in parents and trashed = false"
                if convert_to_gsheet:
                    query += " and mimeType = 'application/vnd.google-apps.spreadsheet'"
                
                results = service.files().list(q=query, fields="files(id)").execute()
                files = results.get('files', [])

                if files:
                    fid = files[0]['id']
                    logger.debug(f"[GDrive] Updating existing file: {fid}")
                    request = service.files().update(fileId=fid, media_body=media)
                else:
                    meta = {'name': drive_name, 'parents': [folder_id]}
                    if convert_to_gsheet:
                        meta['mimeType'] = 'application/vnd.google-apps.spreadsheet'
                    logger.debug(f"[GDrive] Creating new file...")
                    request = service.files().create(body=meta, media_body=media, fields='id')

                response = None
                last_printed_progress = -1  
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        current_progress = int(status.progress() * 100)
                        if current_progress % 25 == 0 and current_progress != last_printed_progress:
                            logger.debug(f"[GDrive] Uploading status: {current_progress}%...")
                            last_printed_progress = current_progress

                return response.get('id')

            except Exception as e:
                err_str = str(e)
                logger.debug(f"DEBUG ERROR: {err_str}")
                if any(x in err_str for x in ["500", "503", "504", "403", "429", "socket", "rateLimit", "Too Many Requests", "User Rate Limit"]):
                    wait_time = (2 ** attempt) * 5 + random.uniform(0, 5)
                    logger.warning(f"[GDrive] Network or API Rate Limit error. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"[GDrive] sync_file failed: {e}")
                break
        return None
    
    @classmethod
    def upload_files(
        cls, 
        token_path: str,
        file_paths: List[str], 
        target_folder_id: str, 
        share_emails: Optional[List[str]] = None,
        convert_to_gsheet: bool = True
    ) -> Dict[str, str]:
        """Main interface to upload a list of files to Drive. Returns {filename: link}."""
        service = cls._get_service(token_path)
        if not service: return {}
        
        success_links = {}
        list_emails = [e.strip() for e in share_emails if e.strip()] if share_emails else []

        for f_path in file_paths:
            full_path = os.path.abspath(f_path)
            if not os.path.isfile(full_path):
                logger.warning(f"[GDrive] File not found: {full_path}")
                continue
            
            fname = os.path.basename(full_path)
            drive_name = fname.replace('.xlsx', '') if fname.endswith('.xlsx') and convert_to_gsheet else fname
            
            # Execute SYNC FILE
            file_id = cls.sync_file(service, full_path, drive_name, target_folder_id, convert_to_gsheet)
        
            if file_id:
                new_link = f"https://docs.google.com/spreadsheets/d/{file_id}" if convert_to_gsheet else f"https://drive.google.com/file/d/{file_id}/view"
                
                # Configure permissions
                try:
                    if not list_emails:
                        service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
                    else:
                        for email in list_emails:
                            service.permissions().create(
                                fileId=file_id,
                                body={'type': 'user', 'role': 'writer', 'emailAddress': email},
                                sendNotificationEmail=False
                            ).execute()
                except Exception as e:
                    logger.warning(f"[GDrive] Permission configuration error: {e}")
                
                logger.info(f"[GDrive] Successfully uploaded: {full_path}")
                success_links[fname] = new_link
            else:
                logger.error(f"[GDrive] Failed to upload: {full_path}")

        return success_links
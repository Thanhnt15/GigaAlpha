# Cloud Synchronization & Report Distribution Guide

This guide provides technical specifications and setup procedures for the automated distribution and persistence of GigaAlpha analytics. The system uses **Google Drive** as the primary cloud channel for structural archival of Excel-based research results. Interactive HTML visualizations are stored locally in `outputs/html/`.

---

## I. Google Drive Integration (Data Persistence)

GigaAlpha utilizes the Google Drive API v3 to securely upload and organize Excel-based results.

### 1. Enable Google Drive API
1.  Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project or select an existing one.
3.  Go to **APIs & Services > Library** and search for "Google Drive API".
4.  Enable the API.

### 2. Configure OAuth 2.0 Credentials
1.  Go to **APIs & Services > Credentials**.
2.  Configure the **OAuth Consent Screen** (Standard/External is sufficient).
3.  Click **Create Credentials > OAuth client ID**.
4.  Select **Desktop app** as the application type.
5.  Download the JSON file and rename it to `credentials.json` in your project root.

### 3. Generate Authentication Token
GigaAlpha requires a persistent `token.pickle` (or `.json`) file to operate without interactive login. Use the built-in helper to authorize your environment:

```bash
python3 -c "from gigaalpha.helpers.drive import GDrive; GDrive.generate_pickle('credentials.json', 'token.pickle')"
```
*A browser window will open requesting access permissions. Once granted, a success message will appear and `token.pickle` will be generated.*

### 4. Application Setup
Update your `.env` file with the generated token path:
```env
GDRIVE_TOKEN_PATH="/absolute/path/to/GigaAlpha/token.pickle"
```

---

## II. Unified Configuration Summary

Ensure the following blocks are configured in your YAML manifest:

```yaml
upload:
  enabled: true
  target_folder_id: "YOUR_GOOGLE_DRIVE_FOLDER_ID"
```

---
*GigaAlpha — Enterprise-grade automation for quantitative research distribution.* 🚀

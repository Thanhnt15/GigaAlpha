# Cloud Synchronization & Report Distribution Guide

This guide provides technical specifications and setup procedures for the automated distribution and persistence of GigaAlpha analytics. The system supports two primary cloud channels: **Interactive Web Hosting** (for visual exploration) and **Data Persistence** (for structural archival).

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

## II. GitHub Pages Hosting (Visual Reports)

Interactive 3D HTML charts are hosted via GitHub Pages for centralized visual research.

### 1. Repository Preparation
1.  **Fork** the repository to your personal account.
2.  Ensure you have established SSH or Personal Access Token (PAT) authentication for Git in your local environment.

### 2. GitHub Configuration
1.  Go to your fork's **Settings > Pages**.
2.  Under **Build and deployment > Source**, ensure `Deploy from a branch` is selected.
3.  Under **Branch**, select `gh-pages` and save.
    *   *Note: If the `gh-pages` branch is not visible, it will be automatically created upon the first successful scan run.*

### 3. Execution
Enable deployment in your configuration (`deploy: enabled: true`). The system will automatically:
- Synchronize local HTML artifacts with the remote web branch.
- Log accessible URLs to `logs/html_links.txt`.

---

## III. Automated Run with Token (Portable Mode)

The most convenient way for automated servers or distributed research is using a **GitHub Personal Access Token (PAT)**. This allows anyone to clone and run the system by simply providing a token in the `.env` file.

### 1. Generate GitHub PAT
1.  Go to **GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)**.
2.  Click **Generate new token (classic)**.
3.  Select scopes: `repo` (all) and `workflow`.
4.  Copy the generated token immediately.

### 2. Configure Environment
Add the following line to your `.env` file:
```env
GITHUB_TOKEN="your_ghp_token_value_here"
```

*The GigaAlpha engine will automatically detect this token and use it to authenticate all Git push operations during the scan.*

---

## IV. Unified Configuration Summary

Ensure the following blocks are configured in your YAML manifest:

```yaml
upload:
  enabled: true
  target_folder_id: "YOUR_GOOGLE_DRIVE_FOLDER_ID"

deploy:
  enabled: true
  branch: "gh-pages"
```

---
*GigaAlpha — Enterprise-grade automation for quantitative research distribution.* 🚀

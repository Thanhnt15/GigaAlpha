# Technical Guide: Automated Telegram Monitoring Setup

This document provides a comprehensive protocol for provisioning and integrating a Telegram-based alerting layer into the GigaAlpha research pipeline.

## 1. Bot Provisioning via BotFather

Telegram bots are managed through the official **BotFather** interface. Follow these steps to generate a secure API token:

1.  **Initiate Conversation**: Search for [@BotFather](https://t.me/botfather) in Telegram.
2.  **Create Bot**: Send the `/newbot` command.
3.  **Naming Convention**: 
    -   Provide a **Display Name** (e.g., `GigaAlpha Monitor`).
    -   Provide a unique **Username** ending in `_bot` (e.g., `gigaalpha_research_bot`).
4.  **Secure the Token**: BotFather will return an **HTTP API Token**. 
    > [!CAUTION]
    > Treat this token as a private key. Disclosure allows unauthorized entities to intercept logs or push malicious alerts to your endpoints.

## 2. Collaborative Group Integration

To facilitate distributed monitoring across multiple stakeholders or servers, integration into a Telegram Group is recommended:

1.  **Create Group**: Create a new Private Group (e.g., `GigaAlpha Alerts`).
2.  **Add Bot**: Invite your newly created bot to the group.
3.  **Administrator Privileges**: Promote the bot to an **Administrator**. Ensure it has permissions to "Post Messages".

## 3. Extracting the Numerical Chat ID

The GigaAlpha engine requires a unique numerical identifier (`CHAT_ID`) to route alerts. Use one of the following validated methods:

### Method A: Using a Diagnostic Bot (Recommended)
1.  Invite [@userinfobot](https://t.me/userinfobot) or [@GetIDsBot](https://t.me/GetIDsBot) to your group.
2.  The bot will automatically display the **Group ID** (usually a negative number starting with `-100...`).
3.  Remove the diagnostic bot after obtaining the ID.

### Method B: Manual API Call
Perform a `GET` request to the Telegram API after sending a test message in the group:
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
Look for the `chat` object in the JSON response to find the `id` field.

## 4. Environment Synchronization

Once credentials are secured, update your local `.env` file at the project root:

```env
# --- TELEGRAM MONITORING CONFIGURATION ---
TELEGRAM_BOT_TOKEN=123456789:ABCDefghIJKLmnopQRSTuvwxYZ
TELEGRAM_CHAT_ID=-100123456789
```

> [!NOTE]
> The GigaAlpha logging engine automatically detects these variables at runtime. No further pipeline modification is required.

## 5. Verification

To verify the integration, execute the following diagnostic command:

```bash
python gigaalpha/scripts/scan.py --config configs/scan_large.yaml
```

If configured correctly, you will receive a **Success Notification** upon pipeline completion, or a structured **Error Alert** if the execution encounters issues.

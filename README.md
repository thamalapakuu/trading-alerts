# Trading Alert Bot Setup Guide

This guide walks you through setting up your own copy of the Trading Alert Bot from scratch. It uses a Telegram bot, an FXCM demo account, and Railway hosting. Pushover notifications are optional.

> Security first: Never share your Telegram bot token, FXCM password, Pushover keys, or Railway variables. Do not commit them to GitHub or paste them into chats/screenshots.

## 1. Copy the bot to your GitHub account

1. Open the source repository: [trading-alert-bot](https://github.com/maligireddydineshreddy/trading-alert-bot).
2. Create your own copy:
   - Click **Fork** to copy it directly into your GitHub account, or
   - Download the repository and upload it to a new GitHub repository.
3. Confirm the repository is visible in your GitHub account. You will select it when deploying to Railway.

## 2. Create your Telegram bot

1. Open Telegram on your phone or desktop.
2. Search for **@BotFather** and open the official bot.
3. Send `/start`.
4. Send `/newbot`.
5. Follow the prompts:
   - Enter a display name for the bot.
   - Enter a unique username. Telegram bot usernames normally end in `bot`.
6. BotFather will provide a token. Copy it and save it securely; this is your `BOT_TOKEN`.

If the token is ever exposed, use BotFather to revoke and replace it, then update Railway with the new value.

## 3. Create an FXCM demo account

1. Open the FXCM demo signup page: [FXCM Trading Station demo](https://www.fxcm.com/markets/platforms/trading-station/free-demo/).
2. Complete the demo-account form and select **UAE** if that is appropriate for you.
3. Provide accurate, valid account details and complete any verification requested by FXCM. The original setup process mentioned using a random phone number; do not do this—use truthful information and follow FXCM’s current requirements.
4. Click **Trade Now** (or the equivalent current button).
5. Save the demo-account credentials FXCM provides:
   - Username → `FXCM_USERNAME`
   - Password → `FXCM_PASSWORD`

> FXCM’s signup screens and requirements can change. Follow the current FXCM instructions shown during registration.

## 4. Create a Railway project

1. Go to [Railway](https://railway.com/).
2. Sign in with GitHub.
3. Authorize Railway’s GitHub connection when prompted.
4. Allow Railway access to the GitHub repository you created in Step 1.
5. Create a new project and choose **Deploy from GitHub Repo**.
6. Select your copy of `trading-alert-bot`.

Railway should begin building the project automatically.

## 5. Add persistent storage

The bot saves alerts and Pushover user settings in a local database. A Railway volume keeps that data when the service restarts or redeploys.

1. In Railway, open your bot’s service.
2. Add a **Volume**.
3. Set its mount path to:

   ```text
   /app/data
   ```

## 6. Set the service region and replica count

1. Open the service’s **Settings** in Railway.
2. Find **Scale**.
3. Set the region to **Southeast Asia (Singapore)**.
4. Set **Replicas** to **1**.

Using one replica is important because this bot uses a local SQLite database stored in the mounted volume.

## 7. Add Railway variables

Open your Railway service, then open **Variables**. Add these values:

| Variable | Value |
|---|---|
| `BOT_TOKEN` | The token supplied by BotFather |
| `FXCM_USERNAME` | Your FXCM demo-account username |
| `FXCM_PASSWORD` | Your FXCM demo-account password |
| `FXCM_URL` | `https://www.fxcorporate.com/Hosts.jsp` |
| `PUSHOVER_APP_TOKEN` | Your Pushover application token — optional |

After saving the variables, Railway should redeploy the service automatically. Check the deployment logs for a successful bot startup.

## 8. Optional: configure Pushover notifications

Pushover can send emergency-priority alerts to the Pushover app on your phone.

### Create the Pushover application token

1. Go to [Pushover](https://pushover.net/) and create an account.
2. Install the Pushover app on your Android or iPhone.
3. Verify your email address.
4. On the Pushover website, open **Your Applications**.
5. Choose **Create an Application/API Token**.
6. Enter a name for the application, accept the required checkbox, and create it.
7. Copy the generated application/API token.
8. In Railway, set that token as `PUSHOVER_APP_TOKEN`.

### Connect your personal Pushover account inside Telegram

The Railway variable is the application token; the bot also needs your personal Pushover **User Key**.

1. Open your Telegram bot.
2. Tap **🔔 Notification Settings**.
3. Tap **🔑 Enter Pushover Key**.
4. Paste your Pushover User Key when the bot asks for it.

After connection, the menu changes to offer:

- **🧪 Test Alert** — sends a test Pushover notification.
- **🔄 Change User Key** — replaces your saved Pushover User Key.
- **❌ Disable Pushover** — turns off Pushover notifications for your Telegram user.

You can alternatively send `/setpush YOUR_PUSHOVER_USER_KEY` to the bot.

## 9. Start the Telegram bot

1. Open Telegram.
2. Find the bot you created. If you cannot find it, open your earlier BotFather messages and tap the bot link.
3. Tap **Start** or send:

   ```text
   /start
   ```

The bot displays its main menu.

## 10. What each bot button does

### Main menu

- **📈 Add Alert** — creates a new price alert.
- **📋 My Alerts** — shows your active alerts, including symbol, target, and direction.
- **🗑 Remove Alert** — lets you select one or more alerts and delete them.
- **🔔 Notification Settings** — connects and manages optional Pushover notifications.
- **ℹ️ Status** — checks the bot, FXCM, and Binance connection status.

### Creating an alert

1. Tap **📈 Add Alert**.
2. Choose a market:
   - **💱 Forex**
   - **🪙 Crypto**
   - **🥇 Commodities**
   - **📊 Indices**
3. Select a listed symbol, or use the manual-entry option:
   - Forex: `EURUSD`, `GBPUSD`, `USDJPY`, `GBPJPY`, or **✏️ Enter Forex Pair**
   - Crypto: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `XRPUSDT`, or **✍️ Enter Crypto Pair**
   - Commodities: `XAUUSD`, `XAGUSD`, `USOIL`, `COPPER`, or **✍️ Enter Commodity**
   - Indices: `SPX500`, `US30`, or **✏️ Enter Index**
4. The bot shows the current price and asks for a target price. Send a number, for example `1.08500` or `65000`.
5. The bot automatically decides whether the alert is for price moving **ABOVE** or **BELOW** your target, then starts monitoring it.
6. Use **⬅️ Back** at any menu stage to return to the previous screen.

### Removing alerts

1. Tap **🗑 Remove Alert**.
2. Tap each alert you want to remove. A selected alert receives a ✅ mark.
3. Tap **🗑 Delete Selected** to remove the selected alerts.

The bot is an alerting tool. Start with a demo account, validate prices and notifications yourself, and make independent trading decisions.

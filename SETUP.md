# Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)

### 2. Installation Steps

```bash
# Clone or download the repository
cd discord-bot

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your details
# Add your DISCORD_TOKEN and OWNER_ID
```

### 3. Configuration

Edit the `.env` file:
```
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=your_discord_user_id_here
```

**How to get your Discord User ID:**
1. Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
2. Right-click your username and select "Copy ID"

**How to get a Bot Token:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under the bot's username, click "Reset Token" and copy it
6. Enable all "Privileged Gateway Intents" (Presence, Server Members, Message Content)

### 4. Bot Permissions

When inviting the bot to your server, use these permissions:
- Administrator (recommended for full functionality)

Or individual permissions:
- Manage Roles
- Manage Channels
- Kick Members
- Ban Members
- Manage Messages
- View Audit Log
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Connect (Voice)
- Speak (Voice)
- Move Members (Voice)

**Invite URL Generator:**
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=8&scope=bot
```
Replace `YOUR_BOT_CLIENT_ID` with your bot's client ID from the Developer Portal.

### 5. Running the Bot

```bash
python main.py
```

If successful, you'll see:
```
Bot is ready! Logged in as BotName (123456789)
Connected to X guilds
------
Loaded cogs.logging
Loaded cogs.antinuke
Loaded cogs.moderation
Loaded cogs.roles
Loaded cogs.voicechannel
Loaded cogs.roleplay
Loaded cogs.settings
```

## Initial Server Setup

Once the bot is running and in your server:

### 1. Setup Logging Channels

```
.setuplog messages
.setuplog voice
.setuplog roles
.setuplog antinuke
```

For each command, the bot will ask if you want to create a new channel or use an existing one.

### 2. Setup Jail System (for Anti-Nuke)

Create a jail role or use an existing one:
```
.jail role @JailRole
```

Optionally set a jail channel:
```
.jail channel #jail-channel
```

### 3. Configure Anti-Nuke Thresholds

Set thresholds for actions (example: 5 bans per 1 hour):
```
.antinuke threshold ban 5 1
.antinuke threshold kick 5 1
.antinuke threshold role_delete 3 1
.antinuke threshold channel_delete 3 1
.antinuke threshold webhook_create 5 1
```

### 4. Add Anti-Nuke Whitelist

Whitelist trusted users/roles:
```
.whitelist add @TrustedUser
.whitelist add @AdminRole
```

### 5. Enable Roleplay Commands (Optional)

```
.roleplay on
```

Add custom GIFs for roleplay commands:
```
.rolegif hug https://example.com/hug.gif
```

## Common Issues

### Bot doesn't respond
- Check that the bot is online in your server
- Ensure the bot has Read Messages and Send Messages permissions
- Verify your .env file has the correct token
- Check that Message Content Intent is enabled in Discord Developer Portal

### Bot can't execute moderation commands
- Ensure the bot has the required permissions (Kick Members, Ban Members, etc.)
- Make sure the bot's role is higher than the roles it's trying to manage
- Check that you're using commands as the server owner or with admin permissions

### Anti-nuke not working
- Ensure you've set thresholds using `.antinuke threshold`
- Check that the jail role is configured with `.jail role`
- Verify the bot has "View Audit Log" permission
- Make sure the user triggering actions is not whitelisted

### Logging not working
- Ensure log channels are set up with `.setuplog <type>`
- Check that the bot has Send Messages and Embed Links permissions in log channels
- Verify the bot has "View Audit Log" permission for attribution in logs

## Updating the Bot

```bash
# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart the bot
python main.py
```

## Support Commands

- `.ghelp` - View all admin commands (Administrator only)
- Test if bot is responsive with any command like `.hug` (if roleplay is enabled)

## Data Backup

The bot stores all data in the `data/` directory as JSON files. To backup:

```bash
# Create a backup
cp -r data/ data_backup_$(date +%Y%m%d)/
```

To restore:
```bash
# Stop the bot
# Copy backup files
cp -r data_backup_YYYYMMDD/* data/
# Start the bot
```

## Security Notes

- Never share your bot token
- Keep the `.env` file secure and never commit it to git
- Regularly review hardban and fake permission lists
- Only grant hardban permissions to highly trusted users
- Whitelist anti-nuke users carefully to prevent abuse

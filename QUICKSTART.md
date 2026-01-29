# Quick Start Guide

Get your Discord bot up and running in 5 minutes!

## Prerequisites
- Python 3.8+
- A Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- Your Discord User ID (Enable Developer Mode in Discord, right-click your name, Copy ID)

## Installation (5 Steps)

### 1. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Bot
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your details
# Set DISCORD_TOKEN and OWNER_ID
```

### 3. Run the Bot
```bash
python main.py
```

You should see:
```
Bot is ready! Logged in as YourBot (123456789)
Connected to X guilds
------
Loaded cogs.logging
Loaded cogs.antinuke
...
```

### 4. Initial Server Setup (In Discord)

Run these commands in your Discord server:

```
.setuplog messages
.setuplog voice
.setuplog roles
.setuplog antinuke
```

For each, react with 1️⃣ to create a new channel or 2️⃣ to use existing.

### 5. Configure Anti-Nuke (Optional but Recommended)

```
.jail role @JailRole
.antinuke threshold ban 5 1
.antinuke threshold kick 5 1
.whitelist add @TrustedRole
```

## Essential Commands

### For Server Owner
```
.ghelp                              # View all commands
.whitelist add @user                # Add to anti-nuke whitelist
.antinuke threshold ban 5 1         # 5 bans per 1 hour triggers anti-nuke
.jail role @JailRole                # Set jail role
.hbpermsadd @Moderator              # Grant hardban permission
.fakeperm add @Moderator ban kick   # Grant fake ban/kick permissions
.roleplay on                        # Enable roleplay commands
```

### For Moderators
```
.ban @user [reason]                 # Ban a user
.kick @user [reason]                # Kick a user
.hb @user <reason>                  # Hardban a user (if permission granted)
.cls 50                             # Delete 50 messages
.r @user @RoleName                  # Assign role
```

### For Everyone (if roleplay enabled)
```
.hug @user                          # Hug someone
.dance                              # Dance
.wave @user                         # Wave at someone
```

### Voice Channel Owners
```
.vc lock                            # Lock your VC
.vc trust @user                     # Allow user to join locked VC
.vc block @user                     # Block user from VC
.vc limit 5                         # Set user limit to 5
.vc rename My Cool VC               # Rename VC
```

## Bot Invite URL

Replace `YOUR_BOT_CLIENT_ID` with your bot's client ID:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=8&scope=bot
```

**Permissions Code `8` = Administrator** (recommended for full functionality)

## Troubleshooting

### Bot doesn't respond
- ✅ Check bot is online in Discord
- ✅ Verify bot has "Read Messages" and "Send Messages" permissions
- ✅ Ensure "Message Content Intent" is enabled in Discord Developer Portal
- ✅ Check .env file has correct token

### Commands don't work
- ✅ Make sure you're using the correct prefix: `.` (period)
- ✅ Verify you have the required permissions (Owner/Admin)
- ✅ Check bot is not rate-limited

### Anti-nuke not working
- ✅ Set thresholds: `.antinuke threshold <action> <count> <hours>`
- ✅ Configure jail role: `.jail role @JailRole`
- ✅ Bot needs "View Audit Log" permission
- ✅ Ensure triggering user is not whitelisted

## File Structure

```
discord-bot/
├── main.py              # Start here
├── config.py            # Configuration
├── cogs/                # Bot features
│   ├── antinuke.py     # Anti-nuke protection
│   ├── logging.py      # Message/voice/role logs
│   ├── moderation.py   # Ban/kick/hardban
│   ├── roles.py        # Role management
│   ├── voicechannel.py # VC system
│   ├── roleplay.py     # 94 roleplay commands
│   └── settings.py     # Admin settings
└── utils/               # Helper functions
```

## Data Storage

All data stored in `data/` directory (auto-created):
- `config.json` - Server settings
- `hardbans.json` - Hardban list
- `fake_perms.json` - Fake permissions
- `roleplay_gifs.json` - Custom GIFs
- `vc_data.json` - Voice channel data
- `antinuke_data.json` - Whitelist & thresholds

**Backup regularly:** `cp -r data/ backup/`

## Next Steps

1. ✅ Read [SETUP.md](SETUP.md) for detailed configuration
2. ✅ Read [README.md](README.md) for complete feature list
3. ✅ Read [FEATURES.md](FEATURES.md) for feature checklist
4. ✅ Configure anti-nuke thresholds for your server size
5. ✅ Set up roleplay commands and add custom GIFs
6. ✅ Grant permissions to trusted moderators

## Support

- Check logs in terminal for errors
- Verify bot permissions in server settings
- Ensure intents are enabled in Developer Portal
- Test with `.ghelp` command

## Quick Test

After setup, test if bot is working:

```
.ghelp          # Should show command list (Admin only)
.roleplay on    # Enable roleplay (Owner only)
.hug            # Test roleplay command (Everyone)
```

If all three work, you're ready to go! 🎉

---

**Need help?** Check the other documentation files:
- [SETUP.md](SETUP.md) - Detailed setup instructions
- [README.md](README.md) - Complete feature documentation
- [FEATURES.md](FEATURES.md) - Feature checklist

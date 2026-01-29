# Discord Community Management Bot

A comprehensive Python Discord bot for community server management with anti-nuke protection, logging systems, moderation tools, voice channel management, and roleplay commands.

## Features

### 1. Anti-Nuke System
- Owner-only whitelist system for users and roles
- Configurable thresholds for mass actions (bans, kicks, role deletions, channel deletions, webhook spam)
- Automatic punishment: Jail users by removing all roles and adding jail role
- Logs all violations to dedicated anti-nuke log channel

### 2. Comprehensive Logging System
- **Message Logs**: Track deleted messages with full details
- **Voice Logs**: Monitor voice channel activity (joins, leaves, streaming, duration tracking)
- **Role Logs**: Track role creation, assignment, and removal with attribution
- **Anti-nuke Logs**: Document all anti-nuke violations and punishments

### 3. Role Management
- `.r <user> <role>` or `.role <user> <role>` - Assign roles
- `.role remove <user> <role>` - Remove roles
- All actions logged with attribution

### 4. Moderation Commands

#### Basic Moderation
- `.ban <user> [reason]` - Ban a user
- `.kick <user> [reason]` - Kick a user
- `.cls <amount>` - Bulk delete messages (max 100)
- `.ghelp` - Display comprehensive admin command overview

#### Hardban System (Owner-level)
- `.hb <user> <reason>` - Hardban a user from the guild
- `.unhb <user>` - Remove hardban
- `.hblist <page>` - View all hardbanned users (paginated)
- Auto-rebans users when someone tries to unban them
- Funny warnings for staff who try to unban hardbanned users

#### Hardban Permissions (Owner only)
- `.hbpermsadd @user/@role` - Grant hardban permission
- `.hbpermsrem @user/@role` - Remove hardban permission

#### Fake Permissions (Owner only)
Bot-based command permissions system. Users with fake permissions can only use bot commands, not actual Discord permissions.
- `.fakeperm add @user/@role <perms>` - Add fake permissions
- `.fakeperm remove @user/@role <perms>` - Remove fake permissions
- `.fakeperm list <page>` - View all fake permission grants
- `.fakeperm check @user` - Check user's fake permissions

### 5. Voice Channel (VC) System with Dashboard

#### VC Commands
- `.vc claim` - Claim a VC if owner hasn't been in it for 30+ seconds
- `.vc lock/unlock` - Lock/unlock the VC
- `.vc trust @user` - Add user to trusted list
- `.vc untrust @user` - Remove user from trusted list
- `.vc block @user` - Block user (auto-disconnect + deny permissions)
- `.vc unblock @user` - Unblock user
- `.vc disconnect @user` - Disconnect user from VC
- `.vc limit <number>` - Set max user limit
- `.vc transfer @user` - Transfer ownership
- `.vc rename <new_name>` - Rename the VC
- `.vc delete` - Delete the VC

#### VC Dashboard
Interactive dashboard posted when VC is created/claimed showing:
- Current owner, member count, limit, lock status
- Blocked users list, trusted users list
- All available commands with descriptions

### 6. Roleplay Commands (94 total)

#### Roleplay System Toggle
- `.roleplay on/off` - Enable/disable roleplay commands (Admin only)
- `.rolegif <command> <gif_url>` - Add custom gif for roleplay command (Admin only)

#### Interaction Commands (30)
.hug, .kiss, .airkiss, .pat, .slap, .poke, .cuddle, .holdhands, .highfive, .bite, .tickle, .brofist, .cheers, .clap, .handhold, .lick, .love, .nom, .nuzzle, .pinch, .smack, .sorry, .thumbsup, .punch, .rpkick, .bonk, .stare, .wave, .yeet

#### Emote/Action Commands (64)
.yes, .dance, .run, .jump, .hide, .sleep, .eat, .drink, .headbang, .peek, .shrug, .sip, .yawn, .cry, .laugh, .blush, .pout, .smile, .wink, .angry, .angrystare, .confused, .facepalm, .happy, .mad, .nervous, .sad, .scared, .shy, .sigh, .smug, .surprised, .sweat, .tired, .woah, .yay, .bleh, .celebrate, .cool, .drool, .evillaugh, .nyah, .shout, .slowclap, .sneeze, .explode

### 7. Admin Settings & Configuration

#### Logging Setup
- `.setuplog messages` - Configure message log channel
- `.setuplog voice` - Configure voice log channel
- `.setuplog roles` - Configure role log channel
- `.setuplog antinuke` - Configure anti-nuke log channel

#### Anti-nuke Configuration
- `.whitelist add @user/@role` - Add to anti-nuke whitelist
- `.whitelist remove @user/@role` - Remove from whitelist
- `.antinuke threshold <action> <count> <hours>` - Set thresholds

Actions: ban, kick, role_delete, channel_delete, webhook_create

#### Jail System
- `.jail role <role>` - Set jail role (can use external role for multi-bot compatibility)
- `.jail channel <channel>` - Set jail channel

#### Log Permissions
- `.logperms <logtype> <role>` - Grant role access to log channel

### 8. Multi-Bot Compatibility
- Assign external jail roles/channels to work with other bots' jail systems
- Configure via `.jail role <role>` and `.jail channel <channel>`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd discord-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` and add your bot token and owner ID:
```
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=your_discord_user_id_here
```

5. Run the bot:
```bash
python main.py
```

## Configuration

All configuration is stored in JSON files in the `data/` directory:
- `config.json` - Guild settings
- `hardbans.json` - Hardban data
- `fake_perms.json` - Fake permissions
- `roleplay_gifs.json` - Roleplay command GIFs
- `vc_data.json` - Voice channel data
- `antinuke_data.json` - Anti-nuke whitelist and thresholds

## Requirements

- Python 3.8+
- discord.py 2.3.0+
- python-dotenv 1.0.0+
- aiofiles 23.0.0+

## Project Structure

```
discord-bot/
├── main.py                 # Bot entry point
├── config.py              # Configuration loader
├── cogs/                  # Bot cogs/modules
│   ├── antinuke.py       # Anti-nuke system
│   ├── logging.py        # Logging system
│   ├── moderation.py     # Moderation commands
│   ├── roles.py          # Role management
│   ├── voicechannel.py   # Voice channel system
│   ├── roleplay.py       # Roleplay commands
│   └── settings.py       # Admin settings
├── utils/                # Utility modules
│   ├── checks.py         # Permission checks
│   ├── formatting.py     # Message formatting
│   ├── config_manager.py # Configuration management
│   └── vc_manager.py     # Voice channel management
├── data/                 # Data storage (created automatically)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create from .env.example)
└── README.md            # This file
```

## Permission Requirements

The bot requires the following Discord permissions:
- Administrator (for full functionality)
- Or individually: Manage Roles, Manage Channels, Kick Members, Ban Members, Manage Messages, View Audit Log, Connect, Move Members

## Support

For issues, questions, or feature requests, please open an issue on the repository.

## License

This project is provided as-is for community server management purposes.

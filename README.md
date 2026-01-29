# Discord Bot - Production Ready

A fully featured, production-ready Discord bot with all intents configured and every feature implemented.

## ✨ Features

### 🛡️ Anti-Nuke System
- **Ban Detection** - Monitors mass banning activities
- **Kick Detection** - Tracks mass kick activities
- **Role Deletion Detection** - Alerts on mass role deletions
- **Channel Deletion Detection** - Monitors channel deletion
- **Webhook Spam Detection** - Prevents webhook abuse
- **Auto-Jail** - Automatically jails malicious users
- **Whitelist System** - Exempt trusted users from anti-nuke

### 📝 Logging System
- **Message Deletion Logging** - Track deleted messages
- **Voice Channel Activity** - Join/leave/switch/stream tracking
- **Role Creation & Updates** - Monitor role changes
- **Member Role Updates** - Track role assignments

### 🔨 Moderation
- **Ban/Kick** - Standard moderation commands
- **Hardban** - Permanent bans with auto-reban detection
- **Hardban List** - View all hardbanned users
- **Bulk Delete** - Clear messages (up to 100)
- **Fake Permissions** - Bot-based permission system

### 🎙️ Voice Channel Management
- **VC Ownership** - Claim and manage voice channels
- **Trust System** - Add trusted users
- **Block System** - Block users from VC
- **Lock/Unlock** - Control VC access
- **User Limits** - Set maximum users
- **Transfer Ownership** - Give VC to another user
- **Rename/Delete** - Manage VC settings

### 💕 Roleplay (94 Commands)
**Interaction Commands (29):**
hug, kiss, airkiss, pat, slap, poke, cuddle, holdhands, highfive, bite, tickle, brofist, cheers, clap, handhold, lick, love, nom, nuzzle, pinch, smack, sorry, thumbsup, punch, rpkick, bonk, stare, wave, yeet

**Emote Commands (65):**
yes, dance, run, jump, hide, sleep, eat, drink, headbang, peek, shrug, sip, yawn, cry, laugh, blush, pout, smile, wink, angry, angrystare, confused, facepalm, happy, mad, nervous, sad, scared, shy, sigh, smug, surprised, sweat, tired, woah, yay, bleh, celebrate, cool, drool, evillaugh, nyah, shout, slowclap, sneeze, explode

### ⚙️ Settings
- **Anti-Nuke Thresholds** - Configure detection sensitivity
- **Jail System** - Set jail role and channel
- **Log Permissions** - Grant role access to logs
- **Roleplay Toggle** - Enable/disable roleplay commands
- **Custom GIFs** - Set custom images for roleplay

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
```env
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=your_discord_user_id_here
```

### 3. Run the Bot
```bash
python main.py
```

## 📋 Command Reference

### Moderation Commands
| Command | Description |
|---------|-------------|
| `.ban <user> [reason]` | Ban a user |
| `.kick <user> [reason]` | Kick a user |
| `.hb <user> <reason>` | Hardban a user |
| `.unhb <user>` | Remove hardban |
| `.hblist [page]` | List hardbanned users |
| `.cls [amount]` | Bulk delete messages |

### Anti-Nuke Commands
| Command | Description |
|---------|-------------|
| `.whitelist add @user/@role` | Add to whitelist |
| `.whitelist remove @user/@role` | Remove from whitelist |
| `.whitelist list` | View whitelist |
| `.antinuke threshold <action> <count> <hours>` | Set thresholds |

### Role Commands
| Command | Description |
|---------|-------------|
| `.r <user> <role>` | Assign role |
| `.role <user> <role>` | Assign role (long form) |
| `.role remove <user> <role>` | Remove role |

### Voice Channel Commands
| Command | Description |
|---------|-------------|
| `.vc claim` | Claim an unowned VC |
| `.vc lock/unlock` | Lock/unlock VC |
| `.vc trust @user` | Add trusted user |
| `.vc untrust @user` | Remove trusted user |
| `.vc block @user` | Block user from VC |
| `.vc unblock @user` | Unblock user |
| `.vc disconnect @user` | Disconnect user |
| `.vc limit <number>` | Set user limit |
| `.vc transfer @user` | Transfer ownership |
| `.vc rename <name>` | Rename VC |
| `.vc delete` | Delete VC |
| `.vc help` | Show VC commands |

### Roleplay Commands
| Command | Description |
|---------|-------------|
| `.hug @user` | Hug a user |
| `.kiss @user` | Kiss a user |
| `.pat @user` | Pat a user |
| `.slap @user` | Slap a user |
| `.dance` | Dance |
| `.sleep` | Sleep |
| `.cry` | Cry |
| `.laugh` | Laugh |
| ... | And 84 more! |

### Settings Commands
| Command | Description |
|---------|-------------|
| `.roleplay on/off` | Toggle roleplay |
| `.rolegif <cmd> <url>` | Set custom GIF |
| `.jail role <@role>` | Set jail role |
| `.jail channel <#channel>` | Set jail channel |
| `.setuplog <type>` | Setup logging |
| `.logperms <type> <@role>` | Grant log access |

### Admin Commands
| Command | Description |
|---------|-------------|
| `.ghelp` | Show all admin commands |
| `.fakeperm add/remove/list/check` | Manage fake permissions |
| `.hbpermsadd/rem` | Manage hardban permissions |

## 🔧 Configuration

### Anti-Nuke Thresholds
Configure detection sensitivity:
```
.antinuke threshold ban 5 1      # 5 bans per hour
.antinuke threshold kick 5 1     # 5 kicks per hour
.antinuke threshold role_delete 3 1  # 3 role deletes per hour
.antinuke threshold channel_delete 3 1  # 3 channel deletes per hour
.antinuke threshold webhook_create 5 1  # 5 webhooks per hour
```

### Logging Setup
```
.setuplog messages   # Setup message logging
.setuplog voice      # Setup voice logging
.setuplog roles      # Setup role logging
.setuplog antinuke   # Setup anti-nuke logging
```

## 📁 Data Files

The bot stores data in the `data/` directory:
- `config.json` - Guild configuration
- `hardbans.json` - Hardban data
- `fake_perms.json` - Fake permissions
- `roleplay_gifs.json` - Custom roleplay GIFs
- `vc_data.json` - Voice channel data
- `antinuke_data.json` - Anti-nuke settings

## 🔐 Permissions Required

The bot requires these permissions:
- Manage Roles
- Manage Channels
- Ban Members
- Kick Members
- Manage Messages
- View Audit Log
- Send Messages
- Embed Links
- Manage Nicknames

## 🛠️ Development

### Project Structure
```
├── main.py              # Bot entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── cogs/                # Command modules
│   ├── antinuke.py     # Anti-nuke system
│   ├── logging.py      # Logging system
│   ├── moderation.py   # Moderation commands
│   ├── roles.py        # Role management
│   ├── roleplay.py     # Roleplay commands
│   ├── settings.py     # Settings commands
│   └── voicechannel.py # Voice channel management
└── utils/              # Utilities
    ├── config_manager.py   # JSON management
    ├── vc_manager.py       # VC data management
    ├── checks.py           # Permission checks
    └── formatting.py       # Embed helpers
```

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

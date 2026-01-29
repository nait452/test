# Command Reference

Complete list of all bot commands organized by category.

## Command Prefix
All commands use the `.` (period) prefix.

---

## 📋 Admin Commands

### Setup & Configuration

#### `.ghelp`
**Permission:** Administrator  
**Description:** Display comprehensive admin command overview  
**Usage:** `.ghelp`

#### `.setuplog <type>`
**Permission:** Administrator  
**Description:** Configure log channels (messages, voice, roles, antinuke)  
**Usage:** 
- `.setuplog messages` - Setup message logging
- `.setuplog voice` - Setup voice logging
- `.setuplog roles` - Setup role logging
- `.setuplog antinuke` - Setup anti-nuke logging

#### `.logperms <logtype> <role>`
**Permission:** Administrator  
**Description:** Grant role access to log channels  
**Usage:** `.logperms messages @Moderators`

---

## 🛡️ Anti-Nuke Commands

### Whitelist Management

#### `.whitelist add <@user/@role>`
**Permission:** Owner  
**Description:** Add user or role to anti-nuke whitelist  
**Usage:** 
- `.whitelist add @TrustedUser`
- `.whitelist add @AdminRole`

#### `.whitelist remove <@user/@role>`
**Permission:** Owner  
**Description:** Remove user or role from anti-nuke whitelist  
**Usage:** 
- `.whitelist remove @User`
- `.whitelist remove @Role`

### Threshold Configuration

#### `.antinuke threshold <action> <count> <hours>`
**Permission:** Owner  
**Description:** Set anti-nuke thresholds  
**Actions:** ban, kick, role_delete, channel_delete, webhook_create  
**Usage:** 
- `.antinuke threshold ban 5 1` - 5 bans per 1 hour triggers anti-nuke
- `.antinuke threshold kick 10 2` - 10 kicks per 2 hours

---

## 🔨 Moderation Commands

### Basic Moderation

#### `.ban <user> [reason]`
**Permission:** Ban Members (or fake ban permission)  
**Description:** Ban a user from the server  
**Usage:** 
- `.ban @User`
- `.ban @User Spamming`

#### `.kick <user> [reason]`
**Permission:** Kick Members (or fake kick permission)  
**Description:** Kick a user from the server  
**Usage:** 
- `.kick @User`
- `.kick @User Breaking rules`

#### `.cls <amount>`
**Permission:** Administrator  
**Description:** Bulk delete messages (max 100)  
**Usage:** 
- `.cls` - Delete 100 messages
- `.cls 50` - Delete 50 messages

### Hardban System

#### `.hb <user> <reason>`
**Permission:** Hardban permission (Owner grants)  
**Description:** Hardban a user (auto-rebans if someone unbans)  
**Usage:** `.hb @User Serious violation`

#### `.unhb <user>`
**Permission:** Hardban permission (only who hardbanned)  
**Description:** Remove hardban from a user  
**Usage:** `.unhb @User`

#### `.hblist [page]`
**Permission:** Hardban permission  
**Description:** View all hardbanned users (paginated)  
**Usage:** 
- `.hblist` - Page 1
- `.hblist 2` - Page 2

#### `.hbpermsadd <@user/@role>`
**Permission:** Owner  
**Description:** Grant hardban permission  
**Usage:** 
- `.hbpermsadd @Moderator`
- `.hbpermsadd @AdminRole`

#### `.hbpermsrem <@user/@role>`
**Permission:** Owner  
**Description:** Remove hardban permission  
**Usage:** 
- `.hbpermsrem @User`
- `.hbpermsrem @Role`

---

## 🎭 Fake Permissions

#### `.fakeperm add <@user/@role> <perms...>`
**Permission:** Owner  
**Description:** Add fake permissions (bot-based command permissions)  
**Available perms:** ban, kick, role  
**Usage:** 
- `.fakeperm add @User ban kick`
- `.fakeperm add @ModRole ban kick role`

#### `.fakeperm remove <@user/@role> <perms...>`
**Permission:** Owner  
**Description:** Remove fake permissions  
**Usage:** `.fakeperm remove @User ban`

#### `.fakeperm list [page]`
**Permission:** Owner  
**Description:** View all fake permission grants (paginated)  
**Usage:** 
- `.fakeperm list`
- `.fakeperm list 2`

#### `.fakeperm check <@user>`
**Permission:** Owner  
**Description:** Check what fake permissions a user has  
**Usage:** `.fakeperm check @User`

---

## 👥 Role Management

#### `.r <user> <role>` / `.role <user> <role>`
**Permission:** Manage Roles (or fake role permission)  
**Description:** Assign a role to a user  
**Usage:** 
- `.r @User @RoleName`
- `.role @User @RoleName`

#### `.role remove <user> <role>`
**Permission:** Manage Roles (or fake role permission)  
**Description:** Remove a role from a user  
**Usage:** `.role remove @User @RoleName`

---

## 🎙️ Voice Channel Commands

### VC Management

#### `.vc claim`
**Permission:** In voice channel  
**Description:** Claim VC if owner left 30+ seconds ago  
**Usage:** `.vc claim`

#### `.vc lock` / `.vc unlock`
**Permission:** VC owner  
**Description:** Lock/unlock the voice channel  
**Usage:** 
- `.vc lock`
- `.vc unlock`

#### `.vc trust <@user>` / `.vc untrust <@user>`
**Permission:** VC owner  
**Description:** Add/remove user from trusted list (can join locked VC)  
**Usage:** 
- `.vc trust @User`
- `.vc untrust @User`

#### `.vc block <@user>` / `.vc unblock <@user>`
**Permission:** VC owner  
**Description:** Block/unblock user from VC (auto-disconnect + deny permissions)  
**Usage:** 
- `.vc block @User`
- `.vc unblock @User`

#### `.vc disconnect <@user>`
**Permission:** VC owner  
**Description:** Disconnect a user from the VC  
**Usage:** `.vc disconnect @User`

#### `.vc limit <number>`
**Permission:** VC owner  
**Description:** Set user limit (0-99, 0=unlimited)  
**Usage:** 
- `.vc limit 5`
- `.vc limit 0` - Unlimited

#### `.vc transfer <@user>`
**Permission:** VC owner  
**Description:** Transfer ownership to another user  
**Usage:** `.vc transfer @User`

#### `.vc rename <new_name>`
**Permission:** VC owner  
**Description:** Rename the voice channel  
**Usage:** `.vc rename My Cool VC`

#### `.vc delete`
**Permission:** VC owner  
**Description:** Delete the voice channel  
**Usage:** `.vc delete`

---

## 🎭 Roleplay Commands

### System Control

#### `.roleplay <on/off>`
**Permission:** Administrator  
**Description:** Enable or disable roleplay commands  
**Usage:** 
- `.roleplay on`
- `.roleplay off`

#### `.rolegif <command> <gif_url>`
**Permission:** Administrator  
**Description:** Add/update custom gif for a roleplay command  
**Usage:** `.rolegif hug https://example.com/hug.gif`

### Interaction Commands (30)
All support both standalone and mention usage.

**.hug** [user] - Hug someone  
**.kiss** [user] - Kiss someone  
**.airkiss** [user] - Air kiss  
**.pat** [user] - Pat someone  
**.slap** [user] - Slap someone  
**.poke** [user] - Poke someone  
**.cuddle** [user] - Cuddle someone  
**.holdhands** [user] - Hold hands  
**.highfive** [user] - High five  
**.bite** [user] - Bite someone  
**.tickle** [user] - Tickle someone  
**.brofist** [user] - Brofist  
**.cheers** [user] - Cheers  
**.clap** [user] - Clap  
**.handhold** [user] - Hold hands  
**.lick** [user] - Lick someone  
**.love** [user] - Show love  
**.nom** [user] - Nom someone  
**.nuzzle** [user] - Nuzzle someone  
**.pinch** [user] - Pinch someone  
**.smack** [user] - Smack someone  
**.sorry** [user] - Apologize  
**.thumbsup** [user] - Thumbs up  
**.punch** [user] - Punch someone  
**.rpkick** [user] - Kick someone (roleplay)  
**.bonk** [user] - Bonk someone  
**.stare** [user] - Stare at someone  
**.wave** [user] - Wave at someone  
**.yeet** [user] - Yeet someone  

**Usage examples:**
- `.hug` - Hug yourself
- `.hug @User` - Hug someone

### Emote/Action Commands (64)
Self-action commands (no target).

**.yes** - Say yes  
**.dance** - Dance  
**.run** - Run  
**.jump** - Jump  
**.hide** - Hide  
**.sleep** - Sleep  
**.eat** - Eat  
**.drink** - Drink  
**.headbang** - Headbang  
**.peek** - Peek  
**.shrug** - Shrug  
**.sip** - Sip  
**.yawn** - Yawn  
**.cry** - Cry  
**.laugh** - Laugh  
**.blush** - Blush  
**.pout** - Pout  
**.smile** - Smile  
**.wink** - Wink  
**.angry** - Look angry  
**.angrystare** - Angry stare  
**.confused** - Look confused  
**.facepalm** - Facepalm  
**.happy** - Look happy  
**.mad** - Look mad  
**.nervous** - Look nervous  
**.sad** - Look sad  
**.scared** - Look scared  
**.shy** - Look shy  
**.sigh** - Sigh  
**.smug** - Look smug  
**.surprised** - Look surprised  
**.sweat** - Sweat  
**.tired** - Look tired  
**.woah** - Say woah  
**.yay** - Say yay  
**.bleh** - Stick tongue out  
**.celebrate** - Celebrate  
**.cool** - Look cool  
**.drool** - Drool  
**.evillaugh** - Evil laugh  
**.nyah** - Say nyah  
**.shout** - Shout  
**.slowclap** - Slow clap  
**.sneeze** - Sneeze  
**.explode** - Explode  

**Usage:** `.dance`, `.cry`, `.laugh`, etc.

---

## ⚙️ Settings Commands

### Jail System

#### `.jail role <role>`
**Permission:** Owner  
**Description:** Set jail role for anti-nuke system  
**Usage:** `.jail role @JailRole`

#### `.jail channel <channel>`
**Permission:** Owner  
**Description:** Set jail channel  
**Usage:** `.jail channel #jail-channel`

---

## Permission Levels

**Owner:** Server owner or bot owner (set in .env)  
**Administrator:** Users with Administrator permission  
**Hardban Permission:** Granted by owner via `.hbpermsadd`  
**Fake Permissions:** Bot-based permissions for specific commands  
**VC Owner:** User who owns/claimed a voice channel  

---

## Examples

### Setup New Server
```
.setuplog messages
.setuplog voice
.setuplog roles
.setuplog antinuke
.jail role @JailRole
.antinuke threshold ban 5 1
.whitelist add @TrustedAdmins
.roleplay on
```

### Moderate User
```
.kick @User Spamming
.ban @User Serious violation
.hb @User Permanent ban
```

### Manage Permissions
```
.hbpermsadd @Moderator
.fakeperm add @Helper ban kick
.fakeperm check @Helper
```

### Voice Channel Management
```
.vc lock
.vc trust @Friend
.vc block @BadUser
.vc limit 5
```

### Roleplay
```
.hug @Friend
.dance
.wave @Everyone
```

---

## Tips

- Use `.ghelp` to see all admin commands in Discord
- Most commands log their actions to appropriate log channels
- Whitelist trusted users/roles to prevent false anti-nuke triggers
- Fake permissions are bot-based only, not Discord permissions
- VC commands only work when you're in the voice channel
- Roleplay must be enabled with `.roleplay on` before use
- All settings persist across bot restarts

---

## Need Help?

Check the documentation:
- [README.md](README.md) - Full feature overview
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [SETUP.md](SETUP.md) - Detailed setup instructions
- [FEATURES.md](FEATURES.md) - Complete feature checklist

# Anti-Nuke System - Enhanced Features

## Overview
The Anti-Nuke system has been comprehensively enhanced to detect and prevent various types of raid/nuke activities beyond just bans and kicks. It now monitors role manipulations, channel manipulations, webhook abuse, emoji spam, and sticker spam.

## New Detection Capabilities

### 1. Role Operations
- **Role Creation Detection**: Monitors mass role creation attempts
- **Role Deletion Detection**: Tracks bulk role deletion activities
- Default thresholds: 5 creates/hour, 3 deletes/hour

### 2. Channel Operations
- **Channel Creation Detection**: Detects mass channel spam
- **Channel Deletion Detection**: Tracks bulk channel deletion
- Default thresholds: 5 creates/hour, 3 deletes/hour

### 3. Webhook Operations
- **Webhook Creation Detection**: Identifies webhook spam (potential raid prep)
- **Webhook Deletion Detection**: Monitors webhook removal abuse
- Default thresholds: 5 creates/hour, 3 deletes/hour

### 4. Emoji Operations
- **Emoji Creation Detection**: Catches mass emoji uploads
- **Emoji Deletion Detection**: Tracks bulk emoji removal
- Default thresholds: 10 creates/hour, 5 deletes/hour

### 5. Sticker Operations
- **Sticker Creation Detection**: Identifies sticker spam
- **Sticker Deletion Detection**: Monitors bulk sticker removal
- Default thresholds: 10 creates/hour, 5 deletes/hour

## Configuration Commands

### Setting Thresholds
```
.antinuke threshold <action> <count> <hours>
```

**Available Actions:**
- `ban` - Member ban operations
- `kick` - Member kick operations
- `role_create` - Role creation
- `role_delete` - Role deletion
- `channel_create` - Channel creation
- `channel_delete` - Channel deletion
- `webhook_create` - Webhook creation
- `webhook_delete` - Webhook deletion
- `emoji_create` - Emoji creation
- `emoji_delete` - Emoji deletion
- `sticker_create` - Sticker creation
- `sticker_delete` - Sticker deletion

**Example:**
```
.antinuke threshold role_delete 3 1
```
This sets the threshold to 3 role deletions within 1 hour.

### Viewing Configuration
```
.antinuke view
```
Shows all configured thresholds and the default punishment action.

### Setting Punishment Action
```
.antinuke action <ban|kick|jail>
```
Sets the default punishment when thresholds are exceeded.

**Example:**
```
.antinuke action jail
```

### Whitelist Management
```
.antinuke whitelist add <@user/@role>
.antinuke whitelist remove <@user/@role>
.antinuke whitelist view
```

Users or roles on the whitelist are exempt from anti-nuke protection.

### Action History
```
.antinuke history
```
View the last 10 anti-nuke actions taken by the system.

## How It Works

### Detection Process
1. **Event Monitoring**: Discord events are monitored in real-time
2. **Audit Log Verification**: Each action is verified through Discord's audit log
3. **Bot Filtering**: Actions performed by bots are ignored
4. **Whitelist Check**: Whitelisted users/roles are exempt
5. **Threshold Tracking**: Actions are tracked within time windows
6. **Auto-Punishment**: When thresholds are exceeded, configured punishment is applied
7. **Detailed Logging**: All actions are logged to the antinuke log channel
8. **History Recording**: Action history is stored for review

### Punishment Options
- **Jail**: Removes all roles and adds the jail role (requires jail role setup)
- **Ban**: Permanently bans the offender from the server
- **Kick**: Kicks the offender from the server

### Logging
When an anti-nuke action is triggered, the following information is logged:
- 🚨 Alert title with action type
- Actor information (mention, name, ID)
- Action count vs threshold
- Time window
- Punishment applied
- Timestamp

## Default Thresholds

| Action | Count | Time Window |
|--------|-------|-------------|
| ban | 3 | 1 hour |
| kick | 5 | 1 hour |
| role_create | 5 | 1 hour |
| role_delete | 3 | 1 hour |
| channel_create | 5 | 1 hour |
| channel_delete | 3 | 1 hour |
| webhook_create | 5 | 1 hour |
| webhook_delete | 3 | 1 hour |
| emoji_create | 10 | 1 hour |
| emoji_delete | 5 | 1 hour |
| sticker_create | 10 | 1 hour |
| sticker_delete | 5 | 1 hour |

These defaults are used until custom thresholds are configured.

## Data Storage

All anti-nuke configuration is stored in `data/antinuke_data.json`:

```json
{
  "guild_id": {
    "whitelist": {
      "users": [],
      "roles": []
    },
    "thresholds": {
      "ban": {"count": 3, "hours": 1},
      "kick": {"count": 5, "hours": 1},
      ...
    },
    "default_action": "jail",
    "action_history": [
      {
        "timestamp": "2024-01-31T12:00:00",
        "action_type": "role_delete",
        "user_id": 123456789,
        "user_name": "BadActor#1234",
        "punishment": "Jailed",
        "reason": "Mass role deletion detected - 5 roles in 1 hour(s)",
        "details": {...}
      }
    ]
  }
}
```

## Setup Requirements

1. **Required Permissions**: The bot needs the following permissions:
   - View Audit Log
   - Manage Roles
   - Ban Members (if using ban punishment)
   - Kick Members (if using kick punishment)

2. **Log Channel**: Set up an antinuke log channel using:
   ```
   .log antinuke #channel
   ```

3. **Jail Role** (if using jail punishment): Set up a jail role using:
   ```
   .settings jailrole @role
   ```

## Best Practices

1. **Whitelist Admins**: Add trusted administrators to the whitelist
   ```
   .antinuke whitelist add @Admin
   ```

2. **Adjust Thresholds**: Customize thresholds based on your server's size and activity
   ```
   .antinuke threshold channel_delete 2 1
   ```

3. **Monitor History**: Regularly check action history to identify patterns
   ```
   .antinuke history
   ```

4. **Test Configuration**: Test with a trusted user to ensure settings are correct

5. **Set Appropriate Punishment**: Choose punishment that fits your server's moderation style
   - Use `jail` for temporary restriction with manual review
   - Use `kick` for immediate removal with ability to rejoin
   - Use `ban` for permanent removal (most severe)

## Technical Details

### Event Listeners
The system uses the following Discord.py event listeners:
- `on_member_ban`
- `on_member_remove` (for kicks)
- `on_guild_role_create`
- `on_guild_role_delete`
- `on_guild_channel_create`
- `on_guild_channel_delete`
- `on_webhooks_update` (for webhook operations)
- `on_guild_emojis_update` (for emoji operations)
- `on_guild_stickers_update` (for sticker operations)

### Thread Safety
All configuration operations use asyncio locks to ensure thread-safe access to data files.

### Action Tracking
Actions are tracked in-memory using a defaultdict structure with automatic cleanup of expired entries based on the configured time windows.

## Troubleshooting

### Anti-Nuke Not Working
- Verify the bot has "View Audit Log" permission
- Check that the log channel is properly configured
- Ensure the actor is not whitelisted
- Verify thresholds are set appropriately

### False Positives
- Add legitimate administrators to the whitelist
- Increase threshold counts
- Increase time windows for thresholds

### Jail Punishment Not Working
- Verify jail role is configured: `.settings jailrole @role`
- Check bot has "Manage Roles" permission
- Ensure bot's role is higher than the jail role

## Command Permissions

All anti-nuke commands require owner permissions (configured via `OWNER_ID` in `.env`).
